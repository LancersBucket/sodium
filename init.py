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
    try:
        dpg.delete_item(caller+"Error")
    except Exception:
        pass
    dpg.add_text("",parent=caller,tag=caller+"Error",color=(255,255,255,255))
    if (start=="" and end==""):
        return
    elif start == "":
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

    @ffmpeg.on("start")
    def on_start(arguments: list[str]):
        print("arguments:", arguments)

    @ffmpeg.on("stderr")
    def on_stderr(line):
        print("stderr:", line)
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

    try:
        await ffmpeg.execute()
        dpg.configure_item(caller+"colLab",color=(0,255,0,255))
        dpg.delete_item(caller+"Error")
        Global.numComplete += 1
    except Exception as e:
        dpg.configure_item(caller+"Error",color=(255,0,0,255))
        dpg.configure_item(caller+"colLab",color=(255,0,0,255))
        Global.errors += 1
        print(e)

def run_cut():
    """Callback to run ffmpeg segment cuts"""
    dpg.configure_item("runStatus",color=(255,255,255,255))
    dpg.set_value("runStatus","Running... standby...")
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.configure_item(dpg.get_item_alias(segment)+"colLab",color=(255,255,255,255))
    for segment in segments:
        segtag = dpg.get_item_alias(segment)
        dpg.configure_item(segtag+"colLab",color=(255,0,0,255))
        if dpg.get_item_label(segtag+"Butt") == "Disabled":
            dpg.configure_item(segtag+"colLab",color=(150,150,150,255))
            continue
        asyncio.run(ffmpeg_cut(FD.filePath,outname=dpg.get_value(segtag+"Lab"),caller=segtag,
                               start=dpg.get_value(segtag+"Start"),end=dpg.get_value(segtag+"End")))
    dpg.configure_item("runStatus",color=(0,255,0,255))
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
    audio = MP3(FD.filePath)
    FD.filelengthS = audio.info.length
    FD.timecodeLength = calc_timecode(FD.filelengthS)
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

def sec_destroy(sender):
    """Destroys a segment"""
    dpg.delete_item(sender.split("Remove")[0])

def add_sec():
    """Adds a section in the segment list"""
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
        dpg.add_button(label="Delete",tag=loctag+"Remove",callback=sec_destroy)
    Global.tag += 1

dpg.create_context()
dpg.create_viewport(title='Carbon', width=1000, height=600)
dpg.setup_dearpygui()

with dpg.file_dialog(label="Select a music file",tag="fileselect",file_count=1,height=400,width=600,
                     modal=True,show=False,callback=file_select):
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[Music]")
    dpg.add_file_extension(".*",color=(255,0,0,255),custom_text="")

with dpg.window(label="Carbon",tag="main",no_close=True):
    dpg.add_button(label="File Select",callback=lambda: dpg.show_item("fileselect"))
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")
    dpg.add_button(label="Add Section",tag="secButtonAdd",callback=add_sec,show=False)
    with dpg.group(tag="timing"):
        pass
    dpg.add_button(label="RUN!",tag="runButt",callback=run_cut,show=False)
    dpg.add_text(tag="runStatus")

dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
exit()
