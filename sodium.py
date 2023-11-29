"""Module Imports"""
from sys import exit as sys_exit
from datetime import timedelta
from re import compile as regex_compile
import asyncio
import dearpygui.dearpygui as dpg
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.aac import AAC
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC

class Global:
    """Globalvar vars"""
    tag = 0
    numComplete = 0
    errors = 0

class FD:
    """Data Storage For Loaded File"""
    file = ""
    filePath = ""
    filelengthS = -1
    timecodeLength = ""
    fileExt = ""

def timecode_parser(timecode: str) -> tuple | str:
    """Parses timecode into h, m, s, and ms"""
    valid = timecode_checker(timecode)
    if valid is not True:
        return valid
    has_ms = False
    tc = timecode
    h = ""
    m = ""
    s = ""
    ms = ""

    # If a timecode has a . split timecode into everything else and the ms
    count_ms = timecode.count(".")
    if count_ms == 1:
        has_ms = True
    if has_ms:
        tc, ms = timecode.split(".")

    # Split the timecode into h, m, and s
    count_split = tc.count(":")
    if count_split == 1:
        m, s = tc.split(":")
    elif count_split == 2:
        h, m, s = tc.split(":")

    return h, m, s, ms

def timecode_checker(timecode:str) -> str | bool:
    """Validates timecode"""
    has_ms = False
    tc = timecode
    h = ""
    m = ""
    s = ""
    ms = ""

    regex = regex_compile("^[0-9:.]+$")
    if not regex.match(timecode):
        return "Timecode can only contain 0-9, :, and ."

    # Counts number of .
    count_ms = timecode.count(".")
    # If it is one, then there are ms, if it is >1, then invalid
    if count_ms == 1:
        has_ms = True
    if count_ms > 1:
        return "Multiple . detected"

    # If it has ms, put the timecode without ms into tc
    if has_ms:
        tc, ms = timecode.split(".")
        # If # of digits in ms >3, invalid
        if len(ms) > 3:
            return "Milliseconds greater than 3 digits"

    # Count number of : in tc
    count_split = tc.count(":")

    # If 0, invalid
    if count_split == 0:
        return "Format: [HH:]MM:SS.mmm"

    # If 1, then it only has minutes and second
    if count_split == 1:
        m, s = tc.split(":")
    # If it is 2, then it has hr, min, and sec
    elif count_split == 2:
        h, m, s = tc.split(":")
    # If it has more than 2, then it is invalid
    elif count_split > 2:
        return "Format: [HH:]MM:SS.mmm"

    if len(h) > 2:
        return "Format: [HH:]MM:SS.mmm"
    if not len(m) == 2:
        return "Format: [HH:]MM:SS.mmm"
    if not len(s) == 2:
        return "Format: [HH:]MM:SS.mmm"

    if int(m) >= 60:
        return "Minutes greater than 59"
    if int(s) >= 60:
        return "Seconds greater than 59"

    return True

def calc_timecode(len_seconds: float) -> str:
    """Calculates timecode from given length in seconds"""
    return str(timedelta(seconds=len_seconds)).split("000",maxsplit=1)[0]

async def ffmpeg_cut(inp: str, outname: str, ext: str, caller:str, start="", end=""):
    """Main ffmpeg function to segment a given file"""
    dpg.configure_item(caller+"Error",color=(255,255,255,255))
    output_name = outname+"."+ext

    # If start or end is empty set up options to ignore it
    if start == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("to",end)
            .input(inp)
            .output(output_name)
        )
    elif end == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .input(inp)
            .output(output_name)
        )
    else:
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .option("to",end)
            .input(inp)
            .output(output_name)
        )

    # Logging handlers
    @ffmpeg.on("start")
    def on_start(arguments: list[str]):
        print("arguments:", arguments)

    @ffmpeg.on("stderr")
    def on_stderr(line):
        print("stderr:", line)
        # Print any errors directly to the status line
        dpg.set_value(caller+"Error",line)

    @ffmpeg.on("progress")
    def on_progress(progress: Progress):
        print(progress)

    @ffmpeg.on("completed")
    def on_completed():
        print("completed")

    @ffmpeg.on("terminated")
    def on_terminated():
        print("terminated")

    # Try to execute ffmpeg, set the label to green, and remove the status text
    try:
        await ffmpeg.execute()
        dpg.configure_item(caller+"colLab",color=(0,255,0,255))
        dpg.set_value(caller+"Error","")
        Global.numComplete += 1
    # Otherwise set label to red, and error out
    except Exception as e:
        dpg.configure_item(caller+"Error",color=(255,0,0,255))
        dpg.configure_item(caller+"colLab",color=(255,0,0,255))
        Global.errors += 1
        print(e)

