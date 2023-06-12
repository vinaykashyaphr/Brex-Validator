
import pathlib
from lxml import etree
from lxml.builder import E
from datetime import datetime
import os


class GenerateReport():

    def __init__(self, folderpath: pathlib.Path, results: dict) -> None:
        with open(pathlib.Path(r'static').joinpath(r'main.html').as_posix(), 'r', encoding='utf-8') as template:
            self.html_template = template.read()
        self.prepare_html(folderpath, results)

    def CLASS(self, *args):
        return {"class": ' '.join(args)}

    def generate_report(self, results: dict, brex: str, status: bool = True) -> etree._Element:
        if status == True:
            status = 'Pass'
        else:
            status = 'Fail'

        summary = E.div(
            E.div(self.CLASS("expand")),
            E.p(brex, self.CLASS("desc")),
            E.p(status, self.CLASS("status")),
            self.CLASS("summary", f'{str(status).lower()}'))

        report = E.div(summary, self.CLASS("check"))
        if (results != {}) and any(results.values()):
            summary[0].append(
                E.p("[+]", self.CLASS("active"), onclick="expand(this)"))
            details = E.div(self.CLASS("details"))
            for dmc, comments in results.items():
                if comments != []:
                    p = E.p(dmc, E.ul())
                    for r in comments:
                        p[0].append(E.li(r, onclick="check(this)"))
                    details.append(p)
            report.append(details)
        return report

    def prepare_html(self, folderpath: pathlib.Path, results: dict):
        out_file = f'{str(folderpath.name).upper()}-Validation_report.html'
        parsed_template = etree.fromstring(self.html_template)
        head = parsed_template.find("head")
        head.find(
            "title").text = f'{str(folderpath.name).upper()}: BREX Validation Report'

        body = parsed_template.find("body")
        body.find(
            "table/tr/td[@id='time']").text = datetime.now().strftime("%H:%M:%S")
        body.find(
            "table/tr/td[@id='date']").text = datetime.now().strftime("%B %d, %Y")
        body.find("table/tr/td[@id='user']").text = os.getlogin()
        body.find("table/tr/td[@id='job_no']").text = folderpath.name
        e_acc = body.find("table/tr/td[@id='accuracy']")
        e_stat = body.find("table/tr/td[@id='status']")

        overall_accuracy = []
        for brex in list(results.keys()):
            accuracy = len([results[brex][state] for state in list(
                results[brex].keys()) if results[brex][state] != []])
            overall_accuracy.append(
                1 - accuracy/len(list(results[brex].keys())))
            body.append(self.generate_report(
                results[brex], brex, not bool(accuracy)))

        general_accuracy = (sum(overall_accuracy)/len(overall_accuracy))*100
        e_acc.append(E.b(f'{int(general_accuracy)}%'))

        if general_accuracy < 100:
            e_stat.text = "Fail"
            e_acc.attrib['class'] = "fail"
        else:
            e_stat.text = "Pass"
            e_acc.attrib['class'] = "pass"

        with open(folderpath / out_file, 'w') as output:
            output.write(etree.tostring(parsed_template,
                         method='html').decode(encoding="utf-8"))
