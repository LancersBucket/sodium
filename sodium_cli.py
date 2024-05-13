"""Sodium CLI"""
import asyncio
import getopt
import os
import sys
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
import sodium_core as SC

class Global:
    """Globalvar vars"""
    numComplete = 0
    errors = 0

async def ffmpeg_cut(inp: str, outname: str, ext: str, start="", end="") -> None:
    """Main ffmpeg function to segment a given file"""
    output_name = f"{outname}.{ext}"

    # If start or end is empty set up options to ignore it
    if start == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("to",end)
            .input(inp)
            .output(output_name, acodec="copy")
        )
    elif end == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .input(inp)
            .output(output_name, acodec="copy")
        )
    else:
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .option("to",end)
            .input(inp)
            .output(output_name, acodec="copy")
        )

    # Logging handlers
    @ffmpeg.on("start")
    def on_start(_arguments: list[str]):
        pass
        #print("arguments:", arguments)

    @ffmpeg.on("stderr")
    def on_stderr(line):
        print("FFmpeg:", line)

    @ffmpeg.on("progress")
    def on_progress(_progress: Progress):
        pass
        #print(progress)

    @ffmpeg.on("completed")
    def on_completed():
        print("completed")

    @ffmpeg.on("terminated")
    def on_terminated():
        print("terminated")

    # Try to execute ffmpeg, set the label to green, and remove the status text
    try:
        await ffmpeg.execute()
        Global.numComplete += 1
    # Otherwise set label to red, and error out
    except Exception as e:
        Global.errors += 1
        print(e)

def run_cut(file_path,file_name,file_length,sodium_file,jobname) -> None:
    """Callback to run ffmpeg segment cuts"""
    label_arr, time_start_arr, time_end_arr, error = SC.process_timecode_file(sodium_file,sodium_file,file_length)

    if error is not False:
        print(error)
        return

    # Run ffmpeg asyncronously and make the output folder if needed
    file_ext = file_name.split(".")[len(file_name.split("."))-1]

    if jobname == "":
        outputdir = file_name.split(file_ext)[0]
    else:
        outputdir = jobname

    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)
    elif os.path.isdir(outputdir) and len(os.listdir(outputdir)) > 0:
        warn = input(f"Warning: Output directory ({os.path.abspath(outputdir)}) is not empty and may overwrite files. Continue [y/N]? ")
        if warn.lower() != "y":
            print("Aborted.")
            sys.exit()

    # Loop over each segment
    for i, ele in enumerate(label_arr):
        asyncio.run(ffmpeg_cut(file_path, outname=os.path.join(outputdir, ele), ext=file_ext,
                               start=time_start_arr[i], end=time_end_arr[i]))

    # String formatting for final status, and resets counters
    seg_str = "segment" if Global.numComplete == 1 else "segements"
    err_str = "error" if Global.errors == 1 else "errors"

    output = f"\nCompleted {Global.numComplete} {seg_str} with {Global.errors} {err_str}.\nOutput folder: {os.path.abspath(outputdir)}"
    print(output)
    Global.numComplete = 0
    Global.errors = 0

def main(argv):
    """Main"""
    inputfile = ''
    sodiumfile = ''
    jobname = ''
    try:
        opts, _args = getopt.getopt(argv,"hi:s:j:",["ifile=","sfile=","jname="])
    except getopt.GetoptError:
        print('sodium_cli.py -i <inputfile> -s <Sodium Timecode File> [-j <Job name>]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('sodium_cli.py -i <inputfile> -s <Sodium Timecode File> [-j <Job name>]')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-s", "--sfile"):
            sodiumfile = arg
        elif opt in ("-j", "--jname"):
            jobname = arg

    if inputfile == "" or sodiumfile == "":
        print('sodium_cli.py -i <inputfile> -s <Sodium Timecode File> [-j <Job name>]')
        sys.exit(2)

    run_cut(inputfile,inputfile,0,sodiumfile,jobname)

if __name__ == "__main__":
    main(sys.argv[1:])
