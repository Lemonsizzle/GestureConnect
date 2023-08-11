import math
import os
import re
import signal
import time

import cv2
import mediapipe as mp
import numpy as np
from HandPositionIdentifier import HPI
from RPS import RPS
import HandModelMaker as HMM
import GCDatabase
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO
from google.protobuf.json_format import MessageToDict

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh

app = Flask(__name__)
socketio = SocketIO(app)

db = GCDatabase.database("data.db")

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


@app.route('/change_source', methods=['POST'])
def change_source(src=None):
    global cap
    if src is None:
        src = request.form.get('src')

    for char in src:
        if char not in "0123456789":
            break
    else:
        src = int(src)

    ip_port = r"^\d+\.\d+\.\d+\.\d+:\d+$"

    if re.match(ip_port, src):
        parts = src.split(":")
        src = f"http://{parts[0]}:{parts[1]}"

    if cap.isOpened():
        cap.release()
    cap = cv2.VideoCapture(src)

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
    x1, y1, z1 = point
    x2, y2, z2 = origin
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


@app.route('/record', methods=['POST'])
def record():
    global resultHand  # , db

    # TODO: implement buttons for recording, also js for generating buttons based on classes
    # shape = request.form.get('shape')
    shape = None
    return

    if resultHand:
        if resultHand.multi_hand_landmarks:
            wrist = ()
            xs, ys, zs = [], [], []
            data = [shape]
            landmark_list = resultHand.multi_hand_landmarks[0]
            for idx, landmark in enumerate(landmark_list.landmark):
                xs.append(landmark.x)
                ys.append(landmark.y)
                zs.append(landmark.z)
                if idx == 0:
                    wrist = (xs[0], ys[0], zs[0])

            minx, maxx = np.min(xs), np.max(xs)
            miny, maxy = np.min(ys), np.max(ys)
            minz, maxz = np.min(zs), np.max(zs)

            point1 = (minx, miny, minz)
            point2 = (maxx, maxy, maxz)

            longest_length = distance(point1, point2)

            for idx, (x, y, z) in enumerate(zip(xs, ys, zs)):
                if idx > 0:
                    dist = distance((x, y, z), wrist)
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
        # labelText.set(RPS.getTime())
        if gesture in ["rock", "paper", "scissors"]:
            RPS_game.setUserChoice(gesture)


def process(frame, times):
    global resultHand

    leftGesture = None
    rightGesture = None

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
                xs, ys, zs = [], [], []
                distances = []

                for idx, landmark in enumerate(landmark_list.landmark):
                    if idx:
                        xs.append(landmark.x)
                        ys.append(landmark.y)
                        zs.append(landmark.z)
                    else:
                        wrist = (landmark.x, landmark.y, landmark.z)

                minx, maxx = np.min(xs), np.max(xs)
                miny, maxy = np.min(ys), np.max(ys)
                minz, maxz = np.min(zs), np.max(zs)

                point1 = (minx, miny, minz)
                point2 = (maxx, maxy, maxz)

                longest_length = distance(point1, point2)

                for (x, y, z) in zip(xs, ys, zs):
                    dist = distance((x, y, z), wrist)
                    norm_dist = dist / longest_length
                    distances.append(norm_dist)

                if hand_idx == left_hand_idx:
                    leftGesture = classifier.identify(distances)[0]
                if hand_idx == right_hand_idx:
                    rightGesture = classifier.identify(distances)[0]

                fingers = get_finger_positions(distances)

                for idx, finger in enumerate(fingers):
                    if finger:
                        cv2.putText(frame, str(1), (int(xs[4 * idx + 3] * frame_w), int(ys[4 * idx + 3] * frame_h)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    2, (255, 0, 0), 3)

            """if leftGesture:
                leftText.set(leftGesture)
            if rightGesture:
                rightText.set(rightGesture)
                
            times.append(time.time())
        else:  # if resultHand.multi_hand_landmarks
            leftText.set("")
            rightText.set("")
    else:  # if not "off"
        leftText.set("")
        rightText.set("")"""

    if rightGesture is None and leftGesture:
        gesture = leftGesture
    else:
        gesture = rightGesture

    if mode == "rps":
        rps(frame, gesture)

    return frame


def gen_frames():
    global fps, h_flip, v_flip
    while True:
        if cap is None:
            continue
        success, frame = cap.read()
        if not success:
            break

        # frame_h, frame_w, _ = frame.shape

        frame = process(frame, None)

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


@app.route('/')
def index():
    return render_template('index.html')


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


@app.route('/close', methods=['POST'])
def close():
    print("Closing")
    os.kill(os.getpid(), signal.SIGINT)
    return 'Closing application...'


if __name__ == '__main__':
    # cap = cv2.VideoCapture("http://192.168.1.55:8000")
    change_source("http://192.168.1.55:8000")
    app.run(host='0.0.0.0', port='5000')
