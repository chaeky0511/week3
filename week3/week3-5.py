from flask import Flask, render_template_string, url_for, redirect, jsonify
import RPi.GPIO as GPIO
import threading
import time
import Adafruit_DHT  # DHT 라이브러리 추가

app = Flask(__name__)

# GPIO 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# LED 핀 설정
ledPin = [22, 23, 24]  # 에어컨, 히터, 제습기 LED 핀
ledStates = [0, 0, 0]  # LED 초기 상태 (OFF)

GPIO.setup(ledPin[0], GPIO.OUT)
GPIO.setup(ledPin[1], GPIO.OUT)
GPIO.setup(ledPin[2], GPIO.OUT)

# 터치 센서 핀 설정
TOUCH_PIN = 27
touchState = 0
mode = "AUTO"  # 기본은 AUTO 모드
GPIO.setup(TOUCH_PIN, GPIO.IN)

# 초음파 센서 핀 설정
TRIG_PIN = 17
ECHO_PIN = 18
distance = 0
alert_threshold = 10  # 10cm 미만이면 알림
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# DHT 센서 핀 설정
DHT_SENSOR = Adafruit_DHT.DHT11  # 사용할 DHT 센서 종류
DHT_PIN = 4  # GPIO 4번 핀

# GPIO 잠금 객체
gpio_lock = threading.Lock()

# LED 상태 업데이트
def updateLeds():
    for num, value in enumerate(ledStates):
        GPIO.output(ledPin[num], value)

# AUTO 모드에서 온습도에 따른 LED 제어
def auto_mode():
    global ledStates
    while True:
        if mode == "AUTO":
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if temperature is not None and humidity is not None:
                # LED 상태 업데이트
                if temperature >= 29:
                    if humidity >= 40:
                        ledStates = [1, 0, 1]  # 에어컨 ON, 제습기 ON
                    else:
                        ledStates = [1, 0, 0]  # 에어컨 ON, 히터, 제습기 OFF
                elif temperature <= 28:
                    if humidity >= 40:
                        ledStates = [0, 1, 1]  # 히터 ON, 제습기 ON
                    else:
                        ledStates = [0, 1, 0]  # 히터 ON, 에어컨, 제습기 OFF
                else:
                    ledStates = [0, 0, 0]  # 모든 장치 OFF
            else:
                print("센서 읽기 오류")
            updateLeds()  # LED 상태 업데이트
            time.sleep(1)

# 터치 센서 상태 체크 (한 번 터치로 AUTO/MANU 변경)
def monitor_touch():
    global mode
    touch_previous_state = GPIO.LOW  # 이전 터치 상태를 저장 (LOW = 터치되지 않음)

    while True:
        touch_current_state = GPIO.input(TOUCH_PIN)  # 현재 터치 상태를 읽음

        if touch_previous_state == GPIO.LOW and touch_current_state == GPIO.HIGH:
            # 이전에 터치되지 않았고, 현재 터치되었다면 모드 변경
            mode = "AUTO" if mode == "MANU" else "MANU"
            print(f"모드가 {mode}로 변경되었습니다.")

        # 현재 상태를 이전 상태로 저장
        touch_previous_state = touch_current_state

        time.sleep(0.2)  # 짧은 간격으로 터치 상태를 체크 (200ms)

# 초음파 거리 측정
def measure_distance():
    global distance
    while True:
        GPIO.output(TRIG_PIN, True)
        time.sleep(0.00001)  # 10us 펄스 전송
        GPIO.output(TRIG_PIN, False)

        start_time = time.time()
        stop_time = time.time()

        while GPIO.input(ECHO_PIN) == 0:
            start_time = time.time()

        while GPIO.input(ECHO_PIN) == 1:
            stop_time = time.time()

        # 거리 계산
        elapsed_time = stop_time - start_time
        distance = (elapsed_time * 34300) / 2
        time.sleep(1)  # 1초 간격으로 거리 측정


