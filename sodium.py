"""Module Imports"""
from re import compile as regex_compile
from sys import exit as sys_exit
from datetime import timedelta
import asyncio
import dearpygui.dearpygui as dpg
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.aac import AAC

class Global:
    """Globalvar vars"""
    VERSION = "v1.2.2"
    tag = 0
    numComplete = 0
    errors = 0

class FD:
    """Data Storage For Loaded File"""
    file = ""
    filePath = ""
    filelengthS = -1
    timecodeLength = ""
    parsedTimecode = ["","","",""]
    fileExt = ""

def timecode_parser(timecode: str, retvalid=True) -> tuple:
    """Parses timecode into h, m, s, and ms, optionally return if parsed timecode is valid"""
    valid = timecode_validate(timecode)
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

    if retvalid:
        return h, m, s, ms, valid
    return h, m, s, ms

def timecode_validate(timecode:str) -> str | bool:
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
        if len(ms) == 0:
            return "Specified milliseconds but none provided"

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
        return "Format: [HH:]MM:SS[.mmm]"

    if len(h) > 2:
        return "Format: [HH:]MM:SS[.mmm]"
    if not len(m) == 2:
        return "Format: [HH:]MM:SS[.mmm]"
    if not len(s) == 2:
        return "Format: [HH:]MM:SS[.mmm]"

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
    def on_start(arguments: list[str]):
        print("arguments:", arguments)

    @ffmpeg.on("stderr")
    def on_stderr(line):
        print("stderr:", line)
        # Print any errors directly to the status line
        if line.find("[sw") == -1:
            dpg.set_value(caller+"Error",line)
        if line.find("Press [q]") >= 0:
            dpg.set_value(caller+"Error","Running...")

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
    dpg.hide_item("runButt")
    # Get segements internal id
    segments = dpg.get_item_children("timing")[1]
    # Set final status to white text
    dpg.configure_item("runStatus",color=(255,255,255,255))
    dpg.set_value("runStatus","Running... ({done}/{total})".format(
        done=Global.numComplete+Global.errors,total=len(segments)))
    dpg.show_item("load")
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
        dpg.set_value("runStatus","Running... ({done}/{total})".format(
            done=Global.numComplete+Global.errors,total=len(segments)))
    # Set final status to green
    dpg.configure_item("runStatus",color=(0,255,0,255))
    dpg.hide_item("load")
    dpg.show_item("runButt")

    # String formatting for final status, and resets counters
    seg_str = "segment" if Global.numComplete == 1 else "segements"
    err_str = "error" if Global.errors == 1 else "errors"
    output = "Completed {numComplete} {seg_str} with {errors} {err_str}."
    output = output.format(numComplete=Global.numComplete,seg_str=seg_str,errors=Global.errors,err_str=err_str)
    dpg.set_value("runStatus",output)
    Global.numComplete = 0
    Global.errors = 0

def music_select(sender, app_data):
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

    # Get song length depending on the file type
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
    FD.filelengthS = round(FD.filelengthS, 3)
    FD.timecodeLength = calc_timecode(FD.filelengthS)
    FD.parsedTimecode = timecode_parser(FD.timecodeLength,retvalid=False)

    # Display filename, length, and show the buttons to use the program
    dpg.set_value("stat", "Currently loaded file: " + FD.file)
    dpg.set_value('filelen',"File length: " + FD.timecodeLength + " (" + str(FD.filelengthS)+" seconds)")
    dpg.show_item("secAddGroup")
    dpg.show_item("runButt")

    # Enable importing/exporting STC file
    dpg.show_item("importSTC")
    dpg.show_item("exportSTC")

def output_toggle(sender):
    """Toggles the label on the enable/disable segment button"""
    if dpg.get_item_label(sender) == "Enabled":
        dpg.set_item_label(sender,"Disabled")
        dpg.set_value(sender.split("Butt")[0]+"Error","")
    else:
        dpg.set_item_label(sender,"Enabled")

def timecode_compare(time1: tuple[int], time2: tuple[int]) -> int:
    """1 for time1 being larger than time2, 0 if they are the same, -1 if time2 is larger than time1"""
    h1, m1, s1, ms1 = time1
    h2, m2, s2, ms2 = time2

    # Compare h1 and h2, if they are the same fall through to next check
    if h1>h2:
        return 1
    if h1<h2:
        return -1
    # Compare m1 and m2, if they are the same fall through to next check
    if m1>m2:
        return 1
    if m1<m2:
        return -1
    # Compare s1 and s2, if they are the same fall through to next check
    if s1>s2:
        return 1
    if s1<s2:
        return -1
    # Compare ms1 and ms2, if they are the same return 0
    if ms1>ms2:
        return 1
    if ms1<ms2:
        return -1
    return 0

