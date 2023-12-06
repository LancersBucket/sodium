# Sodium
[![/COPYING](https://img.shields.io/badge/License-GPLv3-blue.svg)](/COPYING)

---

> A lightweight music cutter

## About <a name = "about"></a>
Sodium is designed to be a simple and easy program to cut music files into segments.

## Usage
1. Download the latest release from the [releases page](https://github.com/LancersBucket/sodium/releases).
2. Put the audio file you want to cut into the directory of the application (Supports MP3, WAV, AAC, OGG, and FLAC). 
3. Open the application and use the file browser to select your aduio file to start segmenting.
   - Press Add Segment to add a new segment
   - Press Disable to disable a segment from being cut
   - Press Run to start cutting the audio segment

### Importing A Timecode File
You can create a .stc (Sodium Timecode) file to import precreated segments. An .stc file has three parts to it, a segment label, the start time, and end time. There is one segment per line of the file. A "?" separates the label from the timecodes, and optionally have a "-" that separates the start and end time code, or just have a start code. In the event an end code is not present, the end code will be the start code of the next segment (or the file length for the last timecode).
```
[Label]?[Start]-[End]
```
An example file looks as follows:
```
Song 1?00:00:00.000-00:00:30.000
Song 2?00:00:30-00:01:30
Song 3?02:30.000
Song 4?03:00-04:15
```

Alternatively, Sodium supports using youtube style timestamps in the following forms. The end timestamp for the segment will be generated from the start timestamp of the next segment, or the file length for the last segment. Using this format REQUIRES a V2 on the first line of the file.
```
[Label] [Start]
[Label] - [Start]
[Label]: [Start]
```
An example file looks as follows:
```
V2
0:00 Song 1
0:30: Song 2
1:30.567 - Song 3
3:00 Song 4
```

Sodium also supports a .txt file extension in place of a .stc extension 

## TODO
- [ ] Add more functionality for segment creation
   - [ ] Ability to disable segments in .stc files
- [ ] Improve UI layout
- [ ] Make a command line version for fast segmenting

## Contributing
Your contributions are always welcome! If you encounter any bugs or have a feature idea, put it on the [issues](https://github.com/LancersBucket/sodium/issues) page!