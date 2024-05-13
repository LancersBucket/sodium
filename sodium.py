"""Module Imports"""
import os
from sys import exit as sys_exit
import asyncio
import dearpygui.dearpygui as dpg
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.aac import AAC
import sodium_core as SC

class Global:
    """Globalvar vars"""
    VERSION = "Sodium v1.4.2-DEV"
    tag = 0
    numComplete = 0
    errors = 0

class FD:
    """Data Storage For Loaded File"""
    file = ""
    filePath = ""
    folderPath = ""
    filelengthS = -1
    timecodeLength = ""
    # Hours, Minutes, Seconds, MS
    parsedTimecode = ["","","",""]
    fileExt = ""

class Color:
    """Colors\n
        General: WHITE, GREY\n
        Status: OK (Green), WARN (Orange), ERR (Red)"""
    WHITE = (255,255,255,255)
    GREY = (150,150,150,255)
    OK = (0,255,0,255)
    WARN = (255,165,0,255)
    ERR = (255,0,0,255)

async def ffmpeg_cut(inp: str, outname: str, ext: str, caller: str, start="", end="") -> None:
    """Main ffmpeg function to segment a given file"""
    dpg.configure_item(f"{caller}Error",color=Color.WHITE)
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
    def on_start(arguments: list[str]):
        print("arguments:", arguments)

    @ffmpeg.on("stderr")
    def on_stderr(line):
        print("stderr:", line)
        # Print any errors directly to the status line
        if line.find("[sw") == -1:
            dpg.set_value(f"{caller}Error",line)
        if line.find("Press [q]") >= 0:
            dpg.set_value(f"{caller}Error","Running...")

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
        dpg.configure_item(f"{caller}colLab",color=Color.OK)
        dpg.set_value(f"{caller}Error","")
        Global.numComplete += 1
    # Otherwise set label to red, and error out
    except Exception as e:
        dpg.configure_item(f"{caller}Error",color=Color.ERR)
        dpg.configure_item(f"{caller}colLab",color=Color.ERR)
        Global.errors += 1
        print(e)

def run_cut() -> None:
    """Callback to run ffmpeg segment cuts"""
    dpg.hide_item("runButt")
    # Get segements internal id
    segments = dpg.get_item_children("timing")[1]
    # Set final status to white text
    dpg.configure_item("runStatus",color=Color.WHITE)
    dpg.set_value("runStatus",f"Running... ({Global.numComplete+Global.errors}/{len(segments)})")
    dpg.show_item("load")

    outputdir = os.path.join(FD.folderPath,dpg.get_value("JobName"))
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)

    # Reset segment label color to white
    for segment in segments:
        dpg.configure_item(f"{dpg.get_item_alias(segment)}colLab",color=Color.WHITE)
    # Loop over each segment
    for segment in segments:
        # Get friendly name of segment
        segtag = dpg.get_item_alias(segment)
        # Set label to red as a default
        dpg.configure_item(f"{segtag}colLab",color=Color.ERR)
        # If the segment is disabled, set label to grey color
        if dpg.get_item_label(f"{segtag}Butt") == "Disabled":
            dpg.configure_item(f"{segtag}colLab",color=Color.GREY)
            continue

        # Run ffmpeg asyncronously and make the output folder if needed
        asyncio.run(ffmpeg_cut(FD.filePath,
                               outname=(os.path.join(outputdir,dpg.get_value(f"{segtag}Lab"))),
                               caller=segtag,ext=FD.fileExt,start=dpg.get_value(f"{segtag}Start"),
                               end=dpg.get_value(f"{segtag}End")))
        dpg.set_value("runStatus",f"Running... ({Global.numComplete+Global.errors}/{len(segments)})")
    # Set final status to green
    dpg.configure_item("runStatus",color=Color.OK)
    dpg.hide_item("load")
    dpg.show_item("runButt")

    # String formatting for final status, and resets counters
    seg_str = "segment" if Global.numComplete == 1 else "segements"
    err_str = "error" if Global.errors == 1 else "errors"

    output = f"Completed {Global.numComplete} {seg_str} with {Global.errors} {err_str}.\nOutput folder: {outputdir}"
    dpg.set_value("runStatus", output)
    Global.numComplete = 0
    Global.errors = 0

