from flask import Flask, render_template_string, url_for, redirect
import RPi.GPIO as GPIO

# Set the GPIO mode to BCM (Broadcom SOC channel numbering)
GPIO.setmode(GPIO.BCM)

# Define GPIO pin numbers for the LEDs
ledPin = [22, 23,  24]

# Initialize the states of the LEDs (0 for OFF, 1 for ON)
ledStates = [0, 0, 0]                       

# Setup the GPIO pins as output pins
GPIO.setup(ledPin[0], GPIO.OUT)
GPIO.setup(ledPin[1], GPIO.OUT)
GPIO.setup(ledPin[2], GPIO.OUT) 

# Function to update the LED states by writing the values to the GPIO pins
def updateLeds():
    for num, value in enumerate(ledStates):
        GPIO.output(ledPin[num], value)

# HTML template for the web page that controls the LEDs
html_page = '''<!doctype html>
    <html>
        <head>
            <title>LED Controller</title>
        </head>
     <body>
         <h1>Embedded System LED Controller</h1>
         <hr>
    
         <div style="padding-left:20px;">
                <h3>LED1, LED2, LED3</h3>
             <p>
                 <b>LED1: {% if ledStates[0]==1 %} ON {% else %} OFF {% endif %}</b>
                 <a href="{{ url_for('LEDControl', LEDN=0, state=1) }}"><input type="button" value="ON"></a>
                 <a href="{{ url_for('LEDControl', LEDN=0, state=0) }}"><input type="button" value="OFF"></a>
             </p>
             <p>
                 <b>LED2: {% if ledStates[1]==1 %} ON {% else %} OFF {% endif %}</b>
                 <a href="{{ url_for('LEDControl', LEDN=1, state=1) }}"><input type="button" value="ON"></a>
                 <a href="{{ url_for('LEDControl', LEDN=1, state=0) }}"><input type="button" value="OFF"></a>
                 
             </p>
             <p>
                <b>LED3: {% if ledStates[2]==1 %} ON {% else %} OFF {% endif %}</b>
                 <a href="{{ url_for('LEDControl', LEDN=2, state=1) }}"><input type="button" value="ON"></a>
                 <a href="{{ url_for('LEDControl', LEDN=2, state=0) }}"><input type="button" value="OFF"></a>
                
            </p>
         </div>
       </body>
    </html>
'''

# Initialize the Flask app
app = Flask(__name__)

# Define the route for the homepage, which will display the LED control interface
@app.route('/')
def index():
    # Render the HTML page with the current LED states passed to it
    return render_template_string(html_page, ledStates=ledStates)

# Define the route for controlling individual LEDs (LEDN is the LED number, state is the desired state)
@app.route('/<int:LEDN>/<int:state>')
def LEDControl(LEDN, state):
    # Update the state of the selected LED
    ledStates[LEDN] = state
    # Apply the changes to the hardware by calling updateLeds()
    updateLeds()
    # Redirect back to the homepage after changing the LED state
    return redirect(url_for('index'))

# Run the Flask web server when the script is executed directly
if __name__ == "__main__":
    app.run()