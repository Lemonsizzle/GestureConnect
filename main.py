import time
import threading
from tkinter import *
from tkinter import messagebox

import cv2 as cv
from PIL import ImageTk, Image
from ThreadedCamera import Camera


class Display(Tk):
    fps = 0
    lastdang = False
    start = None
    reportTimer = 3
    logged = False

    value = 0

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
        self.trackHands = IntVar()
        self.trackBody = IntVar()
        self.trackHead = IntVar()

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
        Checkbutton(trackOptions, text="Track Hands", variable=self.trackHands).grid(row=0, column=0, sticky=W)
        Checkbutton(trackOptions, text="Track Body", variable=self.trackBody).grid(row=0, column=1, sticky=W)
        Checkbutton(trackOptions, text="Track Head", variable=self.trackHead).grid(row=0, column=2, sticky=W)

    def onClose(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.camera.stop()
            self.destroy()

    def run(self):
        ret, frame, fps = self.camera.read()
        if ret is not None:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            if self.showFPS.get():
                cv.putText(frame, str(int(fps)), (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

            if self.vFlip.get():
                frame = cv.flip(frame, 0)

            if self.hFlip.get():
                frame = cv.flip(frame, 1)

            if self.trackHands.get():


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
