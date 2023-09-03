from threading import Thread
import cv2 as cv
import time


class Camera:
    def __init__(self, camera=0):

        self.fps = None
        self.running = False
        self.ret = None
        self.frame = None

        self.cap = cv.VideoCapture(camera)

        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True

    def start(self):
        self.running = True
        self.thread.start()
        print(self.thread.name + " started")

    def stop(self):
        if self.running:
            self.running = False
            self.frame = None
            self.cap.release()
            self.thread.join()
            print(self.thread.name + " stopped")

    def read(self):
        return self.ret, self.frame, self.fps

    def update(self):
        pTime = time.time()
        while self.running:
            self.ret, self.frame = self.cap.read()

            if not self.ret:
                break

            cTime = time.time()

            if cTime - pTime == 0:
                continue

            self.fps = int(1 / (cTime - pTime))
            pTime = cTime

            if __name__ == "__main__":
                cv.imshow(f"{self.thread.name}", self.frame)
                cv.waitKey(1)


if __name__ == "__main__":
    cam = Camera(0)
    cam.start()
    time.sleep(5)
    cam.stop()

cv.destroyAllWindows()
