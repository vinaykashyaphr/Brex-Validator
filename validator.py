from kivy.config import Config
import pyautogui
from kivy.core.window import Window
width, height = pyautogui.size()
Window.maximize()
Config.set('graphics', 'borderless', 0)
Config.set('graphics', 'width', str(width))
Config.set('graphics', 'height', str(height))

Window.borderless = False
import pathlib
import os
import sys
from kivymd.app import MDApp
from kivy.lang import Builder
from functions.main import MainRoot

cwd = pathlib.Path.cwd()
Builder.load_file(r"design.kv")


class BVI(MDApp):
    index = 0

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Orange"
        self.title = 'Honeywell BREX Validator - V1.0 (Mar 2023)'
        return MainRoot()

    @staticmethod
    def restart():
        os.execvp(sys.executable, ['python'] + sys.argv)


def reset():
    import kivy.core.window as window
    from kivy.base import EventLoop
    if not EventLoop.event_listeners:
        from kivy.cache import Cache
        window.Window = window.core_select_lib(
            'window', window.window_impl, True)
        Cache.print_usage()
        for cat in Cache._categories:
            Cache._objects[cat] = {}


if __name__ == "__main__":
    reset()
    BVI().run()