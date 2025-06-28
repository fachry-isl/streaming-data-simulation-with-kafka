import time
import requests

while True:
    data = requests.get("http://127.0.0.1:8000/iot-data").json()
    print(data)
    time.sleep(1)