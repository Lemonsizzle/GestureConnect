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
from GCWindows import WindowsControl
from flask import Flask, render_template, Response, request, jsonify, abort
from google.protobuf.json_format import MessageToDict
from collections import deque

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh

app = Flask(__name__)

db = GCDatabase.database("data.db")

control_win = WindowsControl()

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

if not os.path.exists(scripts_dir):
    os.mkdir(scripts_dir)

ml_manager = GCML.MLManager()

RPS_game = RPS()

hands = mp_hands.Hands(model_complexity=0,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.6)

resultHand = None

fps = False
h_flip = False
v_flip = False

mode = "off"

lock = threading.Lock()

"""# "time":0, maybe
    "wrist": [],
    "thumb": [],
    "index": [],
    "middle": [],
    "ring": [],
    "pinky": [],
    "finger_pos": []"""
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

    config_data['user_config']['src'] = src

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

            smooth_points = tracker.get_smooth_points()

            xs = [x for x, _ in smooth_points]
            ys = [y for _, y in smooth_points]
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

    # Normalize the vector
    magnitude = math.sqrt(dx ** 2 + dy ** 2)
    if magnitude == 0:
        return (0, 0)

    dx /= magnitude
    dy /= magnitude

    # Eight possible directions
    directions = [
        (1, 0),
        (1 / math.sqrt(2), 1 / math.sqrt(2)),
        (0, 1),
        (-1 / math.sqrt(2), 1 / math.sqrt(2)),
        (-1, 0),
        (-1 / math.sqrt(2), -1 / math.sqrt(2)),
        (0, -1),
        (1 / math.sqrt(2), -1 / math.sqrt(2))
    ]

    # Find the closest direction
    closest_direction = min(directions, key=lambda d: (dx - d[0]) ** 2 + (dy - d[1]) ** 2)

    return closest_direction


move_history = deque(maxlen=10)


def functions():
    if len(history) < 2:
        return

    previous = history[-2]
    current = history[-1]

    labels = ["thumb", "index", "middle", "ring", "pinky"]

    cur_val = list(current.values())
    wrist = cur_val[0]
    cur_fingers = cur_val[1:-1]
    cur_is_up = cur_val[-1]

    previous_val = list(previous.values())
    prev_wrist = previous_val[0]
    prev_fingers = previous_val[1:-1]
    prev_is_up = previous_val[-1]

    if cur_is_up != prev_is_up:
        return

    movement_dict = {}
    for label, cur_finger, prev_finger, is_up in zip(labels, cur_fingers, prev_fingers, cur_is_up):
        if is_up:
            movement_dict[label] = calculateMovement(prev_finger, cur_finger)
    if len(move_history):
        if movement_dict != move_history[0]:
            move_history.append(movement_dict)
    else:
        move_history.append(movement_dict)

    if cur_is_up == [1, 1, 0, 0, 0]:
        pass
    elif cur_is_up == [1, 1, 1, 1, 1]:
        pass
    elif cur_is_up == [0, 1, 1, 0, 0]:
        """if (thumb[1] < prev_thumb[1]) and (index[1] < prev_index[1]):
            control_win.scroll(-120)
        elif (thumb[1] > prev_thumb[1]) and (index[1] > prev_index[1]):
            control_win.scroll(120)"""


# Initialize the PointTracker for each landmark point (21 points)
class PointTracker:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.points = [deque(maxlen=window_size) for _ in range(21)]

    def add_points(self, points):
        for i, point in enumerate(points):
            self.points[i].append(point)

    def get_smooth_points(self):
        smooth_points = []
        for deq in self.points:
            if len(deq) == 0:
                smooth_points.append(None)
                continue
            avg_x = sum(x for x, _ in deq) / len(deq)
            avg_y = sum(y for _, y in deq) / len(deq)
            smooth_points.append((avg_x, avg_y))
        return smooth_points


# Create PointTracker instance
tracker = PointTracker(window_size=3)

history_delay = 0


def process(frame, times):
    global resultHand, history_delay

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

                landmark_points = []
                for i in range(21):  # 21 landmarks in MediaPipe hand model
                    x = round(hand_landmarks.landmark[i].x, 2)
                    y = round(hand_landmarks.landmark[i].y, 2)
                    landmark_points.append((x, y))

                # Add points to tracker and get smoothed points
                smooth_points = landmark_points

                tracker.add_points(landmark_points)
                smooth_points = tracker.get_smooth_points()

                xs = [x for x, _ in smooth_points]
                ys = [y for _, y in smooth_points]
                wrist = (xs[0], ys[0])

                minx, maxx = np.min(xs), np.max(xs)
                miny, maxy = np.min(ys), np.max(ys)

                min_point = (minx, miny)
                max_point = (maxx, maxy)

                longest_length = distance(min_point, max_point)

                for point in zip(xs, ys):
                    dist = distance(point, wrist)
                    norm_dist = dist / longest_length
                    distances.append(norm_dist)

                if hand_idx == left_hand_idx:
                    left_gesture = ml_manager.identify(distances[1:])[0]
                if hand_idx == right_hand_idx:
                    right_gesture = ml_manager.identify(distances[1:])[0]

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
                    "fingers": fingers
                }

                if fingers[0] and fingers[1]:
                    pinch_distance = distance(key_data["thumb"], key_data["index"])

                    x, y = key_data["thumb"]
                    relative_thumb = (int(x * frame_w), int(y * frame_h))
                    x, y = key_data["index"]
                    relative_index = (int(x * frame_w), int(y * frame_h))

                    cv2.line(frame, relative_thumb, relative_index, color=(255, 0, 0), thickness=2)

                if len(history):
                    if fingers != history[0]['fingers']:
                        history.clear()

                history_delay += 1
                if history_delay == 5:
                    history.append(key_data)
                    history_delay = 0

                functions()

                for idx, finger in enumerate(fingers):
                    if finger:
                        cv2.putText(frame, str(1), (int(xs[4 * idx + 4] * frame_w), int(ys[4 * idx + 4] * frame_h)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    2, (255, 0, 0), 3)

            """if left_gesture:
                leftText.set(left_gesture)
            if right_gesture:
                rightText.set(right_gesture)
                
            times.append(time.time())"""
        else:  # if resultHand.multi_hand_landmarks
            history.clear()
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

    show_trails(frame, frame_w, frame_h)

    return frame


def show_trails(frame, w, h):
    for current in history:
        cur_val = list(current.values())
        wrist = cur_val[0]
        cur_fingers = cur_val[1:-1]
        cur_is_up = cur_val[-1]
        for finger, up in zip(cur_fingers, cur_is_up):
            if up:
                x, y = finger
                cv2.circle(frame, (int(x * w), int(y * h)), 3, (0, 255, 0), 1)


def gen_frames():
    global fps, h_flip, v_flip
    tick = 5
    prev = time.time()
    while True:
        if cap is None:
            continue

        with lock:
            ret, frame = cap.read()

        if not ret:
            break

        # Perform flips
        if not h_flip:
            frame = cv2.flip(frame, 1)
        if v_flip:
            frame = cv2.flip(frame, 0)

        # frame = cv2.resize(frame, (854, 480))
        frame = cv2.resize(frame, (1280, 720))

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = process(frame, None)

        """cur = time.time()
                if cur - prev >= tick:
                    if len(history):
                        print(history[-1])
                    prev = cur"""

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

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

@app.route('/load', methods=['GET'])
def loadConfig():
    scripts = [f for f in os.listdir(scripts_dir) if os.path.isfile(os.path.join(scripts_dir, f))]

    return {"config": config_data['config'], "scripts": scripts}

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


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_flask_app)
    server_thread.start()
