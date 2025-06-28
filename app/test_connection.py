from fastapi import FastAPI
from faker import Faker
from kafka import KafkaProducer
import random
import json
import datetime
import time

app = FastAPI()
faker = Faker()

# Kafka config - exactly like your original
KAFKA_TOPIC = "iot-stream"
KAFKA_BROKER = "localhost:9092"

# Let's add some simple logging to see what's happening
def log_step(step_name, details=""):
    """Simple function to help us see what's happening at each step"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {step_name}: {details}")

# Create the producer with some diagnostic info
log_step("Starting", "Creating Kafka producer...")

try:
    # Your original producer setup, but let's see if this step works
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    log_step("Success", "Producer created successfully")
except Exception as e:
    log_step("Error", f"Failed to create producer: {e}")
    producer = None

@app.get("/iot-data")
def get_iot_data():
    """Your original function with diagnostic steps added"""
    
    # Check if we even have a producer
    if producer is None:
        log_step("Error", "No producer available")
        return {"status": "error", "message": "Producer not available"}
    
    # Create your data - exactly like before
    data = {
        "device_id": faker.uuid4(),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "temperature": round(random.uniform(20, 40), 2),
        "humidity": round(random.uniform(30, 80), 2)
    }
    
    # Let's see how big our message actually is
    json_string = json.dumps(data)
    message_size = len(json_string.encode("utf-8"))
    log_step("Message created", f"Size: {message_size} bytes, Content: {json_string}")
    
    try:
        # Step 1: Try to send the message
        log_step("Sending", "Attempting to send message to Kafka...")
        
        # Your original send operation
        future = producer.send(KAFKA_TOPIC, value=data)
        log_step("Send called", "producer.send() completed, waiting for confirmation...")
        
        # Step 2: Try to flush - this is often where things go wrong
        log_step("Flushing", "Calling producer.flush()...")
        producer.flush()
        log_step("Flush complete", "producer.flush() completed successfully")
        
        # Step 3: Try to get the result
        log_step("Getting result", "Waiting for send confirmation...")
        record_metadata = future.get(timeout=10)  # Wait max 10 seconds
        log_step("Success", f"Message sent to partition {record_metadata.partition}, offset {record_metadata.offset}")
        
        return {
            "status": "sent to kafka", 
            "data": data,
            "message_size": message_size,
            "kafka_info": {
                "partition": record_metadata.partition,
                "offset": record_metadata.offset
            }
        }
        
    except Exception as e:
        log_step("Error", f"Failed during Kafka operation: {e}")
        return {"status": "error", "message": str(e), "data": data}

@app.get("/test-connection")
def test_connection():
    """Simple test to see if we can connect to Kafka at all"""
    log_step("Connection test", "Testing basic Kafka connection...")
    
    if producer is None:
        log_step("Connection test", "Producer is None - connection failed at startup")
        return {"status": "failed", "reason": "No producer"}
    
    try:
        # Try to get some basic info about Kafka
        # This is a simple way to test if Kafka is responding
        partitions = producer.partitions_for(KAFKA_TOPIC)
        log_step("Connection test", f"Successfully connected. Topic '{KAFKA_TOPIC}' has partitions: {partitions}")
        return {"status": "connected", "topic": KAFKA_TOPIC, "partitions": partitions}
    except Exception as e:
        log_step("Connection test", f"Connection failed: {e}")
        return {"status": "failed", "error": str(e)}

@app.get("/send-tiny-message")
def send_tiny_message():
    """Test with the smallest possible message to isolate the size issue"""
    log_step("Tiny message test", "Sending minimal test message...")
    
    if producer is None:
        return {"status": "error", "message": "No producer"}
    
    # Create the tiniest possible message
    tiny_data = {"test": 1}
    json_string = json.dumps(tiny_data)
    message_size = len(json_string.encode("utf-8"))
    
    log_step("Tiny message", f"Size: {message_size} bytes, Content: {json_string}")
    
    try:
        log_step("Sending tiny", "Attempting to send...")
        future = producer.send(KAFKA_TOPIC, value=tiny_data)
        
        log_step("Flushing tiny", "Flushing...")
        producer.flush()
        
        log_step("Getting result tiny", "Getting confirmation...")
        record_metadata = future.get(timeout=5)
        
        log_step("Tiny success", f"Sent successfully to partition {record_metadata.partition}")
        return {"status": "success", "size": message_size}
        
    except Exception as e:
        log_step("Tiny failed", f"Even tiny message failed: {e}")
        return {"status": "failed", "error": str(e)}

# Add this to run the script directly for testing
if __name__ == "__main__":
    print("=== Testing Kafka Connection ===")
    print("Before starting FastAPI, let's test the producer directly...")
    
    # Test 1: Can we create a producer?
    if producer is not None:
        print("✓ Producer created successfully")
        
        # Test 2: Can we send a simple message?
        test_data = {"direct_test": True, "timestamp": time.time()}
        try:
            log_step("Direct test", "Sending test message directly...")
            future = producer.send(KAFKA_TOPIC, value=test_data)
            producer.flush()
            result = future.get(timeout=10)
            print(f"✓ Direct send successful! Partition: {result.partition}, Offset: {result.offset}")
        except Exception as e:
            print(f"✗ Direct send failed: {e}")
    else:
        print("✗ Failed to create producer")
    
    print("\nNow you can run: uvicorn main:app --reload")
    print("Then test these endpoints:")
    print("  http://localhost:8000/test-connection")
    print("  http://localhost:8000/send-tiny-message") 
    print("  http://localhost:8000/iot-data")