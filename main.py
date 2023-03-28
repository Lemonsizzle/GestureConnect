import time
import threading
from tkinter import *
from tkinter import messagebox

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera

import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
mp_holistic = mp.solutions.holistic


class Display(Tk):
    fps = 0

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
        self.pTime = time.time()

        # Cam flip variables
        self.showFPS = IntVar()
        self.hFlip = IntVar()
        self.vFlip = IntVar()

        # Cam tracking variables
        self.trackAll = IntVar()
        self.trackHands = IntVar()
        self.trackBody = IntVar()
        self.trackHead = IntVar()

        self.hands = mp_hands.Hands(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.holistic = mp_holistic.Holistic(model_complexity=0,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.8)

        self.resultHand = None

    def __addComponents(self):
        # Cam adjustment group
        camAdjustments = Frame(self)
        camAdjustments.grid(row=1, column=0)

        # Checkboxes for cam flipping
        Checkbutton(camAdjustments, text="FPS Counter", variable=self.showFPS).grid(row=0, column=0, sticky=W)
        Checkbutton(camAdjustments, text="Horizontal Flip", variable=self.hFlip).grid(row=0, column=1, sticky=W)
        Checkbutton(camAdjustments, text="Vertical Flip", variable=self.vFlip).grid(row=0, column=2, sticky=W)

        # Tracking group
        trackOptions = Frame(self)
        trackOptions.grid(row=2, column=0)

        # Checkboxes for tracking
        Checkbutton(trackOptions, text="Track All", variable=self.trackAll).grid(row=0, column=0, sticky=W)
        Checkbutton(trackOptions, text="Track Hands", variable=self.trackHands).grid(row=0, column=1, sticky=W)
        Checkbutton(trackOptions, text="Track Body", variable=self.trackBody).grid(row=0, column=2, sticky=W)
        Checkbutton(trackOptions, text="Track Head", variable=self.trackHead).grid(row=0, column=3, sticky=W)

        # Macro recording group
        recordingButtons = Frame(self)
        recordingButtons.grid(row=3, column=0)

        # Buttons for recording macros
        Button(recordingButtons, text="Record Hand", command=self.record).grid(row=0, column=0, sticky=W)

    def record(self):
        if self.resultHand.multi_hand_landmarks:
            landmark_list = self.resultHand.multi_hand_landmarks[0]
            for landmark in landmark_list:
                print(landmark)
            """for hand_world_landmarks in self.resultHand.multi_hand_world_landmarks:
                mp_drawing.plot_landmarks(
                    hand_world_landmarks, mp_hands.HAND_CONNECTIONS, azimuth=5)"""

    def onClose(self):
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.camera.stop()
        self.destroy()

    def run(self):
        ret = None

        while ret is None:
            ret, frame, fps = self.camera.read()

        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        if self.trackAll.get():
            results = self.holistic.process(frame)

            # Draw landmark annotation on the image.
            frame.flags.writeable = True
            mp_drawing.draw_landmarks(
                frame,
                results.face_landmarks,
                mp_holistic.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles
                .get_default_face_mesh_contours_style())
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles
                .get_default_pose_landmarks_style())

        elif self.trackHands.get():
            # frame = handTracker.getFrame()
            frame.flags.writeable = False
            self.resultHand = self.hands.process(frame)

            # Draw the hand annotations on the image.
            frame.flags.writeable = True
            frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
            if self.resultHand.multi_hand_landmarks:
                for hand_landmarks in self.resultHand.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())

        if self.vFlip.get():
            frame = cv.flip(frame, 0)

        if self.hFlip.get():
            frame = cv.flip(frame, 1)

        if self.showFPS.get():
            cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        img = Image.fromarray(frame)

        # Convert image to PhotoImage
        imgtk = ImageTk.PhotoImage(image=img)

        self.viewport.imgtk = imgtk
        self.viewport.configure(image=imgtk)

        if self.fps > 0:
            self.viewport.after(int(1000 / self.fps), self.run)
        else:
            self.viewport.after(int(1), self.run)


if __name__ == '__main__':
    display = Display()
