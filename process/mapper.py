from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.tab import MDTabs
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.stacklayout import MDStackLayout
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock, mainthread
import concurrent.futures
from kivy.metrics import dp
from kivymd.uix.list import IconLeftWidget, TwoLineIconListItem
from generalfunctions.helper_classes import NameAndCode


class Tab(MDScrollView, MDTabsBase):
    pass


class MainTab(MDTabsBase, MDBoxLayout):
    pass


class ContentLayout(MDStackLayout):
    pass


class Panel(MDBoxLayout):
    pass


class Content(MDBoxLayout):
    pass


class MappingStatus(MDDialog):
    def __init__(self, **kwargs):
        super(MappingStatus, self).__init__(**kwargs)
        self.maintain_pbar()

    def maintain_pbar(self):
        Clock.schedule_once(self.animate, 0)

    def animate(self, df):
        if self.ids.status_bar.value < 100:
            self.ids.status_bar._set_value(self.ids.status_bar.value)
        else:
            self.ids.status_bar._set_value(100)


class MapResult(MDTabs):
    def __init__(self, inlet: dict, **kwargs):
        super(MapResult, self).__init__(**kwargs)
        self.results = inlet
        self.launch_mapper()

    def launch_mapper(self):
        dialog = self.signal_definer('    Mapping the results...')
        dialog.open()
        executor = concurrent.futures.ThreadPoolExecutor()
        executor.submit(self.mapper, dialog)

    def signal_definer(self, label: str):
        dialog = MDDialog(
            title="Please wait..",
            size_hint=(None, None),
            width=dp(200),
            auto_dismiss=False,
            md_bg_color="#FFA500"
        )
        dialog.add_widget(MDLabel(text='\n'+label,
                                  theme_text_color='Custom',
                                  text_color=[1, 1, 1, 1],
                                  bold=True,
                                  halign='center'))
        return dialog

    @mainthread
    def mapper(self, status: MDDialog):
        if self.results != {}:
            for brex in list(self.results.keys()):
                brex_tab = MainTab(title=brex)
                container = MDTabs(background_color=[
                    0.95, 0.95, 0.95, 1], tab_hint_x=True)
                generic_tab = Tab(title='Generic Modules')
                local_tab = Tab(title='Local Modules')
                pub_tab = Tab(title='Publication Modules')
                generic_layout = ContentLayout()
                local_layout = ContentLayout()
                pub_layout = ContentLayout()
                for module in list(self.results[brex].keys()):
                    if ((str(module).startswith('DM')) and (
                            str(module).__contains__('HONAERO')) and (self.results[brex][module] != [])):
                        self.prepare_panel(brex, module, generic_layout)

                    elif ((str(module).startswith('DM')) and not (str(module).__contains__('HONAERO')) and (
                            str(module).__contains__('HON')) and (self.results[brex][module] != [])):
                        self.prepare_panel(brex, module, local_layout)

                    elif ((str(module).startswith('PMC-')) and (
                            str(module).__contains__('-HON')) and (self.results[brex][module] != [])):
                        self.prepare_panel(brex, module, pub_layout)

                generic_tab.add_widget(generic_layout)
                local_tab.add_widget(local_layout)
                pub_tab.add_widget(pub_layout)
                container.add_widget(generic_tab)
                container.add_widget(local_tab)
                container.add_widget(pub_tab)
                brex_tab.add_widget(container)
                self.add_widget(brex_tab)
        status.dismiss()

    def prepare_panel(self, brex, module, main_layout):
        main_table = Panel()

        for n, content in enumerate(self.results[brex][module]):
            main_content_holder = Content()
            label = MDLabel(text=f'{n+1}. '+content, adaptive_size=True)
            label.size_hint = (1, None)
            main_content_holder.add_widget(label)
            main_table.ids.beaker.add_widget(
                main_content_holder)

        main_panel = TwoLineIconListItem(
            IconLeftWidget(icon='file'),
            text=module, secondary_text=f'Total {len(self.results[brex][module])} validation error(s).'
        )
        panel = MDDialog(title=f'[color=FFA500]{NameAndCode().only_name(module)}[/color]',
                         type='custom', content_cls=main_table)
        main_layout.add_widget(main_panel)
        main_panel.on_release = panel.open
