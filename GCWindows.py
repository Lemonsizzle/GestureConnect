import win32api
import win32con
import win32gui
#import wmi
import ctypes


class WindowsControl:
    def __init__(self):
        pass

    def scroll(self, value):
        # Scroll up or down; positive value scrolls up, negative scrolls down
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, value)
        #print(f"Scrolling by {value}")

    def set_volume(self, level):
        # Set the volume level (0.0 to 1.0)
        devices = ctypes.windll.winmm.waveOutGetVolume(0)
        volume = int(level * 0xFFFF) & 0xFFFF
        ctypes.windll.winmm.waveOutSetVolume(0, volume | (volume << 16))

    def set_brightness(self, level):
        # Set the brightness level (0 to 100)
        c = wmi.WMI(namespace='wmi')
        methods = c.WmiMonitorBrightnessMethods()[0]
        methods.WmiSetBrightness(level, 0)

    def zoom(self, direction):
        # Zoom in or out; positive direction zooms in, negative zooms out
        if direction > 0:
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(win32con.VK_ADD, 0, 0, 0)
            win32api.keybd_event(win32con.VK_ADD, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(win32con.VK_SUBTRACT, 0, 0, 0)
            win32api.keybd_event(win32con.VK_SUBTRACT, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)


if __name__ == "__main__":
    winControl = WindowsControl()
    winControl.scroll(300)
