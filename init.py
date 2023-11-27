import os, sys
import dearpygui.dearpygui as dpg
from mutagen.mp3 import MP3
from datetime import timedelta

currentFile = ""
currentFilePath = ""
filelengthS = 0
filelengthMS = 0

class FD:
    file = ""
    filePath = ""
    filelengthS = -1
    timecodeLength = ""

    def calcTimecode(lenS: float) -> str:
        return str(timedelta(seconds=lenS)).split("000")[0]

def callback(sender, app_data):
    print("App Data: ", app_data)
    # Forgive me father for I have sinned
    FD.file = str(app_data["selections"].keys()).split("['")[1].split("']")[0]
    FD.filePath = str(app_data["selections"].values()).split("['")[1].split("']")[0]
    audio = MP3(FD.filePath)
    FD.filelengthS = audio.info.length
    FD.timecodeLength = FD.calcTimecode(FD.filelengthS)
    dpg.set_value("stat", "Currently loaded file: " + FD.file)
    dpg.set_value('filelen',"File length: " + FD.timecodeLength + " (" + str(FD.filelengthS)+")")

dpg.create_context()
dpg.create_viewport(title='Carbon', width=700, height=600)
dpg.setup_dearpygui()

with dpg.file_dialog(label="Select a music file",tag="fileselect",file_count=1,height=300,width=500,modal=True,show=False,callback=callback):
    dpg.add_file_extension(".mp3",color=(0,255,0,255),custom_text="[Music]")
    dpg.add_file_extension(".*",color=(255,0,0,255),custom_text="")

with dpg.window(label="Carbon",tag="main",no_close=True):
    dpg.add_button(label="File Select",callback=lambda: dpg.show_item("fileselect"))
    dpg.add_text("No File Loaded", tag="stat")
    dpg.add_text(tag="filelen")

print(FD.calcTimecode(576.432))
dpg.set_primary_window("main",True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
exit()