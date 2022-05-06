from typing import Tuple
import atexit
import argparse
import time

import cv2 #requires pillow
from pyautogui import screenshot
from pynput import mouse
from numpy import array,delete

import cProfile, pstats, io
from pstats import SortKey

pr = cProfile.Profile()

### globals
rec_x0 = 0
rec_y0 = 0
rec_x1 = 0
rec_y1 = 0
resolution = 0,0
frame_rate_warn_on_exit = False

from_xy=0,0
to_xy=0,0
###

### defaults
DEFAULT_OUTPUT_FILEPATH = 'test_file.avi'
DEFAULT_FRAME_RATE = 10.0
DEFAULT_SHOW_PREVIEW = False
# TODO
_DEFAULT_DURATION= 2.0 # second
_DEFAULT_MAX_FILESIZE_MB = 5.0
###

### args
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--output-file", default=DEFAULT_OUTPUT_FILEPATH, help="destination for .avi file")
parser.add_argument("-r", "--frame-rate", type=float, default=DEFAULT_FRAME_RATE, help="frame rate to capture (between 10-20 seems to be the sweet spot)")
parser.add_argument("-p", "--show-preview", action='store_true', default=DEFAULT_SHOW_PREVIEW, help="(must be true) display a preview window alongside your recording")
parser.add_argument("--profile", action='store_true', help="save the screen recording function's performance metrics to file (profile.txt)")
output_file_args = parser.add_mutually_exclusive_group()
output_file_args.add_argument("-t", "--duration", type=float, default=None, help="duration to capture video (seconds)")
#output_file_args.add_argument("-s", "--max-file-size", type=float, default=None, help="do not allow resulting video file to grow beyond this size (MB)")

args = parser.parse_args()
filename = args.output_file
fps = args.frame_rate
show_preview = args.show_preview
save_profile = args.profile

capture_for = args.duration
###

# 'trick' our atexit() to tearing down the wideowriter
codec = cv2.VideoWriter_fourcc(*"XVID")
vw = cv2.VideoWriter(filename, codec, fps, (0,0))

@atexit.register
def on_exit():
    vw.release()
    cv2.destroyAllWindows()
    if save_profile:
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        with open('profile.txt', 'w') as f:
            f.write(s.getvalue())
    print(f"{filename=}")
    print(f"{resolution=}")
    if frame_rate_warn_on_exit:
        print("WARN: frame rate may be too high.")

print("ready - click and drag to select area to record")

def get_coords():
    def on_click(x,y,button,pressed):
        global rec_x0, rec_y0, rec_x1, rec_y1, from_xy, to_xy
        if pressed:
            from_xy=x,y
        if not pressed:
            to_xy=x,y
            rec_x0, rec_y0 = from_xy
            rec_x1, rec_y1 = to_xy
            if from_xy[0] > to_xy[0]:
                # click-n-dragged from right to left
                rec_x0 = to_xy[0]
                rec_x1 = from_xy[0]
            if from_xy[1] > to_xy[1]:
                # click-n-dragged from bottom to top
                rec_y0 = to_xy[1]
                rec_y1 = from_xy[1]
            return False
    with mouse.Listener(on_click=on_click, suppress=True) as listener:
        listener.join()
    return (rec_x0, rec_y0),(rec_x1, rec_y1)

def capture_frame():
    pr.enable()
    img = screenshot()
    #img = screenshot(region=(rec_x0, rec_y0, rec_x1-rec_x0, rec_y1-rec_y0))
    frame = array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    elim = [_del for _del in range(0, rec_x0)]
    trimmed_before = len(elim)
    frame = delete(frame, elim, axis=1)

    # grabbing new frame shape here...
    elim = [_del for _del in range(rec_x1-trimmed_before, frame.shape[1])]
    frame = delete(frame, elim, axis=1)

    elim = [_del for _del in range(0,rec_y0)]
    frame = delete(frame, elim, axis=0)
    trimmed_before = len(elim)

    # ...and here
    elim = [_del for _del in range(rec_y1-trimmed_before, frame.shape[0])]
    frame = delete(frame, elim, axis=0)
    pr.disable()
    return frame

def record_screen(filename: str, fps: float, resolution: Tuple):
    codec = cv2.VideoWriter_fourcc(*"XVID")
    vw = cv2.VideoWriter(filename, codec, fps, resolution)

    # optional
    if show_preview:
        cv2.namedWindow("live", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("live", resolution[0]+25, resolution[1]+25)

    start_time = None
    if capture_for:
        start_time = time.monotonic()

    while True:
        # each iteration needs to complete in fps seconds
        # if we're early, we wait
        t_start = time.monotonic() 

        if start_time and (t_start >= start_time + capture_for):
            print("Done")
            break
        frame = capture_frame()
        print(f"x={len(frame)}, y={len(frame[0])}")

        vw.write(frame)
        if show_preview:
            cv2.imshow("live", frame)
            if cv2.waitKey(1) == ord('q'):
                break
        t_end = time.monotonic()
        print(f"{t_end=} - {t_start=} = {t_end - t_start} ({(1/fps)=})")

        # wait before capturing another frame
        if time.monotonic() <= t_start + 1/fps:
            while time.monotonic() <= t_start + 1/fps:
                pass
        else:
            frame_rate_warn_on_exit = True
            #print("WARN: frame rate may be too high.")

coords = get_coords()
print(coords)
resolution = ((rec_x1-rec_x0),(rec_y1-rec_y0))
record_screen(filename,fps,resolution)


