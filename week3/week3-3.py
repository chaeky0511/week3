from flask import Flask, render_template_string
import RPi.GPIO as GPIO
import time
import threading

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Define pins for the ultrasonic sensor
TRIG_PIN = 17  # Trigger pin
ECHO_PIN = 18  # Echo pin
distance = 0  # Initialize distance variable
alert_threshold = 10  # Alert threshold distance (cm)

# Setup the ultrasonic sensor pins
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Function to measure distance using the ultrasonic sensor
def measure_distance():
    global distance
    while True:
        try:
            # Generate a trigger signal
            GPIO.output(TRIG_PIN, True)
            time.sleep(0.00001)  # Send a 10 microsecond pulse
            GPIO.output(TRIG_PIN, False)

            # Measure the time for the echo signal to return
            start_time = time.time()
            while GPIO.input(ECHO_PIN) == 0:
                start_time = time.time()

            while GPIO.input(ECHO_PIN) == 1:
                end_time = time.time()

            # Speed of sound: 34300 cm/s
            elapsed_time = end_time - start_time
            distance = (elapsed_time * 34300) / 2  # Convert to cm

            print(f"Distance measured: {distance} cm")  # Log the measured distance

            time.sleep(1)  # Measure distance every second
        except Exception as e:
            print(f"Error measuring distance: {e}")

# HTML page template
html_page = '''<!doctype html>
    <html>
        <head>
            <title>Distance Sensor Controller</title>
            <script>
                function updateStatus() {
                    fetch('/')
                    .then(response => response.text())
                    .then(html => {
                        document.open();
                        document.write(html);
                        document.close();
                    });
                }
                setInterval(updateStatus, 2000);  // Refresh the status every 2 seconds
            </script>
        </head>
     <body>
         <h1>Embedded System Distance Monitor</h1>
         <hr>
         <div style="padding-left:20px;">
            <h3>Distance Measurement</h3>
            <p><b>Distance: {{ distance | round(2) }} cm</b></p>
            {% if distance < alert_threshold %}
                <p style="color: red;"><b>Alert! Object is too close!</b></p>
            {% endif %}
         </div>
       </body>
    </html>
'''

# Initialize the Flask app
app = Flask(__name__)

# Define the route for the homepage, which will display the distance measurement
@app.route('/')
def index():
    # Render the HTML page with the current distance and alert threshold
    return render_template_string(html_page, distance=distance, alert_threshold=alert_threshold)

# Start the distance measurement thread
distance_thread = threading.Thread(target=measure_distance)
distance_thread.daemon = True
distance_thread.start()

# Run the Flask app on port 5000 and make it accessible from any IP address (0.0.0.0)
if __name__ == "__main__":
    try:
        app.run(port=5000, host='0.0.0.0', debug=True)  # Enable debug mode
    finally:
        GPIO.cleanup()  # Clean up GPIO settings when the program exits