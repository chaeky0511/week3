from flask import Flask, render_template_string
import RPi.GPIO as GPIO
import time
import threading

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Define pin for the touch sensor
TOUCH_PIN = 27  # Pin number for the touch sensor
touchState = 0  # Touch sensor state (0: not touched, 1: touched)

# Set the touch sensor pin as input
GPIO.setup(TOUCH_PIN, GPIO.IN)

# Function to periodically monitor the touch sensor state
def monitor_touch():
    global touchState
    while True:
        if GPIO.input(TOUCH_PIN) == GPIO.HIGH:  # Touch detected
            touchState = 1
        else:  # No touch detected
            touchState = 0
        time.sleep(0.1)  # Check every 100 ms

# HTML page template
html_page = '''<!doctype html>
    <html>
        <head>
            <title>Touch Sensor Controller</title>
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
         <h1>Embedded System Controller</h1>
         <hr>
         <div style="padding-left:20px;">
            <h3>Touch Sensor</h3>
            <p><b>Touch Sensor Status: {% if touchState == 1 %} Touched {% else %} Not Touched {% endif %}</b></p>    
         </div>
       </body>
    </html>
'''

# Initialize the Flask app
app = Flask(__name__)

# Define the route for the homepage, which will display the touch sensor status
@app.route('/')
def index():
    # Render the HTML page with the current touch sensor state passed to it
    return render_template_string(html_page, touchState=touchState)

# Start the thread to monitor the touch sensor
touch_thread = threading.Thread(target=monitor_touch)
touch_thread.daemon = True
touch_thread.start()

# Run the Flask app on port 5000 and make it accessible from any IP address (0.0.0.0)
if __name__ == "__main__":
    try:
        app.run(port=5000, host='0.0.0.0')  # Run on port 5000
    finally:
        GPIO.cleanup()  # Clean up GPIO settings when the program exits