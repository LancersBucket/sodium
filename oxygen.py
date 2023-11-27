"""Module Imports"""
from datetime import timedelta
import asyncio
import dearpygui.dearpygui as dpg
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg
from mutagen.mp3 import MP3

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

def calc_timecode(len_seconds: float) -> str:
    """Calculates timecode from given length in seconds"""
    return str(timedelta(seconds=len_seconds)).split("000",maxsplit=1)[0]

async def ffmpeg_cut(inp: str, outname: str, caller:str, start="", end=""):
    """Main ffmpeg function to segment a given file"""
    # Checks if [caller]Error exists and if so, remove it. Otherwise keep going.
    try:
        dpg.delete_item(caller+"Error")
    except Exception:
        pass
    # Add status text for specific segment
    dpg.add_text("",parent=caller,tag=caller+"Error",color=(255,255,255,255))

    # If start or end is empty set up options to ignore it
    if start == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("to",end)
            .input(inp)
            .output(outname+".mp3")
        )
    elif end == "":
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .input(inp)
            .output(outname+".mp3")
        )
    else:
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("ss",start)
            .option("to",end)
            .input(inp)
            .output(outname+".mp3")
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
        dpg.delete_item(caller+"Error")
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
        asyncio.run(ffmpeg_cut(FD.filePath,outname=dpg.get_value(segtag+"Lab"),caller=segtag,
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
    # Forgive me father for I have sinned
    FD.file = str(app_data["selections"].keys()).split("['")[1].split("']")[0]
    FD.filePath = str(app_data["selections"].values()).split("['")[1].split("']")[0]

    # Get song length
    FD.filelengthS = MP3(FD.filePath).info.length
    FD.timecodeLength = calc_timecode(FD.filelengthS)

    # Display filename, length, and show the buttons to use the program
    dpg.set_value("stat", "Currently loaded file: " + FD.file)
    dpg.set_value('filelen',"File length: " + FD.timecodeLength + " (" + str(FD.filelengthS)+" seconds)")
    dpg.show_item("secButtonAdd")
    dpg.show_item("runButt")

def output_toggle(sender):
    """Toggles the label on the enable/disable segment button"""
    if dpg.get_item_label(sender) == "Enabled":
        dpg.set_item_label(sender,"Disabled")
    else:
        dpg.set_item_label(sender,"Enabled")

def add_sec():
    """Adds a section in the segment list"""
    # Generates friendly readable name
    loctag = "tc"+str(Global.tag)
    with dpg.group(parent="timing",horizontal=True,tag=loctag):
        dpg.add_text("Label:",tag=loctag+"colLab")
        dpg.add_input_text(default_value=Global.tag,tag=loctag+"Lab",width=100)
        dpg.add_text("Start:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"Start",width=100)
        dpg.add_text("End:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"End",width=100)
        dpg.add_button(label="Up",callback=lambda:dpg.move_item_up(loctag))
        dpg.add_button(label="Down",callback=lambda:dpg.move_item_down(loctag))
        dpg.add_button(label="Enabled",tag=(loctag+"Butt"), callback=output_toggle)
        dpg.add_button(label="Delete",tag=loctag+"Remove",callback=lambda:dpg.delete_item(loctag))
    Global.tag += 1

dpg.create_context()
dpg.create_viewport(title='Oxygen', width=1000, height=600)
dpg.setup_dearpygui()

# Creates file diag thats shows when you open the app
with dpg.file_dialog(label="Select A Music File",tag="fileselect",file_count=1,height=400,width=600,
                     modal=True,show=True,callback=file_select):
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[Music]")
    dpg.add_file_extension("",color=(150, 150, 150, 255))

with dpg.window(label="Carbon",tag="main",no_close=True):
    dpg.add_button(label="File Select",callback=lambda: dpg.show_item("fileselect"))
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")
    dpg.add_button(label="Add Section",tag="secButtonAdd",callback=add_sec,show=False)
    with dpg.group(tag="timing"):
        pass
    dpg.add_button(label="Execute",tag="runButt",callback=run_cut,show=False)
    dpg.add_text(tag="runStatus")

dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
exit()