def sudo_keyvalue(dat: dict) -> tuple[str]:
    """Returns first key and value of dict"""
    key, value = next(iter(dat.items()), (None, None))
    return key, value

def music_file_selected(_sender, app_data):
    """Music file selecter callback"""
    # Reset segment label color to white
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.configure_item(f"{dpg.get_item_alias(segment)}colLab",color=Color.WHITE)
        dpg.delete_item(f"{dpg.get_item_alias(segment)}Error")

    FD.file, FD.filePath = sudo_keyvalue(app_data["selections"])

    # Get the folder path, excluding the file name
    splt = FD.filePath.split("\\")
    FD.folderPath = ""
    for i in range(len(splt)-1):
        FD.folderPath += f"{splt[i]}\\"

    # Get file extension
    splitfile = FD.file.split(".")
    FD.fileExt = splitfile[len(splitfile)-1]

    # Set the job name
    jobname = f"{splitfile[0]}-split"
    job_name_new = jobname
    inc = 0
    while os.path.isdir(os.path.join(FD.folderPath,job_name_new)):
        inc += 1
        job_name_new = jobname+f"_{inc}"

    dpg.set_value("JobName",job_name_new)

    # Get song length depending on the file type
    file_length = -1
    match FD.fileExt:
        case "mp3":
            file_length = MP3(FD.filePath).info.length
        case "wav":
            file_length = WAVE(FD.filePath).info.length
        case "aac":
            file_length = AAC(FD.filePath).info.length
        case "ogg":
            file_length = OggVorbis(FD.filePath).info.length
        case "flac":
            file_length = FLAC(FD.filePath).info.length
    FD.filelengthS = round(file_length, 3)
    FD.timecodeLength = SC.timecode_calculate(FD.filelengthS)
    FD.parsedTimecode = SC.timecode_parser(FD.timecodeLength,retvalid=False)

    # Display filename, length, and show the buttons to use the program
    dpg.set_value("stat", "Currently Loaded File: " + FD.filePath.replace("\\\\","/"))
    dpg.configure_item("stat",color=Color.OK)
    dpg.set_value("filelen",f"File Length: {FD.timecodeLength} ({FD.filelengthS} seconds)")
    dpg.show_item("secAddGroup")
    dpg.show_item("runButt")

    # Enable importing/exporting STC file buttons
    dpg.show_item("importSTC")
    dpg.show_item("exportSTC")

    # Misc items
    dpg.show_item("jobNameGroup")
    dpg.show_item("sep1")
    dpg.show_item("sep2")

def enable_disable_toggle(sender):
    """Toggles the label on the enable/disable segment button"""
    if dpg.get_item_label(sender) == "Enabled":
        dpg.set_item_label(sender,"Disabled")
        dpg.set_value(f"{sender.split('Butt')[0]}Error","")
    else:
        dpg.set_item_label(sender,"Enabled")

def timecode_box(sender, user_data):
    """Callback to handle and display errors with timecode input"""
    # Checks if Start or End timecode box called it
    if sender.find("Start") > -1:
        error_text = sender.split("Start")[0]
        err_cause = "Start"
    if sender.find("End") > -1:
        error_text = sender.split("End")[0]
        err_cause = "End"

    h, m, s, ms, valid = SC.timecode_parser(user_data)

    # Get other box input and check if it is better or worse you know what I mean
    if err_cause == "Start":
        h2, m2, s2, ms2, valid2 = SC.timecode_parser(dpg.get_value(f"{error_text}End"))
        if valid2 is True:
            compared = SC.timecode_compare((h,m,s,ms),(h2,m2,s2,ms2))
            if compared == 1:
                valid = "Start time is greater than end time"
            elif compared == 0:
                valid = "Times cannot be the same"
    if err_cause == "End":
        h2, m2, s2, ms2, valid2 = SC.timecode_parser(dpg.get_value(f"{error_text}Start"))
        if valid2 is True:
            compared = SC.timecode_compare((h,m,s,ms),(h2,m2,s2,ms2))
            if compared == -1:
                valid = "Start time is greater than end time"
            elif compared == 0:
                valid = "Times cannot be the same"

    # Clears error box or shows error
    if valid is True:
        dpg.configure_item(f"{error_text}Error",color=Color.WHITE)
        dpg.set_value(f"{error_text}Error","")
    else:
        dpg.configure_item(f"{error_text}Error",color=Color.ERR)
        dpg.set_value(f"{error_text}Error", f"{err_cause} Error: {valid}")

    # Checks if timecode is larger than file length and shows a warning if so
    if SC.timecode_compare([h,m,s,ms], FD.parsedTimecode) == 1:
        dpg.configure_item(f"{error_text}Error",color=Color.WARN)
        dpg.set_value(f"{error_text}Error",f"{err_cause} Warning: Timecode larger than file length")