def timecode_box(sender, user_data):
    """Callback to handle and display errors with timecode input"""
    # Checks if Start or End timecode box called it
    if sender.find("Start") > -1:
        error_text = sender.split("Start")[0]
        err_cause = "Start"
    if sender.find("End") > -1:
        error_text = sender.split("End")[0]
        err_cause = "End"

    # Gets error text, if any
    valid = timecode_validate(user_data)
    h, m, s, ms, valid = timecode_parser(user_data)

    # Get other box input and check if it is better or worse you know what I mean
    if err_cause == "Start":
        h2, m2, s2, ms2, valid2 = timecode_parser(dpg.get_value(error_text+"End"))
        if valid2 is True:
            compared = timecode_compare((h,m,s,ms),(h2,m2,s2,ms2))
            if compared == 1:
                valid = "Start time is greater than end time"
            elif compared == 0:
                valid = "Times cannot be the same"
    if err_cause == "End":
        h2, m2, s2, ms2, valid2 = timecode_parser(dpg.get_value(error_text+"Start"))
        if valid2 is True:
            compared = timecode_compare((h,m,s,ms),(h2,m2,s2,ms2))
            if compared == -1:
                valid = "Start time is greater than end time"
            elif compared == 0:
                valid = "Times cannot be the same"

    # Clears error box or shows error
    if valid is True:
        dpg.configure_item(error_text+"Error",color=(255,255,255,255))
        dpg.set_value(error_text+"Error","")
    else:
        dpg.configure_item(error_text+"Error",color=(255,0,0,255))
        dpg.set_value(error_text+"Error",err_cause + " Error: " + valid)

    # Checks if timecode is larger than file length and shows a warning if so
    if timecode_compare([h,m,s,ms], FD.parsedTimecode) == 1:
        dpg.configure_item(error_text+"Error",color=(255,165,0,255))
        dpg.set_value(error_text+"Error",err_cause + " Warning: Timecode larger than file length")

def add_sec(sender, app_data, user_data, label=None,start=None,end=None):
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
        if label is None:
            dpg.add_input_text(default_value=str(Global.tag)+" ",tag=loctag+"Lab",width=150)
        else:
            dpg.add_input_text(default_value=label,tag=loctag+"Lab",width=150)
        dpg.add_text("Start:")
        if start is None:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=last_seg_end,tag=loctag+"Start",
                               width=100,callback=timecode_box)
        else:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=start,tag=loctag+"Start",
                               width=100,callback=timecode_box)
        dpg.add_text("End:")
        if end is None:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"End",
                               width=100,callback=timecode_box)
        else:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=end,tag=loctag+"End",
                               width=100,callback=timecode_box)
        dpg.add_button(label="Enabled",tag=(loctag+"Butt"), callback=output_toggle)
        dpg.add_button(label="Delete",tag=loctag+"Remove",callback=lambda:dpg.delete_item(loctag))
        dpg.add_text(tag=loctag+"Error")
    Global.tag += 1

def import_file(sender, app_data):
    """Callback to parse and import a STC file"""
    # Reset status
    dpg.configure_item("runStatus",color=(255,255,255,255))
    dpg.set_value("runStatus","")

    # Purge all current segments
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.delete_item(segment)

    # Forgive me father for I have sinned. Sudo give me the key and value.
    file = str(app_data["selections"].keys()).split("['")[1].split("']")[0]
    file_path = str(app_data["selections"].values()).split("['")[1].split("']")[0]

    # 0: label, 1: time_start, 2: time_end
    file_data = [[],[],[]]

    error = False
    count = 1
    for line in open(file_path,"r",encoding="UTF-8").readlines():
        if line.find("?") <= 0:
            error = f"Error on line {count} of {file}: Missing ?".format(count=count,file=file)
            break
        if line.find("-") <= 0:
            error = f"Error on line {count} of {file}: Missing -".format(count=count,file=file)
            break

        label, timecodes = line.split("?")
        time_start, time_end = timecodes.split("-")

        label = label.strip()
        time_start = time_start.strip()
        time_end = time_end.strip()

        valid_start = timecode_validate(time_start)
        valid_end = timecode_validate(time_end)

        if valid_start is not True:
            error = f"Error on line {count} of {file}: Start timecode {valid_start}"
            break
        if valid_end is not True:
            error = f"Error on line {count} of {file}: End timecode {valid_end}"
            break

        file_data[0].append(label)
        file_data[1].append(time_start)
        file_data[2].append(time_end)
        count += 1

    if error is not False:
        dpg.configure_item("runStatus",color=(255,0,0,255))
        dpg.set_value("runStatus", error)
        return

    for i in range(len(file_data[0])):
        add_sec(None, None, None, file_data[0][i], file_data[1][i], file_data[2][i])

