from typing import Tuple
import atexit
import argparse
import time
import cv2 #requires pillow
from pyautogui import screenshot
from pynput import mouse
#import numpy as np
from numpy import array,delete


DEFAULT_OUTPUT_FILEPATH = 'test_file.avi'
DEFAULT_FRAME_RATE = 30.0
DEFAULT_SHOW_PREVIEW = True
_DEFAULT_DURATION= 2.0 # second

#filename = 'test_file.avi'
#fps = 30.0

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--output-file", default=DEFAULT_OUTPUT_FILEPATH, help="destination for .avi file")
parser.add_argument("-r", "--frame-rate", type=float, default=DEFAULT_FRAME_RATE, help="frame rate at which to capture")
parser.add_argument("-t", "--duration", type=float, default=None, help="frame rate at which to capture")
parser.add_argument("-p", "--show-preview", default=DEFAULT_SHOW_PREVIEW, help="(must be true) display a preview window alongside your recording")

args = parser.parse_args()
filename = args.output_file
fps = args.frame_rate
if args.show_preview == False:
    print("WARN: preview is required to work")
    show_preview=True
show_preview = args.show_preview

start_time = 0.0
if args.duration:
    start_time = args.duration



rec_x0 = 0
rec_y0 = 0
rec_x1 = 0
rec_y1 = 0
resolution = 0,0
from_xy=0,0
to_xy=0,0

class NextFrame(Exception):
    pass
class FrameSyncTimer:
    def __init__(self, fps_tgt):
        self.fps_tgt = fps_tgt
        self.start_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def reset(self):
        self.start_time = None


@atexit.register
def on_exit():
    print(f"{filename=}")
    print(f"{resolution=}")

#@atexit.register
def print_mouse():
    print(f"{filename=}")
    print(f"{from_xy=} {to_xy=}")
    print(f"{rec_x0=}")
    print(f"{rec_y0=}")
    print(f"{rec_x1=}")
    print(f"{rec_y1=}")
    print(f"{resolution=}")

print("ready")

def get_coords():
    def on_click(x,y,button,pressed):
        global from_xy, to_xy
        if pressed:
            from_xy=x,y
        if not pressed:
            to_xy=x,y
            return False
    with mouse.Listener(on_click=on_click, suppress=True) as listener:
        listener.join()

def record_screen(filename: str, fps: float, resolution: Tuple):
    codec = cv2.VideoWriter_fourcc(*"XVID")
    #codec = cv2.VideoWriter_fourcc(*"MP4V")
    vw = cv2.VideoWriter(filename, codec, fps, resolution)

    # optional
    if show_preview:
        cv2.namedWindow("live", cv2.WINDOW_NORMAL)
        #print(f"{resolution=}")
        cv2.resizeWindow("live", resolution[0]+25, resolution[1]+25)


        
    while True:
        # needs to complete in fps seconds
        t = time.monotonic() 

        img = screenshot()
        frame = array(img)
        #rows x cols
        # comes in as y rows and x cols
        _before=frame.shape
        _del_x_before_frame = rec_x0
        _del_x_after_frame = frame.shape[1] - _del_x_before_frame + rec_x1

        elim = [_del for _del in range(0,_del_x_before_frame)]
        trimmed_before = len(elim)
        frame = delete(frame, elim, axis=1)

        elim = [_del for _del in range(rec_x1-trimmed_before, frame.shape[1])]
        frame = delete(frame, elim, axis=1)

        elim = [_del for _del in range(0,rec_y0)]
        frame = delete(frame, elim, axis=0)
        trimmed_before = len(elim)

        elim = [_del for _del in range(rec_y1-trimmed_before, frame.shape[0])]
        frame = delete(frame, elim, axis=0)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        
        vw.write(frame)
        if show_preview:
            cv2.imshow("live", frame)
        if cv2.waitKey(1) == ord('q'):
            break

        if time.monotonic() <= t + 1/fps:
            while time.monotonic() <= t + 1/fps:
                pass
        else:
            print("WARN: frame rate may be too high.")
    vw.release()
    cv2.destroyAllWindows()



get_coords()
rec_x0 = from_xy[0]
rec_y0 = from_xy[1]
rec_x1 = to_xy[0]
rec_y1 = to_xy[1]
if from_xy[0] > to_xy[0]:
    # click-n-dragged from right to left
    rec_x0 = to_xy[0]
    rec_x1 = from_xy[0]
if from_xy[1] > to_xy[1]:
    # click-n-dragged from bottom to top
    rec_y0 = to_xy[1]
    rec_y1 = from_xy[1]


resolution = ((rec_x1-rec_x0),(rec_y1-rec_y0))
record_screen(filename,fps,resolution)


