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
   - Press Execute to start cutting the audio segment

In addition, you can also create a .stc (Sodium Timecode) file to import precreated segments. A stc file has three parts to it, a segment label, the start time, and end time. There is one segment per line of the file. A "?" separates the label from the timecodes, and a "-" separates the start and end time code. An example file looks as follows:
```
Song 1?00:00:00.000-00:00:30.000
Song 2?00:00:30.000-00:02:30.000
Song 3?00:02:30.000-00:03:00.000
Song 4?00:03:00.000-00:04:15.000
```
Sodium also supports a .txt file in place of a .stc file 

## TODO
- [ ] Improve UI layout
- [ ] Add more functionality for segment creation

## Contributing
Your contributions are always welcome! If you encounter any bugs or have a feature idea, put it on the [issues](https://github.com/LancersBucket/sodium/issues) page!