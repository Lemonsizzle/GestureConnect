import time
import math
import threading
from tkinter import *
from tkinter import messagebox

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera
from HandPositionIdentifier import HPI
import numpy as np

import mediapipe as mp

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

        self.__initVariables()

        self.__addComponents()

        self.run()
        self.mainloop()

    def __initVariables(self):
        self.labelText = StringVar()

        self.tolerance = DoubleVar()
        self.tolerance.set(0.04)

        # Cam flip variables
        self.showFPS = IntVar()
        self.hFlip = IntVar()
        self.vFlip = IntVar()

        # Interaction variables
        self.tracking = True

        self.hands = mp_hands.Hands(model_complexity=0,
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

        # Cam adjustment group
        camAdjustments = Frame(self)
        camAdjustments.grid(row=2, column=0)

        # Checkboxes for cam flipping
        Checkbutton(camAdjustments, text="FPS Counter", variable=self.showFPS).grid(row=0, column=0, sticky=W)
        Checkbutton(camAdjustments, text="Horizontal Flip", variable=self.hFlip).grid(row=0, column=1, sticky=W)
        Checkbutton(camAdjustments, text="Vertical Flip", variable=self.vFlip).grid(row=0, column=2, sticky=W)

        # Checkboxes for interactivity
        interactions = Frame(self)
        interactions.grid(row=3, column=0)

        self.pauseButton = Button(interactions, text="Pause", command=self.pauseTracking)
        self.pauseButton.grid(row=0, column=0, sticky=W)

    def pauseTracking(self):
        self.tracking = not self.tracking
        self.pauseButton.config(text=("Pause" if self.tracking else "Resume"))

    def onClose(self):
        self.camera.stop()
        self.destroy()

    def distance(self, point, origin):
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

        if self.tracking:
            # Draw the hand annotations on the image.
            frame.flags.writeable = True
            self.resultHand = self.hands.process(frame)
            if self.resultHand.multi_hand_landmarks:
                for hand_landmarks in self.resultHand.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                xs, ys, zs = [], [], []
                data = []
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
                        origin = (x, y, z)
                    else:
                        dist = self.distance((x, y, z), origin)
                        norm_dist = dist / longest_length
                        data.append(norm_dist)

                self.labelText.set(self.classifier.identify(data)[0])
            else:
                self.labelText.set("")
        else:
            self.labelText.set("")

        if self.showFPS.get():
            cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        self.viewport.after(int(1000 / self.fps), self.run)


if __name__ == '__main__':
    display = Display()
