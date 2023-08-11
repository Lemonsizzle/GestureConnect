<<<<<<< HEAD
from threading import Thread
=======
import threading
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)
import cv2 as cv
import time


<<<<<<< HEAD
class Camera:
    def __init__(self, camera=0):
=======
class Camera(threading.Thread):
    def __init__(self, camera=0):
        super().__init__()
        self.setDaemon(True)
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)

        self.fps = None
        self.running = False
        self.ret = None
        self.frame = None

        self.cap = cv.VideoCapture(camera)

<<<<<<< HEAD
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True

    def start(self):
        self.running = True
        self.thread.start()
        print(self.thread.name + " started")
=======
    def go(self):
        self.running = True
        print(threading.current_thread().name + " started")
        self.start()
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)

    def stop(self):
        if self.running:
            self.running = False
            self.frame = None
            self.cap.release()
<<<<<<< HEAD
            self.thread.join()
            print(self.thread.name + " stopped")
=======
            print(threading.current_thread().name + " stopped")
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)

    def read(self):
        return self.ret, self.frame, self.fps

<<<<<<< HEAD
    def update(self):
=======
    def run(self):
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)
        pTime = time.time()
        while self.running:
            self.ret, self.frame = self.cap.read()

            if not self.ret:
                break

            cTime = time.time()

            if cTime - pTime == 0:
                continue

            self.fps = int(1/(cTime - pTime))
            pTime = cTime

            if __name__ == "__main__":
<<<<<<< HEAD
                cv.imshow(f"{self.thread.name}", self.frame)
=======
                cv.imshow(f"{threading.current_thread().name}", self.frame)
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)
                cv.waitKey(1)


if __name__ == "__main__":
    cam = Camera(0)
<<<<<<< HEAD
    cam.start()
    time.sleep(5)
    cam.stop()

cv.destroyAllWindows()
=======
    cam.go()
    time.sleep(5)
    cam.stop()
    cv.destroyAllWindows()
>>>>>>> fbd6065 (Converted app to utilize flask instead of tkinter for interfacing)
