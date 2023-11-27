import os, sys, asyncio
import dearpygui.dearpygui as dpg
from mutagen.mp3 import MP3
from datetime import timedelta
from ffmpeg import Progress
from ffmpeg.asyncio import FFmpeg

tag = 0
numComplete = 0
errors = 0

class FD:
    file = ""
    filePath = ""
    filelengthS = -1
    timecodeLength = ""

    def calcTimecode(lenS: float) -> str:
        return str(timedelta(seconds=lenS)).split("000")[0]

async def ffmpegCut(inp: str, outname: str, caller:str, start="", end=""):
    try:
        dpg.delete_item(caller+"Error")
    except Exception as e:
        pass
    dpg.add_text("",parent=caller,tag=caller+"Error",color=(255,255,255,255))
    if (start=="" and end==""):
        return
    elif (start == ""):
        ffmpeg = (
            FFmpeg()
            .option("y")
            .option("to",end)
            .input(inp)
            .output(outname+".mp3")
        )
    elif (end == ""):
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

    global numComplete
    global errors
    try:
        await ffmpeg.execute()
        dpg.configure_item(caller+"colLab",color=(0,255,0,255))
        dpg.delete_item(caller+"Error")
        numComplete += 1
    except Exception as e:
        dpg.configure_item(caller+"Error",color=(255,0,0,255))
        dpg.configure_item(caller+"colLab",color=(255,0,0,255))
        errors += 1
        print(e)
        
def runCut():
    global numComplete
    global errors
    dpg.configure_item("runStatus",color=(255,255,255,255))
    dpg.set_value("runStatus","Running... standby...")
    segments = dpg.get_item_children("timing")[1]
    for segment in segments:
        dpg.configure_item(dpg.get_item_alias(segment)+"colLab",color=(255,255,255,255))
    for segment in segments:
        segtag = dpg.get_item_alias(segment)
        dpg.configure_item(segtag+"colLab",color=(255,0,0,255))
        if (dpg.get_item_label(segtag+"Butt") == "Disabled"):
            dpg.configure_item(segtag+"colLab",color=(124,124,124,255))
            continue
        asyncio.run(ffmpegCut(FD.filePath,outname=dpg.get_value(segtag+"Lab"),caller=segtag, start=dpg.get_value(segtag+"Start"),end=dpg.get_value(segtag+"End")))
    dpg.configure_item("runStatus",color=(0,255,0,255))
    segStr = "segment" if numComplete == 1 else "segements"
    errStr = "error" if errors == 1 else "errors"
    output = "Completed {numComplete} {segStr} with {errors} {errStr}."
    output = output.format(numComplete=numComplete,segStr=segStr,errors=errors,errStr=errStr)
    dpg.set_value("runStatus",output)
    numComplete = 0
    errors = 0

def fileSelect(sender, app_data):
    # Forgive me father for I have sinned
    FD.file = str(app_data["selections"].keys()).split("['")[1].split("']")[0]
    FD.filePath = str(app_data["selections"].values()).split("['")[1].split("']")[0]
    audio = MP3(FD.filePath)
    FD.filelengthS = audio.info.length
    FD.timecodeLength = FD.calcTimecode(FD.filelengthS)
    dpg.set_value("stat", "Currently loaded file: " + FD.file)
    dpg.set_value('filelen',"File length: " + FD.timecodeLength + " (" + str(FD.filelengthS)+")")
    dpg.show_item("secButtonAdd")
    dpg.show_item("runButt")

def outputToggle(sender):
    if (dpg.get_item_label(sender) == "Enabled"):
        dpg.set_item_label(sender,"Disabled")
    else:
        dpg.set_item_label(sender,"Enabled")

def segDestroy(sender):
    dpg.delete_item(sender.split("Remove")[0])

def addSec():
    global tag
    loctag = "tc"+str(tag)
    with dpg.group(parent="timing",horizontal=True,tag=loctag):
        dpg.add_text("Label:",tag=loctag+"colLab")
        dpg.add_input_text(default_value=tag,tag=loctag+"Lab",width=100)
        dpg.add_text("Start:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"Start",width=100)
        dpg.add_text("End:")
        dpg.add_input_text(hint="HH:MM:SS.mmm",default_value="00:00:00.000",tag=loctag+"End",width=100)
        dpg.add_button(label="Up",callback=lambda:dpg.move_item_up(loctag))
        dpg.add_button(label="Down",callback=lambda:dpg.move_item_down(loctag))
        dpg.add_button(label="Enabled",tag=(loctag+"Butt"), callback=outputToggle)
        dpg.add_button(label="Delete",tag=loctag+"Remove",callback=segDestroy)
    tag += 1

dpg.create_context()
dpg.create_viewport(title='Carbon', width=1000, height=600)
dpg.setup_dearpygui()

with dpg.file_dialog(label="Select a music file",tag="fileselect",file_count=1,height=400,width=600,modal=True,show=False,callback=fileSelect):
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[Music]")
    dpg.add_file_extension(".*",color=(255,0,0,255),custom_text="")

with dpg.window(label="Carbon",tag="main",no_close=True):
    dpg.add_button(label="File Select",callback=lambda: dpg.show_item("fileselect"))
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")
    dpg.add_button(label="Add Section",tag="secButtonAdd",callback=addSec,show=False)
    with dpg.group(tag="timing"):
        pass
    dpg.add_button(label="RUN!",tag="runButt",callback=runCut,show=False)
    dpg.add_text(tag="runStatus")

print(FD.calcTimecode(576.432))
dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
exit()