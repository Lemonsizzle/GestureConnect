import math
import os
import re
import signal
import threading
import time
import json
import cv2
import mediapipe as mp
import numpy as np
import GCML
from RPS import RPS
import GCDatabase
from GCScriptRunner import ScriptRunner
from flask import Flask, render_template, Response, request, jsonify, abort
from google.protobuf.json_format import MessageToDict
from collections import deque

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh

app = Flask(__name__)

db = GCDatabase.database("data.db")

config_name = "config.json"
config_data = {}

if os.path.exists(config_name):
    with open(config_name, 'r+') as config_file:
        config_content = config_file.read()
        config_data = json.loads(config_content)

if 'src' in config_data['app']:
    cap = cv2.VideoCapture(config_data['app']['src'])

if not cap.isOpened():
    cap = cv2.VideoCapture(0)

if 'scripts' in config_data['app']:
    scripts_dir = config_data['app']['scripts']
else:
    scripts_dir = "scripts"
    config_data['app']['scripts'] = scripts_dir

if not os.path.exists(scripts_dir):
    os.mkdir(scripts_dir)

ml_manager = GCML.MLManager()
script_runner = ScriptRunner(scripts_dir)

RPS_game = RPS()

hands = mp_hands.Hands(model_complexity=0,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.6)

resultHand = None

fps = False
h_flip = False
v_flip = False

mode = "off"

cap_lock = threading.Lock()

history_lock = threading.Lock()
right_history = deque(maxlen=10)
left_history = deque(maxlen=10)


@app.route('/build', methods=['POST'])
def build():
    ml_manager.build()


@app.route('/change_source', methods=['POST'])
def change_source(src=None):
    global cap, cap_lock
    if src is None:
        src = request.form.get('src')

    for char in src:
        if char not in "0123456789":
            break
    else:
        src = int(src)

    ip_port = r"^\d+\.\d+\.\d+\.\d+:\d+$"

    if type(src) is not int:
        if re.match(ip_port, src):
            parts = src.split(":")
            src = f"http://{parts[0]}:{parts[1]}"

    # Critical section of code that only one thread can access at a time
    print("Thread entering critical section (Changing source)")
    with cap_lock:
        if cap.isOpened():
            cap.release()
        cap = cv2.VideoCapture(src)

    config_data['app']['src'] = src

    return jsonify(success=True, message=f"Camera source changed to {src}")


@app.route('/interact', methods=['POST'])
def interact():
    global fps, h_flip, v_flip

    fps = True if request.form.get('fps') == 'on' else False

    h_flip = True if request.form.get('hflip') == 'on' else False

    v_flip = True if request.form.get('vflip') == 'on' else False

    return jsonify({"message": f"You selected"})


def get_finger_positions(distances, thumb_ref_tip, thumb_ref_middle):
    # Initialize a list with False for each finger
    fingers = [False] * 5

    # Check each finger
    for i in range(5):
        # if the distance to fingertip is less than distance to second knuckle of finger
        if i:
            if distances[4 * i + 2] < distances[4 * i + 4]:
                fingers[i] = True
        else:
            if thumb_ref_middle < thumb_ref_tip:
                fingers[i] = True

    return fingers


def distance(point, origin):
    """
    Calculates the Euclidean distance between two points.

    Parameters
    ----------
    point : tuple
        The coordinates of the first point.
    origin : tuple
        The coordinates of the second point.

    Returns
    -------
    float
        The Euclidean distance between the two points.
    """
    if len(point) == 2:
        x1, y1 = point
        x2, y2 = origin
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    if len(point) == 1:
        x1 = point[0]
        x2 = origin[0]
        return math.sqrt((x2 - x1) ** 2)


@app.route('/db/<string:functionName>', methods=['POST'])
def dbInteractions(functionName):
    functionDict = {
        "undo": undo,
        "remove": remove,
        "record": record,
    }
    return functionDict.get(functionName)()


def undo():
    db.undo()

    return jsonify(success=True)


def remove():
    shape = request.form.get('shape')
    db.removeClass(shape)

    return jsonify(success=True)


def record():
    global resultHand, db

    shape = request.form.get('shape')

    if resultHand:
        if resultHand.multi_hand_landmarks:
            data = [shape]

            hand_landmarks = resultHand.multi_hand_landmarks[0]

            landmark_points = []
            for i in range(21):  # 21 landmarks in MediaPipe hand model
                x = round(hand_landmarks.landmark[i].x, 2)
                y = round(hand_landmarks.landmark[i].y, 2)
                landmark_points.append((x, y))

            xs = [x for x, _ in landmark_points]
            ys = [y for _, y in landmark_points]
            wrist = (xs[0], ys[0])

            minx, maxx = np.min(xs), np.max(xs)
            miny, maxy = np.min(ys), np.max(ys)

            point1 = (minx, miny)
            point2 = (maxx, maxy)

            longest_length = distance(point1, point2)

            for idx, (x, y) in enumerate(zip(xs, ys)):
                if idx > 0:
                    dist = distance((x, y), wrist)
                    norm_dist = dist / longest_length
                    data.append(norm_dist)
            db.addEntry(data)

    return jsonify(success=True)


