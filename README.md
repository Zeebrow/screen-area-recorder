# Area screen recorder

Record an area of your screen and save the recording to a .avi


## debugging

### profiling with cProfile

The frame rate of output videos is a very noticable problem. 

I had a try at "syncing" the rate at which screenshots are captured with the
desired frame rate by using a simple conditional. I get warnings, no matter
what I set `-r` to! 

I decided to isolate the screenshot processing functions and take a closer
look, to see how I might trim some fat.

I ran this command, and selected the menu bar from my desktop for a consistent
size in any comparisons (plus it's easy to remember :)

`python3 rec.py -r 5 --profile -t 3`

Here is a snippet from pstat profiling metrics:

```
$ head -25
         28175 function calls (27905 primitive calls) in 3.168 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       13    0.001    0.000    2.599    0.200 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/pyscreeze/__init__.py:494(_screenshot_linux)
       13    0.000    0.000    2.179    0.168 /usr/lib/python3.9/subprocess.py:341(call)
       26    0.000    0.000    2.139    0.082 /usr/lib/python3.9/subprocess.py:1184(wait)
       26    0.000    0.000    2.139    0.082 /usr/lib/python3.9/subprocess.py:1885(_wait)
       13    0.000    0.000    2.139    0.165 /usr/lib/python3.9/subprocess.py:1872(_try_wait)
       13    2.139    0.165    2.139    0.165 {built-in method posix.waitpid}
       52    0.000    0.000    0.416    0.008 <__array_function__ internals>:177(delete)
   104/52    0.000    0.000    0.416    0.008 {built-in method numpy.core._multiarray_umath.implement_array_function}
       52    0.413    0.008    0.416    0.008 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/numpy/lib/function_base.py:4958(delete)
       26    0.001    0.000    0.408    0.016 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/ImageFile.py:149(load)
      839    0.381    0.000    0.381    0.000 {method 'decode' of 'ImagingDecoder' objects}
    26/13    0.045    0.002    0.152    0.012 {built-in method numpy.array}
       13    0.001    0.000    0.132    0.010 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/Image.py:705(__array__)
       13    0.001    0.000    0.105    0.008 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/Image.py:738(tobytes)
     2808    0.061    0.000    0.061    0.000 {method 'encode' of 'ImagingEncoder' objects}
       13    0.043    0.003    0.043    0.003 {method 'join' of 'bytes' objects}
       13    0.000    0.000    0.039    0.003 /usr/lib/python3.9/subprocess.py:756(__init__)
       13    0.001    0.000    0.039    0.003 /usr/lib/python3.9/subprocess.py:1661(_execute_child)
       13    0.023    0.002    0.023    0.002 {built-in method posix.read}
       13    0.000    0.000    0.019    0.001 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/PngImagePlugin.py:906(load_prepare)

```
`numpy` is being used to transform the screenshot to the size the user selects with the initial click-and-drag. 

The screenshot comes into Python as a really big 2D array - the dimensions are
equal to the resolution on my monitors. In order to get an "area" screen
recording, the unselected area is "cropped" by deleting values from the
screenshot array.

Two ways to speed this up could be
* more efficiently slicing the screenshot array
* taking a more accurate screenshot

Bullet two seems obvious, and I found that `pyautogui.screentshot()` accepts a
`region` keyword argument.

Removing numpy array deletes gives this profile:

```
$ head -25 profile.txt 
         25261 function calls (25041 primitive calls) in 3.088 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       15    0.001    0.000    3.085    0.206 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/pyscreeze/__init__.py:494(_screenshot_linux)
       15    0.000    0.000    2.507    0.167 /usr/lib/python3.9/subprocess.py:341(call)
       30    0.000    0.000    2.452    0.082 /usr/lib/python3.9/subprocess.py:1184(wait)
       30    0.000    0.000    2.451    0.082 /usr/lib/python3.9/subprocess.py:1885(_wait)
       15    0.000    0.000    2.451    0.163 /usr/lib/python3.9/subprocess.py:1872(_try_wait)
       15    2.451    0.163    2.451    0.163 {built-in method posix.waitpid}
       15    0.000    0.000    0.505    0.034 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/Image.py:1187(crop)
       15    0.001    0.000    0.504    0.034 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/ImageFile.py:149(load)
      919    0.465    0.001    0.465    0.001 {method 'decode' of 'ImagingDecoder' objects}
       15    0.000    0.000    0.060    0.004 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/Image.py:2216(save)
       15    0.000    0.000    0.058    0.004 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/PngImagePlugin.py:1217(_save)
       15    0.000    0.000    0.058    0.004 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/ImageFile.py:481(_save)
       75    0.057    0.001    0.057    0.001 {method 'encode' of 'ImagingEncoder' objects}
       15    0.000    0.000    0.055    0.004 /usr/lib/python3.9/subprocess.py:756(__init__)
       15    0.001    0.000    0.055    0.004 /usr/lib/python3.9/subprocess.py:1661(_execute_child)
       15    0.032    0.002    0.032    0.002 {built-in method posix.read}
       15    0.000    0.000    0.031    0.002 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/PngImagePlugin.py:906(load_prepare)
       15    0.000    0.000    0.031    0.002 /home/z/repos/github.com/z/screen-area-recorder/venv/lib/python3.9/site-packages/PIL/ImageFile.py:280(load_prepare)
       15    0.031    0.002    0.031    0.002 {built-in method PIL._imaging.new}
       15    0.019    0.001    0.019    0.001 {built-in method _posixsubprocess.fork_exec}
```

Beach bod?... TBD






### tools

Count frames

```
ffprobe -count_packets -select_streams v:0 -show_entries stream=nb_read_packets test_file.avi
```

functionally equivalent to 

```
ffprobe -count_frames -select_streams v:0 -show_entries stream=nb_read_frames test_file.avi 
```
