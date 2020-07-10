import sys
import queue
import json
import traceback
import monkey_dl
import PySimpleGUI as sg
from threading import Thread
from time import sleep
from util.downloader import Downloader
from util.Color import printer
from util.name_collector import EpisodeNamesCollector

sg.theme('Dark Amber')
i = 0
max_val = 100


def download(anime_url, names_url, start_epi, end_epi, is_filler, is_titles, token, threads, directory, gui,
             resolution="720", is_dub=False):
    global max_val

    #downloader = Downloader(directory, episodes, threads, gui, is_titles)
    downloader = Downloader(anime_url, names_url, start_epi, end_epi, is_filler, is_titles, token, threads, directory, gui, resolution, is_dub)

    max_val = downloader.get_episodes()

    downloader.download()


class AnimeGUI:

    def __init__(self, gui_queue):
        self.gui_queue = gui_queue
        self.window = None

    def create_ui(self):
        layout = [

            [sg.Text("General Details", size=(15, 1)), sg.Text("_" * 60, pad=(0, 15))],
            [sg.Text("Anime URL", text_color="white", size=(25, 1)), sg.InputText(key="anime_url")],
            [sg.Text("Animefillerlist URL", text_color="white", size=(25, 1)), sg.InputText(key="names_url")],
            [sg.Text("Save To", size=(25, 1), text_color="white"), sg.InputText(key="location"), sg.FolderBrowse()],

            [sg.Text("Episodes Details", size=(15, 1)), sg.Text("_" * 60, pad=(0, 15))],
            [sg.Text("From", text_color="white", size=(8, 1)), sg.InputText(key="start_epi", size=(6, 1)),
             sg.Text("To", text_color="white", size=(8, 1)), sg.InputText(key="end_epi", size=(5, 1)),
             sg.Text("Download Fillers?", text_color="white"),
             sg.Combo(["Yes", "No"], size=(4, 1), default_value="Yes", key="isFiller"),
             sg.Text("Threads", text_color="white"),
             sg.Spin([i for i in range(1, 21)], initial_value=1, size=(3, 1), key="threads")],
            [],
            [sg.Text("Resolution", text_color="white", size=(8, 1)),
             sg.Combo(["240", "360", "480", "720", "1080"], size=(4, 1), default_value="1080", key="resolution"),
             sg.Text("Sub/Dub", text_color="white", size=(8, 1)),
             sg.Combo(["Sub", "Dub"], size=(4, 1), default_value="Sub", key="is_dub")],
            [],
            [sg.Text("Optional Settings (Fill this if you don't have 2captcha key)", size=(45, 1)),
             sg.Text("_" * 25, pad=(0, 15))],
            [sg.Text("Recaptcha Token (Optional)", text_color="white", size=(25, 1)),
             sg.Multiline(size=(45, 4), key="token")],
            [sg.Column([[sg.Button("Download", size=(10, 1))]], justification="right", pad=(35, 5))],
            [],
            [sg.Text("Messages")],
            [sg.Multiline(size=(None, 8), key="txt_msg", disabled=True)],
            [],
            [sg.Text("Progress"), sg.Text("_" * 74, pad=(0, 15))],
            [sg.ProgressBar(100, key="progress", orientation="h", size=(45, 15))]
        ]

        if sys.platform.lower() == "win32":
            self.window = sg.Window("Monkey-DL v" + monkey_dl.__version__, layout, icon="app.ico")
        else:
            self.window = sg.Window("Monkey-DL v" + monkey_dl.__version__, layout, icon="app.png")

    def check_messages(self, values):
        global i, max_val
        txt = values["txt_msg"].strip()
        while True:
            try:  # see if something has been posted to Queue
                message = self.gui_queue.get_nowait()
            except queue.Empty:  # get_nowait() will get exception when Queue is empty
                break  # break from the loop if no more messages are queued up
            # if message received from queue, display the message in the Window
            if message:
                txt += "\n" + message

                if "finished downloading..." in message or "failed to download!" in message:
                    i += 1
                    self.window["progress"].UpdateBar(i, max=max_val)

                self.window['txt_msg'].update(txt)
                # do a refresh because could be showing multiple messages before next Read
                self.window.refresh()
                # print(message)

    def run(self):
        global i, max_val
        self.create_ui()

        while True:
            # wait for up to 100 ms for a GUI event
            event, values = self.window.read(timeout=100)
            if event in (None, 'Exit'):
                break

            # self.window["progress"].UpdateBar(i+1, max=100)
            # i+=1

            if event == "Download":
                anime_url = values["anime_url"]
                names_url = values["names_url"]
                is_titles = True if names_url != "" else False
                is_filler = True if values["isFiller"] == "Yes" else False
                is_dub = True if values["is_dub"] == "Dub" else False

                tok = values["token"].rstrip()
                token = tok if tok != "" else None

                directory = values["location"]
                threads = values["threads"]
                start_epi = int(values["start_epi"]) if values["start_epi"] != "" else 1
                end_epi = int(values["end_epi"]) if values["end_epi"] != "" else 9999
                resolution = str(values["resolution"])

                max_val = (end_epi - start_epi) + 1
                self.window["progress"].UpdateBar(i, max=max_val)

                if anime_url == "":
                    self.window['txt_msg'].update("[ERROR!] : Provide Anime URL!")
                    continue

                if directory != "":
                    directory = directory.replace("\\", "/")
                    if not directory.endswith("/"):
                        directory += "/"

                self.window["txt_msg"].update("")
                self.window.refresh()

                thread = Thread(target=download, args=(
                    anime_url, names_url, start_epi, end_epi, is_filler, is_titles, token, threads, directory, self,
                    resolution, is_dub), daemon=True)
                thread.start()

            self.check_messages(values)

        self.window.close()
