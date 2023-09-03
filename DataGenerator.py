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

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


class Display(Tk):
    """
    A GUI application for real-time hand gesture recording.

    Attributes
    ----------
    fps : int
        The frame rate at which the application captures and processes video frames.

    Methods
    -------
    __init__():
        Initializes an instance of the Display class.
    __initVariables():
        Initializes the instance attributes.
    __addComponents():
        Adds widgets to the application window.
    distance(point1, point2):
        Calculates the Euclidean distance between two points.
    record(shape):
        Records the current hand gesture and saves it to a CSV file.
    onClose():
        Stops the camera and destroys the application window.
    run():
        Starts the application's main loop.
    """

    fps = 30

    def __init__(self):
        """
        Initializes an instance of the Display class.
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

        self.camera = Camera("http://192.168.1.55:8000")
        self.camera.start()

        self.temporal_data = []

        self.csv_file = 'data.csv'
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                columns = ['class',
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
        """
        Initializes the instance attributes.
        """
        self.pTime = time.time()

        self.labelText = StringVar()

        self.tolerance = DoubleVar()
        self.tolerance.set(0.04)

        # Cam flip variables
        self.showFPS = IntVar()
        self.hFlip = IntVar()
        self.vFlip = IntVar()

        self.hands = mp_hands.Hands(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.resultHand = None

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

        # Macro recording group
        classButtons = Frame(self)
        classButtons.grid(row=2, column=0)

        # Buttons for recording macros
        Button(classButtons, text="Rock", command=lambda: self.record("rock")).grid(row=0, column=0, sticky=W)
        Button(classButtons, text="Paper", command=lambda: self.record("paper")).grid(row=0, column=1, sticky=W)
        Button(classButtons, text="Scissors", command=lambda: self.record("scissors")).grid(row=0, column=2, sticky=W)
        Button(classButtons, text="Thumbs Up", command=lambda: self.record("tu")).grid(row=0, column=3, sticky=W)
        Button(classButtons, text="Gun", command=lambda: self.record("gun")).grid(row=0, column=4, sticky=W)
        Button(classButtons, text="Point", command=lambda: self.record("point")).grid(row=0, column=5, sticky=W)
        Button()

        dynamicButtons = Frame(self)
        dynamicButtons.grid(row=3, column=0)

        # Buttons for recording macros
        Button(dynamicButtons, text="Snap", command=lambda: self.dynamic(0)).grid(row=0, column=0, sticky=W)
        Button(dynamicButtons, text="Delete", command=lambda: self.dynamic(1)).grid(row=0, column=0, sticky=W)
        Button(dynamicButtons, text="Save", command=lambda: self.dynamic(2)).grid(row=0, column=0, sticky=W)
        Button(dynamicButtons, text="Clear", command=lambda: self.dynamic(3)).grid(row=0, column=0, sticky=W)


    def dynamic(self, function):
        if function == 0:
            pass
        elif function == 1:
            self.temporal_data.pop()
        elif function == 2:
            pass
        elif function == 3:
            self.temporal_data = []

    def distance(self, point1, point2):
        """
        Calculates the Euclidean distance between two points.

        Parameters
        ----------
        point1 : tuple
            The coordinates of the first point.
        point2 : tuple
            The coordinates of the second point.

        Returns
        -------
        float
            The Euclidean distance between the two points.
        """
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def record(self, shape, is_temporal=False):
        """
        Records the current hand gesture and saves it to a CSV file.

        Parameters
        ----------
        is_temporal
        shape : str
            The name of the hand gesture.
        """

        if self.resultHand:
            if self.resultHand.multi_hand_landmarks:
                wrist = ()
                xs, ys, zs = [], [], []
                data = [shape]
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
                if is_temporal:
                    self.temporal_data.append(data)
                else:
                    with open(self.csv_file, 'a+', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(data)

    def onClose(self):
        """
        Stops the camera and destroys the application window.
        """
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.camera.stop()
        self.destroy()

    def run(self):
        """
        Starts the application's main loop.
        """
        ret = None

        while ret is None:
            ret, frame, fps = self.camera.read()

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        self.resultHand = None

        if self.vFlip.get():
            frame = cv.flip(frame, 0)

        if not self.hFlip.get():
            frame = cv.flip(frame, 1)

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

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        self.viewport.after(int(1000 / self.fps), self.run)


if __name__ == '__main__':
    display = Display()