# HTML 페이지 템플릿
html_page = '''<!doctype html>
<html lang="ko">
<!doctype html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Embedded System Controller</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='web_design.css') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100..900&display=swap">
</head>
<body>
    <div class="wrap">
        <div class="intro_bg">
            <div class="bar"></div>
        
            <ul class="nav">
                <li><a href="#">Embedded System Controller</a></li>

                <ul class="mode">
                    <div class="body">
                        <div class="tabs">
                            <input type="radio" id="auto" name="mode" value="AUTO" class="input" {% if mode == 'AUTO' %}checked{% endif %} onclick="changeMode('AUTO')" />
                            <label for="auto" class="label">AUTO</label>
                            
                            <input type="radio" id="manu" name="mode" value="MANU" class="input" {% if mode == 'MANU' %}checked{% endif %} onclick="changeMode('MANU')" />
                            <label for="manu" class="label">MANU</label>
                        </div>
                    </div>
                </ul>
            </ul>   
        </div>

        <div class="temperature-humidity">
            <div class="temperature-humidity-inner">
                <div class="temperature">
                    <img src="{{ url_for('static', filename='thermometer.png') }}" alt="온도계" class="icon1">
                    현재 온도: <span id="temperature">{{ current_temperature }}°C</span>
                </div>

                <div class="humidity">
                    <img src="{{ url_for('static', filename='hydrometer.png') }}" alt="습도계" class="icon1">
                    현재 습도: <span id="humidity">{{ current_humidity }}%</span>
                </div>
            </div>

            <div class="distance">
                <h1>주변 침입자 거리</h1>
                <p>현재 거리: <span id="distance">{{ distance | round(2) }}</span> cm</p>
                <p id="alert" style="color:red;"></p>
            </div>
        </div>

        <ul class="icon2">
                    <li> 
                        <div class="text">에어컨</div>
                        <div class="icon_img">
                          <img src="{{ url_for('static', filename='aircon.png') }}" class="aircon-img">
                        </div> 
                        <label class="switch">
                             <input type="checkbox" class="toggle" {% if ledStates[0] == 1 %}checked{% endif %} id="airconToggle" onclick="toggleLED(0)">
                           <span class="slider"></span>
                        </label>
                    </li>
                    <li> 
                        <div class="text">히터</div>
                        <div class="icon_img">
                         <img src="{{ url_for('static', filename='heater.png') }}" class="heater-img">
                        </div>
                        <label class="switch">
                            <input type="checkbox" class="toggle" {% if ledStates[1] == 1 %}checked{% endif %} id="heaterToggle" onclick="toggleLED(1)">
                            <span class="slider"></span>
                        </label>
                    </li>
                    <li>
                        <div class="text">제습기</div>
                        <div class="icon_img">
                        <img src="{{ url_for('static', filename='dehumidifier.png') }}" class="dehumid-img">
                        </div>
                        <label class="switch">
                            <input type="checkbox" class="toggle" {% if ledStates[2] == 1 %}checked {% endif %} id="dehumidifierToggle" onclick="toggleLED(2)">
                            <span class="slider"></span>
                        </label>
                    </li>
            </ul>

    </div>

    <script>
    function toggleLED(ledNumber) {
        // LED 토글 요청
        fetch(`/toggleLED/${ledNumber}`, { method: 'POST' });
    }

    // 모드 변경 함수
    function changeMode(newMode) {
        fetch(`/change_mode/${newMode}`, { method: 'POST' });
    }

    // 실시간 모드 업데이트 함수
    function updateMode() {
        fetch('/get_mode')
            .then(response => response.json())
            .then(data => {
                const mode = data.mode;
                if (mode === 'AUTO') {
                    document.getElementById('auto').checked = true;
                } else {
                    document.getElementById('manu').checked = true;
                }
            });
    }

    
    // 주기적으로 온도와 습도를 업데이트
    setInterval(() => {
        fetch('/get_DHT')
            .then(response => response.json())
            .then(data => {
                document.getElementById("temperature").innerText = data.temperature + "°C";
                document.getElementById("humidity").innerText = data.humidity + "%";
            });
    }, 5000); // 5초마다 업데이트
        

    // 실시간 거리 업데이트 함수
    function updateDistance() {
        fetch('/get_distance')
            .then(response => response.json())
            .then(data => {
                document.getElementById('distance').innerText = data.distance.toFixed(2);
                if (data.distance < {{ alert_threshold }}) {
                    document.getElementById('alert').innerText = "경고! 10cm 이내 접근!";
                } else {
                    document.getElementById('alert').innerText = "";
                }
            });
    }
    

    // LED 상태 업데이트 함수
    function updateLEDStates() {
        fetch('/get_led_states')
            .then(response => response.json())
            .then(data => {
                const ledStates = data.ledStates;
                document.getElementById('airconToggle').checked = ledStates[0] === 1;
                document.getElementById('heaterToggle').checked = ledStates[1] === 1;
                document.getElementById('dehumidifierToggle').checked = ledStates[2] === 1;
            });
    }

    // 1초마다 거리, 모드, LED 상태 값 갱신
    setInterval(updateDistance, 1000);
    setInterval(updateMode, 1000);
    setInterval(updateLEDStates, 1000);  // LED 상태도 1초마다 갱신
</script>
</body>
</html>

'''

# Flask 라우팅
@app.route('/')
def index():
    current_temperature, current_humidity = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return render_template_string(html_page, current_temperature=current_temperature or 0, current_humidity=current_humidity or 0, distance=distance, mode=mode, alert_threshold=alert_threshold, ledStates=ledStates)

@app.route('/toggleLED/<int:ledNumber>', methods=['POST'])
def toggleLED(ledNumber):
    global ledStates
    if mode == "MANU":
        ledStates[ledNumber] = 1 - ledStates[ledNumber]  # Toggle the state
        updateLeds()  # Update the LEDs to reflect the new states
    return ('', 204)



@app.route('/get_led_states', methods=['GET'])
def get_led_states():
    # LED 상태를 JSON 형태로 반환
    return jsonify({'ledStates': ledStates})

@app.route('/get_mode')
def get_mode():
    return jsonify(mode=mode)

@app.route('/get_DHT')
def get_dht():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return jsonify(temperature=temperature or 0, humidity=humidity or 0)
 

@app.route('/get_distance')
def get_distance():
    return jsonify(distance=distance)

@app.route('/change_mode/<string:new_mode>', methods=['POST'])
def change_mode(new_mode):
    global mode
    if new_mode in ["AUTO", "MANU"]:
        mode = new_mode
    return ('', 204)  # 성공 시 응답 코드 204 반환 (내용 없음)


if __name__ == '__main__':
    try:
        # 스레드 시작
        threading.Thread(target=monitor_touch, daemon=True).start()
        threading.Thread(target=measure_distance, daemon=True).start()
        threading.Thread(target=auto_mode, daemon=True).start()
        
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        GPIO.cleanup()  # Ctrl+C로 종료 시 GPIO 핀 정리
    finally:
        GPIO.cleanup()  # 모든 종료 후 GPIO 핀 정리

