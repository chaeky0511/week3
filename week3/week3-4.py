from flask import Flask, Response
import Adafruit_DHT
import time
import threading

app = Flask(__name__)

# Sensor configuration
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  # GPIO pin number where the sensor is connected

# Global variable to store temperature and humidity data
sensor_data = {'temperature': None, 'humidity': None}

def read_sensor_data():
    """Function to periodically read temperature and humidity data from the sensor"""
    global sensor_data
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            sensor_data['temperature'] = round(temperature, 1)
            sensor_data['humidity'] = round(humidity, 1)
        time.sleep(1)

@app.route('/')
def index():
    """Serve an auto-refreshing HTML page to display temperature and humidity"""
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Temperature & Humidity Monitor</title>
        <meta http-equiv="refresh" content="1">
    </head>
    <body>
        <h1>Temperature & Humidity Monitor</h1>
        <p>Temperature: {sensor_data['temperature']} °C</p>
        <p>Humidity: {sensor_data['humidity']} %</p>
    </body>
    </html>
    """
    return Response(content, mimetype='text/html')

if __name__ == '__main__':
    # Start the thread to read sensor data
    sensor_thread = threading.Thread(target=read_sensor_data)
    sensor_thread.daemon = True
    sensor_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)