def run_cut():
    """Callback to run ffmpeg segment cuts"""
    # Set final status to white text
    dpg.configure_item("runStatus",color=(255,255,255,255))
    dpg.set_value("runStatus","Running... standby...")
    # Get segements internal id
    segments = dpg.get_item_children("timing")[1]
    # Reset segment label color to white
    for segment in segments:
        dpg.configure_item(dpg.get_item_alias(segment)+"colLab",color=(255,255,255,255))
    # Loop over each segment
    for segment in segments:
        # Get friendly name of segment
        segtag = dpg.get_item_alias(segment)
        # Set label to red as a default
        dpg.configure_item(segtag+"colLab",color=(255,0,0,255))
        # If the segment is disabled, set label to grey color
        if dpg.get_item_label(segtag+"Butt") == "Disabled":
            dpg.configure_item(segtag+"colLab",color=(150,150,150,255))
            continue
        # Run ffmpeg asyncronously
        asyncio.run(ffmpeg_cut(FD.filePath,outname=dpg.get_value(segtag+"Lab"),caller=segtag,ext=FD.fileExt,
                               start=dpg.get_value(segtag+"Start"),end=dpg.get_value(segtag+"End")))
    # Set final status to green
    dpg.configure_item("runStatus",color=(0,255,0,255))

    # String formatting for final status, and resets counters
    seg_str = "segment" if Global.numComplete == 1 else "segements"
    err_str = "error" if Global.errors == 1 else "errors"
    output = "Completed {numComplete} {seg_str} with {errors} {err_str}."
    output = output.format(numComplete=Global.numComplete,seg_str=seg_str,errors=Global.errors,err_str=err_str)
    dpg.set_value("runStatus",output)
    Global.numComplete = 0
    Global.errors = 0

def file_select(sender, app_data):
    """File selecter callbacks"""

    # Reset segment label color to white
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.configure_item(dpg.get_item_alias(segment)+"colLab",color=(255,255,255,255))
        dpg.delete_item(dpg.get_item_alias(segment)+"Error")

    # Forgive me father for I have sinned. Sudo give me the key and value.
    FD.file = str(app_data["selections"].keys()).split("['")[1].split("']")[0]
    FD.filePath = str(app_data["selections"].values()).split("['")[1].split("']")[0]

    # Get file extension
    splitfile = FD.file.split(".")
    FD.fileExt = splitfile[len(splitfile)-1]

    # Get song length
    match FD.fileExt:
        case "mp3":
            FD.filelengthS = MP3(FD.filePath).info.length
        case "wav":
            FD.filelengthS = WAVE(FD.filePath).info.length
        case "aac":
            FD.filelengthS = AAC(FD.filePath).info.length
        case "ogg":
            FD.filelengthS = OggVorbis(FD.filePath).info.length
        case "flac":
            FD.filelengthS = FLAC(FD.filePath).info.length
    FD.timecodeLength = calc_timecode(FD.filelengthS)

    # Display filename, length, and show the buttons to use the program
    dpg.set_value("stat", "Currently loaded file: " + FD.file)
    dpg.set_value('filelen',"File length: " + FD.timecodeLength + " (" + str(FD.filelengthS)+" seconds)")
    dpg.show_item("secAddGroup")
    dpg.show_item("runButt")

