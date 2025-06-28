# IoT Streaming Data Simulator

This project provides a **FastAPI** application for simulating and streaming IoT sensor data to a **Kafka** cluster. It is designed for easy local development using **Docker Compose**, and includes endpoints for health checks, single/batch simulation, and Kafka connectivity testing.

## Features

- **Simulate IoT Data:** Generate random sensor data (temperature, humidity, device ID, timestamp) using [Faker](https://faker.readthedocs.io/).
- **Stream to Kafka:** Send data to Kafka topics in real-time or batch mode.
- **REST API:** FastAPI endpoints for sending, simulating, and testing data.
- **Dockerized:** All services (Kafka, Zookeeper, Kafka UI, FastAPI app) run with one command.
- **Kafka UI:** Web interface for inspecting Kafka topics and messages.

## Project Structure

```
.
├── app/
│   ├── main.py               # FastAPI application (core logic)
│   └── test_connection.py    # Kafka connection and diagnostics
├── Dockerfile                # Container build for FastAPI app
├── docker-compose.yml        # Multi-service orchestration
├── requirements.txt          # Python dependencies
```

## Quick Start

### 1. Prerequisites

- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- (Optional) Python 3.11+ for local development

### 2. Clone the Repository

```sh
git clone https://github.com/fachry-isl/streaming-data-simulation-with-kafka.git
cd streaming-data-simulation-with-kafka
```

### 3. Start All Services

```sh
docker-compose up --build
```

This will start:

- **Zookeeper** (port 2181)
- **Kafka** (port 9092)
- **Kafka UI** (port 8080)
- **FastAPI IoT Producer** (port 8000)

### 4. Access the Services

- **FastAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Kafka UI:** [http://localhost:8080](http://localhost:8080)

## API Endpoints

| Method | Endpoint          | Description                               |
| ------ | ----------------- | ----------------------------------------- |
| GET    | `/`               | Welcome message                           |
| GET    | `/health`         | Health check (Kafka connection status)    |
| POST   | `/send-data`      | Send custom IoT data to Kafka             |
| POST   | `/simulate`       | Stream N simulated records to Kafka       |
| GET    | `/simulate`       | Send a single simulated record to Kafka   |
| POST   | `/simulate/batch` | Batch send simulated data (configurable)  |
| GET    | `/test-kafka`     | Test Kafka connection with a test message |

#### **Diagnostic Endpoints** (from [`app/test_connection.py`](app/test_connection.py)):

| Method | Endpoint             | Description                             |
| ------ | -------------------- | --------------------------------------- |
| GET    | `/test-connection`   | Test Kafka connection (partitions info) |
| GET    | `/send-tiny-message` | Send a minimal message to Kafka         |
| GET    | `/iot-data`          | Send a random IoT message to Kafka      |

---

## Configuration

- **Kafka Broker:** Set via environment variable [`KAFKA_BROKER`](app/test_connection.py) (default: `localhost:9092`).
  - In Docker Compose, set to [`kafka:9092`](venv/Lib/site-packages/kafka/__init__.py) for internal networking.
- **Kafka Topics:** Default topics are `iot-data` and `test-topic`.

## Development

### Run Locally (without Docker)

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Start Kafka & Zookeeper (locally or via Docker).
3. Run FastAPI app:
   ```sh
   uvicorn app.main:app --reload
   ```

### Run Tests

You can use the endpoints in [`app/test_connection.py`](app/test_connection.py) for manual Kafka diagnostics:

```sh
python app/test_connection.py
```

---

## Useful Links

- **Kafka UI:** [http://localhost:8080](http://localhost:8080)
- **FastAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Kafka Python:** [https://kafka-python.readthedocs.io/](https://kafka-python.readthedocs.io/)
- **Faker:** [https://faker.readthedocs.io/](https://faker.readthedocs.io/)

## Troubleshooting

- If the FastAPI app cannot connect to Kafka, ensure Kafka is fully started.
- Use the `/test-connection` and `/send-tiny-message` endpoints for debugging.
- Check logs in Docker Compose output for errors.
