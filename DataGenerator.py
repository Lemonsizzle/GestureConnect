import time
import math
import threading
from tkinter import *
from tkinter import messagebox
import os
import csv
import numpy as np

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera

import mediapipe as mp

import win32api

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class Display(Tk):
    fps = 30

    def __init__(self):
        super().__init__()
        # Create an instance of TKinter Window or frame
        self.title = "Interface"

        # Set the size of the window
        self.geometry("700x700")

        self.protocol("WM_DELETE_WINDOW", self.onClose)

        # Create a Viewport to capture the Video frames
        self.viewport = Label(self)
        self.viewport.grid(row=0)

        self.camera = Camera(0)
        self.camera.start()

        self.csv_file = 'data.csv'
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                columns = ['class', 'wrist_x', 'wrist_y', 'wrist_z',
                           'thumb_cmc_dist', 'thumb_mcp_dist',
                           'thumb_dip_dist', 'thumb_tip_dist',
                           'index_cmc_dist', 'index_mcp_dist',
                           'index_dip_dist', 'index_tip_dist',
                           'middle_dip_dist', 'middle_tip_dist',
                           'middle_cmc_dist', 'middle_mcp_dist',
                           'ring_cmc_dist', 'ring_mcp_dist',
                           'ring_dip_dist', 'ring_tip_dist',
                           'pinky_cmc_dist', 'pinky_mcp_dist',
                           'pinky_dip_dist', 'pinky_tip_dist']
                writer.writerow(columns)

        self.__initVariables()

        self.__addComponents()

        self.run()
        self.mainloop()

    def __initVariables(self):
        self.displayW, self.displayH = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

        self.pTime = time.time()

        self.labelText = StringVar()

        self.tolerance = DoubleVar()
        self.tolerance.set(0.04)

        # Cam flip variables
        self.showFPS = IntVar()
        self.hFlip = IntVar()
        self.vFlip = IntVar()

        # Interaction variables
        self.recog = IntVar()

        self.hands = mp_hands.Hands(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.resultHand = None

    def __addComponents(self):
        label = Label(self,
                      textvariable=self.labelText,
                      font=("Arial", 16),
                      fg="red",
                      bg="white",
                      padx=10,
                      pady=10)
        label.grid(row=1, column=0)

        slider = Scale(self, from_=0.0, to=0.08, resolution=0.01, orient=HORIZONTAL, variable=self.tolerance,
                       label="Tolerance")
        slider.grid(row=2, column=0)

        # Tracking group
        trackOptions = Frame(self)
        trackOptions.grid(row=3, column=0)

        # Macro recording group
        classButtons = Frame(self)
        classButtons.grid(row=4, column=0)

        # Buttons for recording macros
        Button(classButtons, text="Rock", command=lambda: self.record("rock")).grid(row=0, column=0, sticky=W)
        Button(classButtons, text="Paper", command=lambda: self.record("paper")).grid(row=0, column=1, sticky=W)
        Button(classButtons, text="Scissors", command=lambda: self.record("scissors")).grid(row=0, column=2, sticky=W)
        Button(classButtons, text="Thumbs Up", command=lambda: self.record("tu")).grid(row=0, column=3, sticky=W)
        Button(classButtons, text="Gun", command=lambda: self.record("gun")).grid(row=0, column=4, sticky=W)
        Button(classButtons, text="Point", command=lambda: self.record("point")).grid(row=0, column=5, sticky=W)

    def rotate_points(self, points, theta, origin):
        ox, oy = origin
        theta = math.radians(theta)  # convert degrees to radians

        rotated_points = ()

        x = points[0]
        y = points[1]

        qx = ox + math.cos(theta) * (x - ox) - math.sin(theta) * (y - oy)
        qy = oy + math.sin(theta) * (x - ox) + math.cos(theta) * (y - oy)
        rotated_points = (qx, qy)

        return rotated_points

    def distance(self, point1, point2):
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def record(self, shape):

        if self.resultHand:
            if self.resultHand.multi_hand_landmarks:
                xs, ys, zs = [], [], []
                data_points = [shape]
                landmark_list = self.resultHand.multi_hand_landmarks[0]
                for idx, landmark in enumerate(landmark_list.landmark):
                    xs.append(landmark.x)
                    ys.append(landmark.y)
                    zs.append(landmark.z)

                minx, maxx = np.min(xs), np.max(xs)
                miny, maxy = np.min(ys), np.max(ys)
                minz, maxz = np.min(zs), np.max(zs)

                point1 = (minx, miny, minz)
                point2 = (maxx, maxy, maxz)

                longest_length = self.distance(point1, point2)

                for idx, (x, y, z) in enumerate(zip(xs, ys, zs)):
                    if idx == 0:
                        data_points.append(x)
                        data_points.append(y)
                        data_points.append(z)
                    else:
                        dist = self.distance((x, y, z), (data_points[1], data_points[2], data_points[3]))
                        norm_dist = dist / longest_length
                        data_points.append(norm_dist)

                """for idx, landmark in enumerate(landmark_list.landmark):
                    if idx == 0:
                        data_points.append(landmark.x)
                        data_points.append(landmark.y)
                        data_points.append(landmark.z)
                    else:
                        x, y, z = (landmark.x, landmark.y, landmark.z)
                        dist = self.distance_from_wrist((x, y, z), (data_points[1], data_points[2], data_points[3]))
                        data_points.append(dist)"""

                print(data_points)

                with open(self.csv_file, 'a+', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data_points)

    def onClose(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.camera.stop()
        self.destroy()

    def run(self):
        ret = None

        while ret is None:
            ret, frame, fps = self.camera.read()

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        self.resultHand = None

        if self.vFlip.get():
            frame = cv.flip(frame, 0)

        if not self.hFlip.get():
            frame = cv.flip(frame, 1)

        # frame = handTracker.getFrame()
        frame.flags.writeable = False
        self.resultHand = self.hands.process(frame)

        # Draw the hand annotations on the image.
        frame.flags.writeable = True
        if self.resultHand.multi_hand_landmarks:
            for hand_landmarks in self.resultHand.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Mark thumb as reference
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                x, y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
                cv.circle(frame, (x, y), 5, (0, 255, 0), -1)

        if self.showFPS.get():
            cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        if self.resultHand and self.recog.get():
            if self.resultHand.multi_hand_landmarks:
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                thumb_tip_x, thumb_tip_y = thumb_tip.x, thumb_tip.y
                ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
                ring_tip_x, ring_tip_y = ring_tip.x, ring_tip.y
                ring_middle = hand_landmarks.landmark[14]
                ring_middle_x, ring_middle_y = ring_middle.x, ring_middle.y

                ring_x = (ring_middle_x + ring_tip_x) / 2
                ring_y = (ring_middle_y + ring_tip_y) / 2

                x, y = int(ring_x * frame.shape[1]), int(ring_y * frame.shape[0])

                cv.circle(frame, (x, y), 5, (0, 255, 0), -1)

                distance = math.sqrt((ring_x - thumb_tip_x) ** 2 + (ring_y - thumb_tip_y) ** 2)
                if distance < self.tolerance.get():
                    self.labelText.set("Scissors")
                else:
                    self.labelText.set("Nothing")
            else:
                self.labelText.set("Nothing")

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        self.viewport.after(int(1000 / self.fps), self.run)


if __name__ == '__main__':
    display = Display()
