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
parser.add_argument("-p", "--show-preview", default=DEFAULT_SHOW_PREVIEW, help="(must be true) display a preview window alongside your recording")
parser.add_argument("--profile", action='store_true', help="save the screen recording function's performance metrics to file (profile.txt)")
output_file_args = parser.add_mutually_exclusive_group()
output_file_args.add_argument("-t", "--duration", type=float, default=None, help="duration to capture video (seconds)")
#output_file_args.add_argument("-s", "--max-file-size", type=float, default=None, help="do not allow resulting video file to grow beyond this size (MB)")

args = parser.parse_args()
filename = args.output_file
fps = args.frame_rate
if args.show_preview == False:
    print("WARN: preview is required to work")
    #show_preview=True
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
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    if save_profile:
        with open('profile.txt', 'w') as f:
            f.write(s.getvalue())
    if frame_rate_warn_on_exit:
        print("WARN: ")
    print(f"{filename=}")
    print(f"{resolution=}")

print("ready - click and drag to select area to record")

def get_coords():
    def on_click(x,y,button,pressed):
        global rec_x0, rec_y0, rec_x1, rec_y1
        from_xy=0,0
        to_xy=0,0
        if pressed:
            from_xy=x,y
        if not pressed:
            to_xy=x,y
            rec_x0, rec_y0, *_ = from_xy
            rec_x1, rec_y1, *_ = to_xy
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

def capture_frame():
    pr.enable()
    #img = screenshot()
    img = screenshot(region=(rec_x0, rec_y0, rec_x1-rec_x0, rec_y1-rec_y0))
    frame = array(img)
    
    #rows x cols
    # comes in as y rows and x cols
#    _before=frame.shape
#
#    elim = [_del for _del in range(0, rec_x0)]
#    trimmed_before = len(elim)
#    frame = delete(frame, elim, axis=1)
#
#    # grabbing new frame shape here...
#    elim = [_del for _del in range(rec_x1-trimmed_before, frame.shape[1])]
#    frame = delete(frame, elim, axis=1)
#
#    elim = [_del for _del in range(0,rec_y0)]
#    frame = delete(frame, elim, axis=0)
#    trimmed_before = len(elim)
#
#    # ...and here
#    elim = [_del for _del in range(rec_y1-trimmed_before, frame.shape[0])]
#    frame = delete(frame, elim, axis=0)
#    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pr.disable()
    return frame

def record_screen(filename: str, fps: float, resolution: Tuple):
    global vw
    codec = cv2.VideoWriter_fourcc(*"XVID")
    #codec = cv2.VideoWriter_fourcc(*"MP4V")
    vw = cv2.VideoWriter(filename, codec, fps, resolution)

    # optionalish
    if show_preview:
        cv2.namedWindow("live", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("live", resolution[0]+25, resolution[1]+25)

    if capture_for:
        start_time = time.monotonic()

    while True:
        # each iteration needs to complete in fps seconds
        # if we're early, we wait
        t = time.monotonic() 
        if start_time and (t >= start_time + capture_for):
            print("Done")
            break
        frame = capture_frame()

        vw.write(frame)
        if show_preview:
            cv2.imshow("live", frame)
        if cv2.waitKey(1) == ord('q'):
            break
        print(t)
        t_end = time.monotonic()
        print(f"{t_end=} - {t=} = {t_end - t} ({(1/fps)=})")

        # wait before capturing another frame
        if time.monotonic() <= t + 1/fps:
            while time.monotonic() <= t + 1/fps:
                pass
        else:
            print("WARN: frame rate may be too high.")
    # should be handled on exit
    #vw.release()
    #cv2.destroyAllWindows()



get_coords()
resolution = ((rec_x1-rec_x0),(rec_y1-rec_y0))
record_screen(filename,fps,resolution)


