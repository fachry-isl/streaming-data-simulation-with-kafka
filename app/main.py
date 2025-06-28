import os
import time
import logging
import random
import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from kafka import KafkaProducer
import json
from contextlib import asynccontextmanager
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Global variable to store the producer
producer = None

def create_kafka_producer(max_retries=10, retry_delay=5):
    """
    Create Kafka producer with retry logic
    """
    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Kafka at {kafka_broker} (attempt {attempt + 1}/{max_retries})")
            
            producer = KafkaProducer(
                bootstrap_servers=[kafka_broker],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                # Add connection timeout settings
                request_timeout_ms=30000,
                retry_backoff_ms=1000,
                max_block_ms=60000
            )
            
            # Test the connection by getting metadata
            producer.bootstrap_connected()
            logger.info("Successfully connected to Kafka!")
            return producer
            
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not connect to Kafka.")
                raise e

def generate_iot_data():
    """Generate simulated IoT sensor data"""
    data = {
        "device_id": fake.uuid4(),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "temperature": round(random.uniform(20, 40), 2),
        "humidity": round(random.uniform(30, 80), 2)
    }
    return data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global producer
    try:
        # Wait for Kafka to be ready
        logger.info("Initializing Kafka producer...")
        time.sleep(5)
        producer = create_kafka_producer()
        logger.info("Kafka producer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
        producer = None
    
    yield
    
    # Shutdown
    if producer:
        producer.close()
        logger.info("Kafka producer closed")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="IoT Data Producer",
    description="A FastAPI application that produces IoT data to Kafka",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "IoT Data Producer is running!"}

@app.get("/health")
async def health_check():
    kafka_status = "connected" if producer else "disconnected"
    return {
        "status": "healthy",
        "kafka": kafka_status
    }

@app.post("/send-data")
async def send_iot_data(data: dict):
    """Send custom IoT data to Kafka"""
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    try:
        topic = "iot-data"
        producer.send(topic, data)
        producer.flush()
        
        logger.info(f"Data sent to topic '{topic}': {data}")
        return {"status": "success", "message": f"Data sent to {topic}", "data": data}
        
    except Exception as e:
        logger.error(f"Failed to send data to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send data: {str(e)}")

@app.post("/simulate")
async def send_simulation_data(count: int = Query(1, ge=1, le=1000, description="Number of simulation records to generate")):
    """Generate and send simulated IoT data to Kafka with streaming response"""
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    async def generate_stream():
        try:
            topic = "iot-data"
            
            for i in range(count):
                # Generate simulation data
                data = generate_iot_data()
                
                # Send to Kafka
                producer.send(topic, data)
                
                # Create response for this record
                response_data = {
                    "status": "success",
                    "record": i + 1,
                    "total": count,
                    "data": data
                }
                
                # Yield this record as JSON line
                yield json.dumps(response_data) + "\n"
                
                # Small delay between messages if sending multiple
                if count > 1:
                    time.sleep(1)
            
            producer.flush()  # Ensure all messages are sent
            logger.info(f"Sent {count} simulation records to topic '{topic}'")
            
            # Send final completion message
            final_response = {
                "status": "completed",
                "message": f"Sent {count} simulation records to {topic}",
                "total_count": count
            }
            yield json.dumps(final_response) + "\n"
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Failed to send simulation data: {str(e)}"
            }
            yield json.dumps(error_response) + "\n"
            logger.error(f"Failed to send simulation data to Kafka: {e}")
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson",  # Newline Delimited JSON
        headers={"Content-Disposition": "inline"}
    )

@app.get("/simulate")
async def send_single_simulation():
    """Generate and send a single simulated IoT data record to Kafka (GET endpoint for easy testing)"""
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    try:
        topic = "iot-data"
        
        # Generate simulation data
        data = generate_iot_data()
        
        # Send to Kafka
        producer.send(topic, data)
        producer.flush()
        
        logger.info(f"Sent simulation data to topic '{topic}': {data}")
        return {
            "status": "success", 
            "message": f"Simulation data sent to {topic}",
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Failed to send simulation data to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send simulation data: {str(e)}")

@app.post("/simulate/batch")
async def send_batch_simulation(
    count: int = Query(10, ge=1, le=1000, description="Number of records to generate"),
    topic: str = Query("iot-data", description="Kafka topic to send data to"),
    delay_ms: int = Query(100, ge=0, le=5000, description="Delay between messages in milliseconds")
):
    """Generate and send a batch of simulated IoT data with configurable parameters"""
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    try:
        sent_data = []
        start_time = time.time()
        
        for i in range(count):
            # Generate simulation data with batch identifier
            data = generate_iot_data()
            data["batch_id"] = fake.uuid4()
            data["sequence"] = i + 1
            
            # Send to Kafka
            producer.send(topic, data)
            sent_data.append(data)
            
            # Delay between messages if specified
            if delay_ms > 0 and i < count - 1:
                time.sleep(delay_ms / 1000.0)
        
        producer.flush()
        end_time = time.time()
        
        logger.info(f"Sent {count} simulation records to topic '{topic}' in {end_time - start_time:.2f} seconds")
        return {
            "status": "success",
            "message": f"Sent {count} simulation records to {topic}",
            "count": count,
            "topic": topic,
            "duration_seconds": round(end_time - start_time, 2),
            "sample_data": sent_data[:3] if len(sent_data) > 3 else sent_data  # Show first 3 records as sample
        }
        
    except Exception as e:
        logger.error(f"Failed to send batch simulation data to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send batch simulation data: {str(e)}")

@app.get("/test-kafka")
async def test_kafka_connection():
    """Test Kafka connection with a simple message"""
    if not producer:
        return {"status": "error", "message": "Kafka producer not initialized"}
    
    try:
        test_data = {"test": True, "timestamp": datetime.datetime.utcnow().isoformat()}
        producer.send("test-topic", test_data)
        producer.flush()
        
        return {"status": "success", "message": "Test message sent successfully", "data": test_data}
    except Exception as e:
        return {"status": "error", "message": f"Kafka connection test failed: {str(e)}"}