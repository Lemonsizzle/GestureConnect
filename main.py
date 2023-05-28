import time
import math
from tkinter import *
import os
import csv

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera
from HandPositionIdentifier import HPI
import numpy as np

import mediapipe as mp

import matplotlib.pyplot as plt

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class GestureConnect(Tk):
    """
    A GUI application for real-time hand gesture recognition.

    Attributes
    ----------
    fps : int
        The frame rate at which the application captures and processes video frames.

    Methods
    -------
    __init__():
        Initializes an instance of the GestureConnect class.
    __initVariables():
        Initializes the instance attributes.
    __addComponents():
        Adds widgets to the application window.
    pauseTracking():
        Pauses or resumes hand gesture tracking.
    onClose():
        Stops the camera and destroys the application window.
    distance(point, origin):
        Calculates the Euclidean distance between two points.
    run():
        Starts the application's main loop.
    """

    fps = 30

    def __init__(self):
        """
        Initializes an instance of the GestureConnect class.
        """
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

        self.timings_file = 'timings.csv'
        self.timing_cols = ['frame', 'detection', 'classification', 'display']
        with open(self.timings_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.timing_cols)

        self.__initVariables()

        self.__addComponents()

        self.run()
        self.mainloop()

    def __initVariables(self):
        """
        Initializes the instance attributes.
        """
        self.labelText = StringVar()

        self.tolerance = DoubleVar()
        self.tolerance.set(0.04)

        # Cam flip variables
        self.showFPS = IntVar()
        self.hFlip = IntVar()
        self.vFlip = IntVar()

        # Interaction variables
        self.mode = StringVar(value="off")

        self.hands = mp_hands.Hands(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.resultHand = None

        self.classifier = HPI()

    def __addComponents(self):
        """
        Adds widgets to the application window.
        """
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

        Radiobutton(interactions, text="Off", variable=self.mode, value="off").grid(row=0, column=0, sticky=W)
        Radiobutton(interactions, text="On", variable=self.mode, value="on").grid(row=0, column=1, sticky=W)
        Radiobutton(interactions, text="RPS", variable=self.mode, value="rps").grid(row=0, column=2, sticky=W)
        #Radiobutton(interactions, text="", variable=self.mode, value="").grid(row=0, column=, sticky=W)

    def onClose(self):
        """
        Stops the camera and destroys the application window.
        """
        self.camera.stop()
        self.destroy()

    def distance(self, point, origin):
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

    def plotTimings(self, y):
        x = len(y+1)

        self.ax.clear()
        # Update the stackplot data
        self.ax.stackplot(x, y, labels=self.timing_cols)

        plt.show()

    def run(self):
        """
        Starts the application's main loop.
        """
        times = [time.time()]
        ret = None

        while ret is None:
            ret, frame, fps = self.camera.read()

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        self.resultHand = None

        if self.vFlip.get():
            frame = cv.flip(frame, 0)

        if not self.hFlip.get():
            frame = cv.flip(frame, 1)

        times.append(time.time())

        if self.mode.get() != "off":
            # Draw the hand annotations on the image.
            frame.flags.writeable = True
            self.resultHand = self.hands.process(frame)
            if self.resultHand.multi_hand_landmarks:
                # Loop through all hands to display them
                for idx, hand_landmarks in enumerate(self.resultHand.multi_hand_landmarks):
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                times.append(time.time())

                wrist = ()
                xs, ys, zs = [], [], []
                data = []
                landmark_list = self.resultHand.multi_hand_landmarks[0]
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

                longest_length = self.distance(point1, point2)

                for idx, (x, y, z) in enumerate(zip(xs, ys, zs)):
                    if idx > 0:
                        dist = self.distance((x, y, z), wrist)
                        norm_dist = dist / longest_length
                        data.append(norm_dist)

                self.gesture = self.classifier.identify(data)[0]

                self.labelText.set(self.gesture)

                times.append(time.time())
            else:
                self.labelText.set("")
        else:
            self.labelText.set("")

        if self.mode.get() == "rps":
            pass

        if self.showFPS.get():
            cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        times.append(time.time())

        with open(self.timings_file, 'a', newline='') as file:
            writer = csv.writer(file)
            timings = [(times[i] - times[i - 1]) for i in range(1, len(times))]
            if len(timings) == len(self.timing_cols):
                writer.writerow(timings)

        self.viewport.after(int(1000 / self.fps), self.run)


if __name__ == '__main__':
    display = GestureConnect()
