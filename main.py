import time
import math
import threading
from tkinter import *
from tkinter import messagebox

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera
from HandPositionIdentifier import HPI

import matplotlib.pyplot as plt

import mediapipe as mp

import win32api

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
mp_holistic = mp.solutions.holistic


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

        # self.cap = cv.VideoCapture(0)

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

        # Cam tracking variables
        self.trackHands = IntVar()
        self.trackEyes = IntVar()

        # Interaction variables
        self.recog = IntVar()
        self.cursor = IntVar()

        self.hands = mp_hands.Hands(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.holistic = mp_holistic.Holistic(model_complexity=0,
                                             min_detection_confidence=0.5,
                                             min_tracking_confidence=0.8)

        self.resultHand = None

        self.classifier = HPI()

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

        # Cam adjustment group
        camAdjustments = Frame(self)
        camAdjustments.grid(row=3, column=0)

        # Checkboxes for cam flipping
        Checkbutton(camAdjustments, text="FPS Counter", variable=self.showFPS).grid(row=0, column=0, sticky=W)
        Checkbutton(camAdjustments, text="Horizontal Flip", variable=self.hFlip).grid(row=0, column=1, sticky=W)
        Checkbutton(camAdjustments, text="Vertical Flip", variable=self.vFlip).grid(row=0, column=2, sticky=W)

        # Tracking group
        trackOptions = Frame(self)
        trackOptions.grid(row=4, column=0)

        # Checkboxes for tracking
        Checkbutton(trackOptions, text="Track Hands", variable=self.trackHands).grid(row=0, column=0, sticky=W)
        Checkbutton(trackOptions, text="Track Eyes", variable=self.trackEyes).grid(row=0, column=1, sticky=W)

        # Checkboxes for interactivity
        interactions = Frame(self)
        interactions.grid(row=5, column=0)

        Checkbutton(interactions, text="Recognition", variable=self.recog).grid(row=0, column=0, sticky=W)
        Checkbutton(interactions, text="Cursor", variable=self.cursor).grid(row=0, column=1, sticky=W)

        # Macro recording group
        recordingButtons = Frame(self)
        recordingButtons.grid(row=6, column=0)

        # Buttons for recording macros
        Button(recordingButtons, text="Record Hand", command=self.record).grid(row=0, column=0, sticky=W)

    def record(self):
        if self.resultHand:
            if self.resultHand.multi_hand_landmarks:
                data = []
                landmark_list = self.resultHand.multi_hand_landmarks[0]
                for idx, landmark in enumerate(landmark_list.landmark):
                    data.append(landmark.x)
                    data.append(landmark.y)

                self.classifier.identify(data)

    def onClose(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.camera.stop()
        self.destroy()

    def distance_from_wrist(self, point, origin):
        x1, y1, z1 = point
        x2, y2, z2 = origin
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

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

        if self.trackHands.get() or True:
            # frame = handTracker.getFrame()
            frame.flags.writeable = False
            self.resultHand = self.hands.process(frame)

            # Draw the hand annotations on the image.
            frame.flags.writeable = True
            if self.resultHand.multi_hand_landmarks:
                for hand_landmarks in self.resultHand.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    if self.cursor.get():
                        # Mark index as reference
                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        x, y = int(index_finger_tip.x * frame.shape[1]), int(index_finger_tip.y * frame.shape[0])
                        cv.circle(frame, (x, y), 5, (0, 255, 0), -1)
                    elif self.recog.get():
                        # Mark thumb as reference
                        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                        x, y = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
                        cv.circle(frame, (x, y), 5, (0, 255, 0), -1)

        if self.showFPS.get():
            cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        if self.resultHand and self.cursor.get():
            if self.resultHand.multi_hand_landmarks:
                # landmark_list = self.resultHand.multi_hand_landmarks[0]
                for hand_landmarks in self.resultHand.multi_hand_landmarks:
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    win32api.SetCursorPos((int(self.displayW * index_finger_tip.x),
                                           int(self.displayH * index_finger_tip.y)))

        if self.resultHand:
            if self.resultHand.multi_hand_landmarks:
                origin = ()
                data = []
                landmark_list = self.resultHand.multi_hand_landmarks[0]
                for idx, landmark in enumerate(landmark_list.landmark):
                    if idx == 0:
                        origin = (landmark.x, landmark.y, landmark.z)
                    else:
                        x, y, z = (landmark.x, landmark.y, landmark.z)
                        dist = self.distance_from_wrist((x, y, z), origin)
                        data.append(dist)

                self.labelText.set(self.classifier.identify(data)[0])

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        self.viewport.after(int(1000 / self.fps), self.run)


if __name__ == '__main__':
    display = Display()
