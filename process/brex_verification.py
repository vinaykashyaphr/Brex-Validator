from process.parsing import Module, SourceParse
from traceback import format_exc
from generalfunctions.helper_classes import NameAndCode
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from time import sleep


class BrexStatus(MDDialog):
    def __init__(self, **kwargs):
        super(BrexStatus, self).__init__(**kwargs)
        self.maintain_pbar()

    def maintain_pbar(self):
        Clock.schedule_once(self.animate, 0)

    def animate(self, df):
        if self.ids.status_bar.value < 100:
            self.ids.status_bar._set_value(self.ids.status_bar.value)
        else:
            self.ids.status_bar._set_value(100)


class QueryParse():
    errors, roots, warnings = {}, {}, {}

    def __init__(self, brexes: list, status: BrexStatus):
        for i, module in enumerate(brexes):
            progress_value = (i/len(brexes))*100
            status.ids.action_name.text = module.name
            status.ids.status_value.text = f"{int(progress_value)}%"
            status.ids.status_bar.value = progress_value
            Clock.schedule_once(status.animate, 0)
            sleep(1)
            try:
                module_root = Module(module).root
            except Exception as e_:
                self.errors.update({module.name: format_exc()})
            else:
                self.roots.update({module.name: module_root})
        status.ids.status_value.text = "100%"
        status.ids.status_bar.value = 100
        Clock.schedule_once(status.animate, 0)
        sleep(1)

    def get_parse_status(self):
        if (self.errors == {}) and (self.roots != {}):
            return "Pass", 1
        elif (self.errors != {}) and (self.roots == {}):
            return 'Fail', 0
        else:
            accuracy = 1 - (len(list(self.errors.keys())) /
                            (len(list(self.errors.keys()))+len(list(self.roots.keys()))))
            return 'Fail', accuracy

    def check_for_brex(self):
        regestered_brexes = [NameAndCode().only_name(file)
                             for file in self.roots.keys()]
        if SourceParse.roots != {}:
            for each in SourceParse.roots:
                module_brexes = SourceParse.roots[each].xpath(
                    './/brexDmRef//dmCode')
                for brex in module_brexes:
                    brex_name = NameAndCode().name_from_dmcode(brex.attrib)
                    if brex_name not in regestered_brexes:
                        self.warnings.update(
                            {each: f'{brex_name}:: This BREX was not found in the uploads.'})
