from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.popup import Popup
from kivymd.uix.card import MDCard
import concurrent.futures
import pathlib
import shutil
from kivymd.uix.button import MDFillRoundFlatIconButton
import tkinter as tk
from kivy.metrics import dp
from kivy.core.window import Window
from tkinter import filedialog
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock, mainthread
from kivymd.uix.tooltip.tooltip import MDTooltip
from kivymd.uix.toolbar import MDTopAppBar
from process.parsing import SourceParse, StatusPopup
from process.brex_verification import QueryParse, BrexStatus
from process.brex_validation import Brex, ValidationStatus
from process.mapper import MapResult
from kivymd.uix.snackbar import Snackbar
from process.download import GenerateReport
from kivymd_extensions.akivymd.uix.badgelayout import AKBadgeLayout
from generalfunctions.helper_classes import NameAndCode
from kivymd.uix.list import IconLeftWidget, TwoLineIconListItem


class ErrorTemplate(MDCard):
    pass


class FileBrowser(MDTopAppBar):
    pass


class StartProcess(MDTopAppBar):
    pass


class StartValidation(MDTopAppBar):
    pass


class StartMapping(MDTopAppBar):
    pass


class Download(MDTopAppBar):
    pass


class BottomBar(MDCard):
    pass


class IconBadge(AKBadgeLayout):
    pass


class HoverRound(MDFillRoundFlatIconButton, MDTooltip):
    pass


class InfoPopup(Popup):
    pass


class BrexPopup(MDBoxLayout):
    pass


class BrexList(MDCard):
    pass


class MappingStatus(MDDialog):
    def __init__(self, **kwargs):
        super(MappingStatus, self).__init__(**kwargs)