def rps(frame, gesture):
    global RPS_game

    frame_h, frame_w = frame.shape[:-1]

    if RPS_game.getReset() or (gesture == "tu" and not RPS_game.getReset() and not RPS_game.getRunning()):
        RPS_game = RPS()
    if not RPS_game.getRunning():
        if not RPS_game.getResult():
            # faceText.set("Do thumbs up when ready")
            pass
        else:
            cv2.putText(frame, str(RPS_game.getResult()), (50, int(frame_h / 2)), cv2.FONT_HERSHEY_SIMPLEX, 2,
                        (255, 0, 0), 3)
            # labelText.set(RPS.getResult())
        if gesture == "tu":
            RPS_game.start()
    if RPS_game.getRunning():
        cv2.putText(frame, str(RPS_game.getTime()), (int(frame_w / 2), int(frame_h / 2)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2, (255, 0, 0), 3)

        if gesture in ["rock", "paper", "scissors"]:
            RPS_game.setUserChoice(gesture)


def calculateMovement(previous, current):
    x1, y1 = previous
    x2, y2 = current

    # Calculate the raw vector
    dx = x2 - x1
    dy = y2 - y1

    # Determine the closest cardinal direction
    if abs(dx) > abs(dy):
        # Horizontal movement is larger
        if dx > 0:
            return "right"
        else:
            return "left"
    else:
        # Vertical movement is larger or equal
        if dy > 0:
            return "down"
        else:
            return "up"


def functions(hand, gesture, history):
    global waiting_right, waiting_left
    if gesture is None:
        return
    if len(history) < 2 or not len(gesture) or gesture == "NONE":
        return

    previous = history[-2]
    current = history[-1]

    cur_center = current["center"]
    prev_center = previous["center"]

    mvmt = calculateMovement(prev_center, cur_center)

    if hand in config_data['config']:
        config = config_data['config'][hand]

        if gesture in config:
            config_gesture = config[gesture]
            if mvmt in config_gesture:
                scripts = config_gesture[mvmt]
                for script in scripts:
                    script_thread = threading.Thread(target=script_runner.run_script, args=(script,))
                    script_thread.start()
                else:
                    if hand == "right":
                        waiting_right = True
                    elif hand == "left":
                        waiting_left = True

    if "either" not in config_data['config']:
        return
    config = config_data['config']["either"]

    if gesture not in config:
        return
    config_gesture = config[gesture]

    if mvmt not in config_gesture:
        return
    scripts = config_gesture[mvmt]
    for script in scripts:
        script_thread = threading.Thread(target=script_runner.run_script, args=(script,))
        script_thread.start()
    else:
        if hand == "right":
            waiting_right = True
        elif hand == "left":
            waiting_left = True


history_delay = 0

waiting_right, waiting_left = False, False


def process(frame, times):
    global resultHand, history_delay, right_history, left_history, waiting_right, waiting_left

    left_gesture = None
    right_gesture = None

    orientation = (0, 0, 0)

    pinch_distance = 0

    frame_h, frame_w = frame.shape[:-1]

    if mode != "off":
        # Draw the hand annotations on the image.
        frame.flags.writeable = True
        resultHand = hands.process(frame)
        if resultHand.multi_hand_landmarks:

            left_hand_idx = -1
            right_hand_idx = -1

            # Loop through all hands to display them
            for idx, hand_landmarks in enumerate(resultHand.multi_hand_landmarks):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            for idx, hand_handedness in enumerate(resultHand.multi_handedness):
                handedness_dict = MessageToDict(hand_handedness)
                handedness = handedness_dict['classification'][0]['label']
                if handedness == "Left":
                    left_hand_idx = idx
                if handedness == "Right":
                    right_hand_idx = idx

            # times.append(time.time())

            for hand_idx, landmark_list in enumerate(resultHand.multi_hand_landmarks):
                distances = []

                landmark_points = []
                for i in range(21):  # 21 landmarks in MediaPipe hand model
                    x = round(landmark_list.landmark[i].x, 2)
                    y = round(landmark_list.landmark[i].y, 2)
                    landmark_points.append((x, y))

                xs = [x for x, _ in landmark_points]
                ys = [y for _, y in landmark_points]
                wrist = (xs[0], ys[0])

                center_point = (int(np.mean(xs, axis=0).item() * frame_w), int(np.mean(ys, axis=0).item() * frame_h))
                cv2.circle(frame, center_point, 3, (255, 0, 0), 5)

                minx, maxx = np.min(xs), np.max(xs)
                miny, maxy = np.min(ys), np.max(ys)

                min_point = (minx, miny)
                max_point = (maxx, maxy)

                longest_length = distance(min_point, max_point)

                for point in zip(xs, ys):
                    dist = distance(point, wrist)
                    norm_dist = dist / longest_length
                    distances.append(norm_dist)

                thumb_ref_point = (xs[13], ys[13])
                thumb_ref_tip = distance((xs[4], ys[4]), thumb_ref_point) / longest_length
                thumb_ref_middle = distance((xs[2], ys[2]), thumb_ref_point) / longest_length

                fingers = get_finger_positions(distances, thumb_ref_tip, thumb_ref_middle)

                key_data = {
                    "wrist": wrist,
                    "thumb": (xs[4], ys[4]),
                    "index": (xs[8], ys[8]),
                    "middle": (xs[12], ys[12]),
                    "ring": (xs[16], ys[16]),
                    "pinky": (xs[20], ys[20]),
                    "center": center_point,
                    "fingers": fingers
                }

                if fingers[0] and fingers[1]:
                    pinch_distance = distance(key_data["thumb"], key_data["index"])

                    x, y = key_data["thumb"]
                    relative_thumb = (int(x * frame_w), int(y * frame_h))
                    x, y = key_data["index"]
                    relative_index = (int(x * frame_w), int(y * frame_h))

                    cv2.line(frame, relative_thumb, relative_index, color=(255, 0, 0), thickness=2)

                if hand_idx == left_hand_idx:
                    left_gesture = ml_manager.identify(distances[1:])[0]
                    if history_delay == 5:
                        left_history.append(key_data)
                if hand_idx == right_hand_idx:
                    right_gesture = ml_manager.identify(distances[1:])[0]
                    if history_delay == 5:
                        right_history.append(key_data)

            with history_lock:
                if not waiting_right:
                    functions("right", right_gesture, right_history)
                if not waiting_left:
                    functions("left", left_gesture, left_history)
            if history_delay == 5 and mode == "on":
                history_delay = 0
            history_delay += 1

            if left_gesture:
                pass
                # leftText.set(left_gesture)
            if right_gesture:
                pass
                # rightText.set(right_gesture)
        else:  # if resultHand.multi_hand_landmarks
            with history_lock:
                left_history.clear()
                right_history.clear()
            waiting_right = False
            waiting_left = False
            """leftText.set("")
            rightText.set("")"""
    """
    else:  # if not "off"
        leftText.set("")
        rightText.set("")"""

    if right_gesture is None and left_gesture:
        gesture = left_gesture
    else:
        gesture = right_gesture

    if mode == "rps":
        rps(frame, gesture)

    return frame


def gen_frames():
    global fps, h_flip, v_flip
    while True:
        if cap is None:
            continue

        with cap_lock:
            ret, frame = cap.read()

        if not ret:
            break

        # Perform flips
        if not h_flip:
            frame = cv2.flip(frame, 1)
        if v_flip:
            frame = cv2.flip(frame, 0)

        # frame = cv2.resize(frame, (854, 480))
        h, w = frame.shape[:-1]
        ratio = h / w
        new_w = 800
        frame = cv2.resize(frame, (new_w, int(new_w * ratio)))

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = process(frame, None)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        addTime()

        # Add fps counter
        if fps:
            # fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
            fps = 1 / timing_data[0]
            cv2.putText(frame, "FPS : " + str(fps), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/test', methods=['POST'])
def testing():
    data = request.form.get('data')
    print(data)


@app.route('/')
def index_page():
    return render_template('index.html', classes=db.getClasses())


@app.route('/<string:page_name>')
def goto_page(page_name):
    # Validate and sanitize the page_name to ensure it's safe to use
    if ".." in page_name or "/" in page_name:
        abort(404)

    template_path = f"{page_name}.html"

    # Check if template exists
    if os.path.exists(f"templates/{template_path}"):
        return render_template(template_path)
    else:
        abort(404)


@app.route('/video_feed')
def video_feed():
    # return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(
        gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )


@app.route('/submit', methods=['POST'])
def submit():
    global mode
    mode = request.form.get('choice')
    print(f"Selected Option: {mode}")
    return jsonify({"message": f"You selected {mode}"})


@app.route('/load', methods=['GET'])
def loadConfig():
    scripts = [f for f in os.listdir(scripts_dir) if os.path.isfile(os.path.join(scripts_dir, f))]

    return {"classes": db.getClasses(), "config": config_data['config'], "scripts": scripts}


@app.route('/save', methods=['POST'])
def saveConfig():
    data = request.form.get('config')
    config_data['config'] = json.loads(data)

    with open("config.json", "w") as config_file:
        json.dump(config_data, config_file)

    return jsonify(success=True, message="Saved")


def shutdown():
    time.sleep(3)
    os.kill(os.getpid(), signal.SIGINT)


@app.route('/close', methods=['POST'])
def close_app():
    print("Shutting Down")

    with open("config.json", "w") as config_file:
        json.dump(config_data, config_file)

    shutdown_thread = threading.Thread(target=shutdown)
    shutdown_thread.start()

    return jsonify(success=True, message="Closing Application")


def run_flask_app():
    app.run(host='0.0.0.0', port=5000)


# Initialize a deque to store timing data with a maximum length of 50
timing_data = deque(maxlen=50)
last = time.time()


def addTime():
    global last
    current = time.time()
    delta = current - last
    last = current

    # Append the new data point to the deque
    timing_data.append(delta)


@app.route('/get_timing_data', methods=['GET'])
def get_timing_data():
    return jsonify(list(timing_data))


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_flask_app)
    server_thread.start()