def output_toggle(sender):
    """Toggles the label on the enable/disable segment button"""
    if dpg.get_item_label(sender) == "Enabled":
        dpg.set_item_label(sender,"Disabled")
    else:
        dpg.set_item_label(sender,"Enabled")

def timecode_box(sender,user_data):
    """Callback to handle and display errors with timecode input"""
    # Checks if Start or End timecode box called it
    if sender.find("Start") > -1:
        error_text = sender.split("Start")[0]
        err_cause = "Start"
    if sender.find("End") > -1:
        error_text = sender.split("End")[0]
        err_cause = "End"

    # Gets error text, if any
    valid = timecode_checker(user_data)

    # Clears error box or shows error
    if valid is True:
        dpg.configure_item(error_text+"Error",color=(255,255,255,255))
        dpg.set_value(error_text+"Error","")
    else:
        dpg.configure_item(error_text+"Error",color=(255,0,0,255))
        dpg.set_value(error_text+"Error",err_cause + " Error: " + valid)

def add_sec():
    """Adds a section in the segment list"""
    # Generates friendly readable name
    loctag = "tc"+str(Global.tag)

    # Tries to get the previous segments end value for new start value, otherwise make it 00:00:00.000
    segments = dpg.get_item_children("timing")[1]
    last_segment = len(segments)-1
    try:
        last_seg_end = dpg.get_value(dpg.get_item_alias(segments[last_segment])+"End")
    except Exception:
        last_seg_end = "00:00:00.000"
    if last_seg_end == "" or last_seg_end is None:
        last_seg_end = "00:00:00.000"

    with dpg.group(parent="timing",horizontal=True,tag=loctag):
        dpg.add_text("Label:",tag=loctag+"colLab")
        dpg.add_input_text(default_value=str(Global.tag)+" ",tag=loctag+"Lab",width=150)
        dpg.add_text("Start:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=last_seg_end,tag=loctag+"Start",
                           width=100,callback=timecode_box)
        dpg.add_text("End:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"End",
                           width=100,callback=timecode_box)
        #dpg.add_button(label="Up",callback=lambda:dpg.move_item_up(loctag))
        #dpg.add_button(label="Down",callback=lambda:dpg.move_item_down(loctag))
        dpg.add_button(label="Enabled",tag=(loctag+"Butt"), callback=output_toggle)
        dpg.add_button(label="Delete",tag=loctag+"Remove",callback=lambda:dpg.delete_item(loctag))
        dpg.add_text("temp",tag=loctag+"Error")
    Global.tag += 1

dpg.create_context()
dpg.create_viewport(title='Sodium', width=1000, height=600)
dpg.setup_dearpygui()

# Creates file diag thats shows when you open the app
with dpg.file_dialog(label="Select A Music File",tag="fileselect",file_count=1,height=400,width=600,
                     modal=True,show=True,callback=file_select):
    dpg.add_file_extension("Music (*.mp3 *.wav *.aac *.ogg *.flac){.mp3,.wav,.aac,.ogg,.flac}")
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[MP3]")
    dpg.add_file_extension(".wav",color=(0,255,0,255),custom_text="[WAV]")
    dpg.add_file_extension(".aac",color=(0,255,0,255),custom_text="[AAC]")
    dpg.add_file_extension(".ogg",color=(0,255,0,255),custom_text="[OGG]")
    dpg.add_file_extension(".flac",color=(0,255,0,255),custom_text="[FLAC]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

with dpg.window(label="Carbon",tag="main",no_close=True):
    dpg.add_button(label="File Select",callback=lambda: dpg.show_item("fileselect"))
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")
    with dpg.group(tag="secAddGroup",horizontal=True,show=False):
        dpg.add_button(label="Add Section",tag="secButtonAdd",callback=add_sec)
    with dpg.group(tag="timing"):
        pass
    dpg.add_button(label="Execute",tag="runButt",callback=run_cut,show=False)
    dpg.add_text(tag="runStatus")

dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
sys_exit()