class MainRoot(MDBoxLayout):
    folderpath = []
    results = {}

    def __init__(self, **kwargs):
        super(MainRoot, self).__init__(**kwargs)
        filebrowser = FileBrowser()
        filebrowser.on_action_button = self.get_path
        self.ids.bottom_box.add_widget(filebrowser)
        self.info_popup = InfoPopup()
        Clock.schedule_once(self.check_for_brex, 1)

    def check_for_brex(self, dt):
        content = BrexPopup()
        brex_list = list(pathlib.Path('brex').glob("*MC*022A*.xml"))
        if brex_list == []:
            no_brex = TwoLineIconListItem(IconLeftWidget(
                icon='shield-alert'), text="NO BREX FOUND",
                secondary_text="please upload atlest a BREX module",
                bg_color="#FFA500", radius=10)
            content.ids.brex_list.add_widget(no_brex)
        else:
            self.ids.added_brex.text = f'{len(brex_list)}'
            if self.ids.added_brex.text == '0':
                self.ids.added_brex.text = ''
            for each in brex_list:
                subcontent = BrexList()
                subcontent.ids.brex_name.text = each.name
                content.ids.brex_list.add_widget(subcontent)
        self.open_brex_box(content)
        return content

    def open_brex_box(self, content):
        brex = MDDialog(title='BREX Manager', type='custom',
                        content_cls=content, auto_dismiss=False)
        content.no_brex = brex
        brex.open()
        return brex

    def browse_for_brex(self, dialog: MDDialog):
        root = tk.Tk()
        root.withdraw()
        file = filedialog.askopenfile(
            filetypes=[("S1000D BREX file", "*MC*022A*.xml")])
        if file != None:
            shutil.copy(pathlib.Path(file.name).as_posix(),
                        pathlib.Path(r'brex').as_posix())
            try:
                dialog.dismiss()
            except AttributeError:
                pass
            Clock.schedule_once(self.check_for_brex, 0)

    def remove_brex(self, brex_name, container: HoverRound):
        brex_path = pathlib.Path(r'brex')
        results = brex_path.glob(brex_name)
        [each.unlink() for each in results]
        # container.parent.remove_widget(container)
        container.text = 'Removed'
        container.md_bg_color = [1, 0, 0, 1]
        container.disabled = True
        container.tooltip_text = 'This BREX has been deleted'

    def get_path(self):
        del self.folderpath[:]
        root = tk.Tk()
        root.withdraw()
        self.folderpath.append(filedialog.askdirectory())
        self.start_parsing_source()

    def start_parsing_source(self):
        if (self.folderpath[0] != None) and (self.folderpath[0] != "") and (self.folderpath != []):
            dialog = StatusPopup()
            dialog.open()
            executor = concurrent.futures.ThreadPoolExecutor()
            executor.submit(self.parse_source, dialog)
            executor.submit(self.manage_widgets1)

    def parse_source(self, status: StatusPopup):
        parse_results = SourceParse(
            pathlib.Path(self.folderpath[0]), status)
        result, accuracy = parse_results.get_parse_status()
        if (result == 'Fail') and (accuracy < 1):
            self.add_info_wid(SourceParse.errors)
        status.dismiss()

    @mainthread
    def add_info_wid(self, bill: dict):
        for parse_exc in list(bill.keys()):
            error_temp = ErrorTemplate()
            error_temp.ids.info_title.text = parse_exc
            error_temp.ids.info_desc.text = bill[parse_exc]
            self.info_popup.ids.info_grid.add_widget(error_temp)
        try:
            self.ids.log_info.text = f"{int(self.ids.log_info.text) + len(list(bill.keys()))}"
        except ValueError:
            self.ids.log_info.text = f"{len(list(bill.keys()))}"

    @mainthread
    def manage_widgets1(self):
        startprocess = StartProcess()
        startprocess.on_action_button = self.start_parsing_brex
        self.ids.bottom_box.clear_widgets(self.ids.bottom_box.children)
        self.ids.bottom_box.add_widget(startprocess)
        # self.ids.bottom_box.add_widget(BottomBar())

    def start_parsing_brex(self):
        brexes = list(pathlib.Path(r"brex").glob("*MC*022A*.xml"))
        if brexes != []:
            dialog = BrexStatus()
            dialog.open()
            executor = concurrent.futures.ThreadPoolExecutor()
            executor.submit(self.parse_brex, brexes, dialog)
            executor.submit(self.manage_widgets2)
        else:
            MDDialog(title='No BREX found',
                     text='Atleast a BREX required, please upload before proceeding').open()

    @mainthread
    def manage_widgets2(self):
        startvalidation = StartValidation()
        startvalidation.on_action_button = self.start_validation
        self.ids.bottom_box.clear_widgets(self.ids.bottom_box.children)
        self.ids.bottom_box.add_widget(startvalidation)

    def parse_brex(self, brexpath: pathlib.Path, status: BrexStatus):
        parse_query = QueryParse(brexpath, status)
        result, accuracy = parse_query.get_parse_status()
        if (result == 'Fail') and (accuracy < 1):
            self.add_info_wid(parse_query.errors)
        parse_query.check_for_brex()
        if parse_query.warnings != {}:
            self.add_info_wid(parse_query.warnings)
        status.dismiss()

    def start_validation(self):
        if (self.ids.log_info.text == "0") or (self.ids.log_info.text == ""):
            dialog = ValidationStatus()
            dialog.open()
            executor = concurrent.futures.ThreadPoolExecutor()
            executor.submit(self.validate, dialog)
            executor.submit(self.manage_widgets3)
        else:
            MDDialog(title="Can't continue for validation",
                     text='Please check "Instructions" and make sure no wanings or errors present.').open()

    def validate(self, status: BrexStatus):
        for i, each in enumerate(list(QueryParse.roots.keys())):
            status.title = NameAndCode().only_name(each)
            final = {}
            brex_object = Brex(QueryParse.roots[each])
            for j, module in enumerate(list(SourceParse.roots.keys())):
                status_value = (
                    i+(j/len(list(SourceParse.roots.keys()))))/len(list(QueryParse.roots.keys()))
                status.ids.status_bar.value = status_value*100
                status.ids.status_value.text = f'{int(status_value*100)}%'
                status.ids.action_name.text = module
                validation_results = brex_object.validate(
                    SourceParse.roots[module])
                final.update({module: validation_results})
            self.results.update({each: final})
        status.dismiss()

    @mainthread
    def manage_widgets3(self):
        startmapping = StartMapping()
        startmapping.on_action_button = self.start_mapping
        self.ids.bottom_box.clear_widgets(self.ids.bottom_box.children)
        self.ids.bottom_box.add_widget(startmapping)

    @mainthread
    def start_mapping(self):
        self.ids.tabs_box.clear_widgets(self.ids.tabs_box.children)
        download_trigger = Download()
        self.ids.bottom_box.clear_widgets(self.ids.bottom_box.children)
        self.ids.bottom_box.add_widget(download_trigger)
        download_trigger.on_action_button = self.start_download
        executor = concurrent.futures.ThreadPoolExecutor()
        executor.submit(self.map_results)

    def start_download(self):
        executor = concurrent.futures.ThreadPoolExecutor()
        executor.submit(self.download)
        Snackbar(
            text="Downloading the validation report...",
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        ).open()

    @mainthread
    def download(self):
        GenerateReport(pathlib.Path(self.folderpath[0]), self.results)

    @mainthread
    def map_results(self):
        self.ids.tabs_box.add_widget(MapResult(self.results))

    def open_info_popup(self):
        if len(self.info_popup.ids.info_grid.children) != 0:
            self.info_popup.open()
        else:
            MDDialog(title=f'[color=FFA500]No Information[/color]',
                     text='The information block is empty, no information found!').open()
