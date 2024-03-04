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
You can create a .stc (Sodium Timecode) file to import precreated segments. Sodium supports using youtube style timestamps in the following forms. You can optionally chose to provide the end timestamp in this format `[Start]-[End]`, examples are provided below. Otherwise, the end timestamp for the segment will be generated from the start timestamp of the next segment, or the file length for the last segment.
```
[Start] [Label] 
[Start] - [Label]
[Start]: [Label]
[Start]-[End] [Label]
[Start]-[End]: [Label]
[Start]-[End] - [Label]
```
An example file looks as follows:
```
0:00 Song 1
0:30-1:00: Song 2
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
