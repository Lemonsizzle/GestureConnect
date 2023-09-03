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
from HandPositionIdentifier import HPI
from RPS import RPS
import HandModelMaker as HMM
import GCDatabase
from GCWindows import WindowsControl
from flask import Flask, render_template, Response, request, jsonify, abort
from flask_socketio import SocketIO
from google.protobuf.json_format import MessageToDict
from collections import deque

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh

app = Flask(__name__)
socketio = SocketIO(app)

db = GCDatabase.database("data.db")

control_win = WindowsControl()

cap = cv2.VideoCapture(0)

classifier = HPI()

RPS_game = RPS()

hands = mp_hands.Hands(model_complexity=0,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.8)

resultHand = None

fps = False
h_flip = False
v_flip = False

mode = "off"

config_name = "config.json"
config_data = {}

if os.path.exists(config_name):
    with open(config_name, 'r+') as config_file:
        config_content = config_file.read()
        if config_content and 'src' in config_content:
            config_data = json.loads(config_content)
            cap = cv2.VideoCapture(config_data['src'])

lock = threading.Lock()

"""# "time":0, maybe
    "wrist": [],
    "thumb": [],
    "index": [],
    "middle": [],
    "ring": [],
    "pinky": [],
    "finger_pos": []"""
#history = []
history = deque(maxlen=10)


@app.route('/change_source', methods=['POST'])
def change_source(src=None):
    global cap, lock
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
    with lock:
        if cap.isOpened():
            cap.release()
        cap = cv2.VideoCapture(src)

    config_data['src'] = src

    return jsonify(success=True, message=f"Camera source changed to {src}")


@app.route('/interact', methods=['POST'])
def interact():
    global fps, h_flip, v_flip

    fps = True if request.form.get('fps') == 'on' else False

    h_flip = True if request.form.get('hflip') == 'on' else False

    v_flip = True if request.form.get('vflip') == 'on' else False

    return jsonify({"message": f"You selected"})


def get_finger_positions(distances):
    # Initialize a list with False for each finger
    fingers = [False] * 5

    # Check each finger
    for i in range(5):
        # if the distance to fingertip is less than distance to second knuckle of finger
        if i:
            if distances[4 * i + 1] < distances[4 * i + 3]:
                fingers[i] = True
        """else:
            if distances[4 * i + 1] < distances[4 * i + 3]:
                fingers[i] = True"""

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


@app.route('/record', methods=['POST'])
def record():
    global resultHand  # , db

    # TODO: implement buttons for recording, also js for generating buttons based on classes
    shape = request.form.get('shape')

    if resultHand:
        if resultHand.multi_hand_landmarks:
            wrist = ()
            xs, ys = [], []
            data = [shape]
            landmark_list = resultHand.multi_hand_landmarks[0]
            for idx, landmark in enumerate(landmark_list.landmark):
                xs.append(landmark.x)
                ys.append(landmark.y)
                if idx == 0:
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


def functions():
    if len(history) < 2:
        return

    current = history[-1]
    previous = history[-2]

    labels = ["thumb", "index", "middle", "ring", "pinky"]

    wrist, thumb, index, middle, ring, pinky, fingers = current.values()
    prev_wrist, prev_thumb, prev_index, prev_middle, prev_ring, prev_pinky, prev_fingers = previous.values()

    if fingers == [1, 1, 0, 0, 0]:
        pass
    if fingers == [1, 1, 1, 1, 1]:
        pass
    elif fingers == [0, 1, 1, 0, 0]:
        if (thumb[1] < prev_thumb[1]) and (index[1] < prev_index[1]):
            control_win.scroll(-120)
        elif (thumb[1] > prev_thumb[1]) and (index[1] > prev_index[1]):
            control_win.scroll(120)


def process(frame, times):
    global resultHand

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
                wrist = ()
                xs, ys = [], []
                distances = []

                for idx, landmark in enumerate(landmark_list.landmark):
                    xs.append(landmark.x)
                    ys.append(landmark.y)
                    if not idx:
                        wrist = (xs[0], ys[0])

                minx, maxx = np.min(xs), np.max(xs)
                miny, maxy = np.min(ys), np.max(ys)

                min_point = (minx, miny)
                max_point = (maxx, maxy)

                longest_length = distance(min_point, max_point)

                for (x, y) in zip(xs, ys):
                    dist = distance((x, y), wrist)
                    norm_dist = dist / longest_length
                    distances.append(norm_dist)

                if hand_idx == left_hand_idx:
                    left_gesture = classifier.identify(distances[1:])[0]
                if hand_idx == right_hand_idx:
                    right_gesture = classifier.identify(distances[1:])[0]

                fingers = get_finger_positions(distances)

                key_data = {
                    "wrist": wrist,
                    "thumb": (xs[4], ys[4]),
                    "index": (xs[8], ys[8]),
                    "middle": (xs[12], ys[12]),
                    "ring": (xs[16], ys[16]),
                    "pinky": (xs[20], ys[20]),
                    "fingers": get_finger_positions(distances)
                }

                pinch_distance = distance(key_data["thumb"], key_data["index"])

                x, y = key_data["thumb"]
                relative_thumb = (int(x * frame_w), int(y * frame_h))
                x, y = key_data["index"]
                relative_index = (int(x * frame_w), int(y * frame_h))

                cv2.line(frame, relative_thumb, relative_index, color=(255, 0, 0), thickness=2)

                history.append(key_data)

                functions()

                for idx, finger in enumerate(fingers):
                    if finger:
                        cv2.putText(frame, str(1), (int(xs[4 * idx + 3] * frame_w), int(ys[4 * idx + 3] * frame_h)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    2, (255, 0, 0), 3)

            """if left_gesture:
                leftText.set(left_gesture)
            if right_gesture:
                rightText.set(right_gesture)
                
            times.append(time.time())
        else:  # if resultHand.multi_hand_landmarks
            leftText.set("")
            rightText.set("")
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
    tick = 5
    prev = time.time()
    while True:
        if cap is None:
            continue

        ret = False

        with lock:
            ret, frame = cap.read()
        if not ret:
            break

        # frame_h, frame_w, _ = frame.shape

        frame = process(frame, None)

        """cur = time.time()
                if cur - prev >= tick:
                    if len(history):
                        print(history[-1])
                    prev = cur"""

        # Perform flips
        if h_flip:
            frame = cv2.flip(frame, 1)
        if v_flip:
            frame = cv2.flip(frame, 0)

        # Add fps counter
        if fps:
            # fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
            fps = 30
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


def shutdown():
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGINT)


@app.route('/close', methods=['POST'])
def close_app():
    print("Shutting Down")

    with open("config.json", "w") as config_file:
        json.dump(config_data, config_file)

    shutdown_thread = threading.Thread(target=shutdown)
    shutdown_thread.start()

    time.sleep(5)

    return jsonify(success=True, message="Closing Application")


def run_flask_app():
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_flask_app)
    server_thread.start()