def export_file():
    """Handles exporting the file"""
    segments = dpg.get_item_children("timing")[1]
    with open(dpg.get_value("exportName")+".stc","w",encoding="UTF-8") as file:
        for segment in segments:
            segtag = dpg.get_item_alias(segment)
            file.write("{lab}?{start}-{end}\n".format(lab=dpg.get_value(segtag+"Lab"),
                                                    start=dpg.get_value(segtag+"Start"),
                                                    end=dpg.get_value(segtag+"End")))
    dpg.delete_item("tcexportmodal")

def export_file_window():
    """Creates the export file window"""
    with dpg.window(label="Export Timecodes",tag="tcexportmodal",
                    no_move=True,no_collapse=True,no_close=True,modal=True,no_resize=True,height=10):
        with dpg.group(horizontal=True):
            dpg.add_text("Enter a file name:")
            dpg.add_input_text(label=".stc",tag="exportName",width=100)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Export",tag="exportFileButt",callback=export_file)
            dpg.add_button(label="Cancel",callback=lambda:dpg.delete_item("tcexportmodal"))

    # Force next render frame so window shows up and size can be calculated
    dpg.split_frame()

    # Get move window to middle of screen
    width = dpg.get_item_width("tcexportmodal")
    height = dpg.get_item_height("tcexportmodal")

    pos = [(dpg.get_viewport_width()//2)-(width//2),
           (dpg.get_viewport_height()//2)-(height//2)]

    dpg.configure_item("tcexportmodal",pos=pos)

# Initalizing dpg
dpg.create_context()
dpg.create_viewport(title='Sodium ' + Global.VERSION, width=1000, height=600)
dpg.setup_dearpygui()

# Creates file diag thats shows when you open the app
with dpg.file_dialog(label="Select A Music File",tag="musicselect",file_count=1,height=400,width=600,
                     modal=True,show=True,callback=music_select):
    dpg.add_file_extension("Music (*.mp3 *.wav *.aac *.ogg *.flac){.mp3,.wav,.aac,.ogg,.flac}")
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[MP3]")
    dpg.add_file_extension(".wav",color=(0,255,0,255),custom_text="[WAV]")
    dpg.add_file_extension(".aac",color=(0,255,0,255),custom_text="[AAC]")
    dpg.add_file_extension(".ogg",color=(0,255,0,255),custom_text="[OGG]")
    dpg.add_file_extension(".flac",color=(0,255,0,255),custom_text="[FLAC]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

# Import diag
with dpg.file_dialog(label="Select A Sodium Timecode File",tag="fileselect",file_count=1,height=400,width=600,
                     modal=True,show=False,callback=import_file):
    dpg.add_file_extension("Sodium Timecode (*.stc *.txt){.stc,.txt}")
    dpg.add_file_extension(".stc",color=(0,255,0,255),custom_text="[Timecode]")
    dpg.add_file_extension(".txt",color=(0,255,0,255),custom_text="[Timecode]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

# Main window
with dpg.window(label="Sodium",tag="main",no_close=True):
    # Top row of buttons and file info
    with dpg.group(horizontal=True):
        dpg.add_button(label="File Select",callback=lambda: dpg.show_item("musicselect"))
        dpg.add_button(label="Import Timecode",tag="importSTC",callback=lambda: dpg.show_item("fileselect"),show=False)
        dpg.add_button(label="Export Timecode",tag="exportSTC",callback=export_file_window,show=False)
        dpg.add_text("Sodium " + Global.VERSION)
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")

    # Segment area
    with dpg.group(tag="secAddGroup",horizontal=True,show=False):
        dpg.add_button(label="Add Section",tag="secButtonAdd",callback=add_sec)
    with dpg.group(tag="timing"):
        pass

    # Run button and loading text
    dpg.add_button(label="Run",tag="runButt",callback=run_cut,show=False)
    with dpg.group(horizontal=True):
        dpg.add_loading_indicator(tag="load", circle_count=6,color=(29, 151, 236, 255),
                                  secondary_color=(51, 51, 55, 255), speed=2, radius=1.5, show=False)
        dpg.add_text(tag="runStatus")

# Set primary window to the main window and start dpg
dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
sys_exit()
