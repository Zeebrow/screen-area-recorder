# Area screen recorder

Record an area of your screen and save the recording to a .avi


## debugging tools

Count frames

```
ffprobe -count_packets -select_streams v:0 -show_entries stream=nb_read_packets test_file.avi
```

functionally equivalent to 

```
ffprobe -count_frames -select_streams v:0 -show_entries stream=nb_read_frames test_file.avi 
```