def add_section(_sender, _app_data, _user_data, label: str = None, start: str = None, end: str = None) -> None:
    """Adds a section in the segment list"""
    # Generates friendly readable name
    loctag = "tc"+str(Global.tag)

    # Tries to get the previous segments end value for new start value, otherwise make it 00:00:00.000
    segments = dpg.get_item_children("timing")[1]
    last_segment = len(segments)-1
    try:
        last_seg_end = dpg.get_value(f"{dpg.get_item_alias(segments[last_segment])}End")
    except Exception:
        last_seg_end = "00:00:00.000"
    if last_seg_end == "" or last_seg_end is None:
        last_seg_end = "00:00:00.000"

    with dpg.group(parent="timing",horizontal=True,tag=loctag):
        dpg.add_text("Label:",tag=f"{loctag}colLab")
        if label is None:
            dpg.add_input_text(default_value=f"{Global.tag} ",tag=f"{loctag}Lab",width=-450)
        else:
            dpg.add_input_text(default_value=label,tag=f"{loctag}Lab",width=-450)
        dpg.add_text("Start:")
        if start is None:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=last_seg_end,tag=f"{loctag}Start",
                               width=100,callback=timecode_box)
        else:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=start,tag=f"{loctag}Start",
                               width=100,callback=timecode_box)
        dpg.add_text("End:")
        if end is None:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=f"{loctag}End",
                               width=100,callback=timecode_box)
        else:
            dpg.add_input_text(hint="HH:MM:SS.mmm",default_value=end,tag=f"{loctag}End",
                               width=100,callback=timecode_box)
        dpg.add_button(label="Enabled",tag=f"{loctag}Butt", callback=enable_disable_toggle)
        dpg.add_button(label="Delete",tag=f"{loctag}Remove",callback=lambda:dpg.delete_item(loctag))
        dpg.add_text(tag=f"{loctag}Error")
    Global.tag += 1

def import_stc(_sender, app_data):
    """Callback to import an STC file"""
    # Reset status
    dpg.configure_item("runStatus",color=Color.WHITE)
    dpg.set_value("runStatus","")

    # Purge all current segments
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.delete_item(segment)

    file, file_path = sudo_keyvalue(app_data["selections"])

    label_arr, time_start_arr, time_end_arr, error = SC.process_timecode_file(file_path, file, FD.timecodeLength)

    if error is not False:
        dpg.configure_item("runStatus",color=Color.ERR)
        dpg.set_value("runStatus", error)
        return

    if dpg.get_value("imp_Numbering"):
        for i, _ele in enumerate(label_arr):
            label_arr[i] = f"{i+1} " + label_arr[i]

    for i, _ele in enumerate(label_arr):
        add_section(None, None, None, label_arr[i], time_start_arr[i], time_end_arr[i])

def export_timecode_file():
    """Handles exporting the file"""
    segments = dpg.get_item_children("timing")[1]
    with open(f"{dpg.get_value('exportName')}.stc","w",encoding="UTF-8") as file:
        for segment in segments:
            segtag = dpg.get_item_alias(segment)
            file.write(f"{dpg.get_value(segtag+'Lab')}?{dpg.get_value(segtag+'Start')}-{dpg.get_value(segtag+'End')}\n")
    dpg.delete_item("tcexportmodal")

