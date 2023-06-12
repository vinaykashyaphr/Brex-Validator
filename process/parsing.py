import re
import pathlib
from lxml import etree
from traceback import format_exc
from generalfunctions.helper_classes import validate_entities
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock


class StatusPopup(MDDialog):
    def __init__(self, **kwargs):
        super(StatusPopup, self).__init__(**kwargs)
        self.maintain_pbar()

    def maintain_pbar(self):
        Clock.schedule_once(self.animate, 0)

    def animate(self, df):
        if self.ids.status_bar.value < 100:
            self.ids.status_bar._set_value(self.ids.status_bar.value)
        else:
            self.ids.status_bar._set_value(100)


class Module():

    def __init__(self, module: pathlib.Path):
        self.get_modules(module, etree.XMLParser(
            resolve_entities=False, recover=True))

    def pre_fixes(self, module: pathlib.Path, encoding: str = "utf-8"):
        validate_entities(module)
        text = module.read_text(encoding=encoding)
        module.write_text(re.sub(r'ns\#(\s+)', 'ns#',
                          text, 1), encoding=encoding)

    def get_modules(self, module: pathlib.Path, par: etree.XMLParser):
        self.pre_fixes(module)
        self.root = etree.parse(module.as_posix(), par).getroot()

    def __repr__(self) -> str:
        return f"<Module object '{self.root}'>"


class SourceParse():
    errors, roots = {}, {}

    def __init__(self, folderpath: pathlib.Path, status: StatusPopup):
        sources = list(folderpath.glob('*M[CE]-*.xml'))
        for i, module in enumerate(sources):
            progress_value = (i/len(sources))*100
            status.ids.action_name.text = module.name
            status.ids.status_value.text = f"{int(progress_value)}%"
            status.ids.status_bar.value = progress_value
            Clock.schedule_once(status.animate, 0)
            try:
                module_root = Module(module).root
            except Exception as e_:
                self.errors.update({module.name: format_exc()})
            else:
                self.roots.update({module.name: module_root})
        status.ids.status_value.text = "100%"
        status.ids.status_bar.value = 100
        Clock.schedule_once(status.animate, 0)

    def get_parse_status(self):
        if (self.errors == {}) and (self.roots != {}):
            return "Pass", 1
        elif (self.errors != {}) and (self.roots == {}):
            return 'Fail', 0
        else:
            accuracy = 1 - (len(list(self.errors.keys())) / \
                (len(list(self.errors.keys()))+len(list(self.roots.keys()))))
            return 'Fail', accuracy