def export_file_window():
    """Creates the export file window"""
    with dpg.window(label="Export Timecodes",tag="tcexportmodal",
                    no_move=True,no_collapse=True,no_close=True,modal=True,no_resize=True,height=10):
        with dpg.group(horizontal=True):
            dpg.add_text("Enter a file name:")
            dpg.add_input_text(label=".stc",tag="exportName",width=100)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Export",tag="exportFileButt",callback=export_timecode_file)
            dpg.add_button(label="Cancel",callback=lambda:dpg.delete_item("tcexportmodal"))

    # Force next render frame so window shows up and size can be calculated
    dpg.split_frame()

    # Get move window to middle of screen
    width = dpg.get_item_width("tcexportmodal")
    height = dpg.get_item_height("tcexportmodal")

    pos = [(dpg.get_viewport_width()//2)-(width//2),
           (dpg.get_viewport_height()//2)-(height//2)]

    dpg.configure_item("tcexportmodal",pos=pos)

def toggle_all_segments():
    """Goes through each segment and toggles the status"""
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        segtag = dpg.get_item_alias(segment)
        enable_disable_toggle(f"{segtag}Butt")

# Initalizing dpg
dpg.create_context()
dpg.create_viewport(title=Global.VERSION, width=1000, height=600)
dpg.setup_dearpygui()

# Creates file diag thats shows when you open the app
with dpg.file_dialog(label="Select A Music File",tag="musicselect",file_count=1,height=400,width=600,
                     modal=True,show=True,callback=music_file_selected):
    dpg.add_file_extension("Music (*.mp3 *.wav *.aac *.ogg *.flac){.mp3,.wav,.aac,.ogg,.flac}")
    dpg.add_file_extension(".mp3",color=Color.OK,custom_text="[MP3]")
    dpg.add_file_extension(".wav",color=Color.OK,custom_text="[WAV]")
    dpg.add_file_extension(".aac",color=Color.OK,custom_text="[AAC]")
    dpg.add_file_extension(".ogg",color=Color.OK,custom_text="[OGG]")
    dpg.add_file_extension(".flac",color=Color.OK,custom_text="[FLAC]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

# Import diag
with dpg.file_dialog(label="Select A Sodium Timecode File",tag="fileselect",file_count=1,height=400,width=800,
                     modal=True,show=False,callback=import_stc):
    dpg.add_file_extension("Sodium Timecode (*.stc *.txt){.stc,.txt}")
    dpg.add_file_extension(".stc",color=Color.OK,custom_text="[Timecode]")
    dpg.add_file_extension(".txt",color=Color.OK,custom_text="[Timecode]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

    dpg.add_text("Import Options:")
    dpg.add_checkbox(label="Segment Numbering",tag="imp_Numbering")

# Main window
with dpg.window(label="Sodium",tag="main",no_close=True):
    # Top row of buttons and file info
    with dpg.group(horizontal=True):
        dpg.add_button(label="File Select",callback=lambda:dpg.show_item("musicselect"))
        dpg.add_button(label="Import Timecode",tag="importSTC",callback=lambda:dpg.show_item("fileselect"),show=False)
        dpg.add_button(label="Export Timecode",tag="exportSTC",callback=export_file_window,show=False)
        dpg.add_text(Global.VERSION)
    dpg.add_text("No File Loaded", tag="stat",color=Color.ERR)
    dpg.add_text(tag="filelen")

    dpg.add_separator(tag="sep1",show=False)

    # Job name box
    with dpg.group(tag="jobNameGroup",horizontal=True,show=False):
        dpg.add_text("Job Name:")
        dpg.add_input_text(tag="JobName",width=400)

    # Segment area
    with dpg.group(tag="secAddGroup",horizontal=True,show=False):
        dpg.add_button(label="Add Section",tag="secButtonAdd",callback=add_section)
        dpg.add_button(label="Enable/Disable All Sections",callback=toggle_all_segments)

    # Timing area
    with dpg.group(tag="timing"):
        pass

    dpg.add_text()
    dpg.add_separator(tag="sep2",show=False)

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
