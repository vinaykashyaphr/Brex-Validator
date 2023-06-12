from lxml import etree
import re
import elementpath
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock


class ValidationStatus(MDDialog):
    def __init__(self, **kwargs):
        super(ValidationStatus, self).__init__(**kwargs)
        self.maintain_pbar()

    def maintain_pbar(self):
        Clock.schedule_once(self.animate, 0)

    def animate(self, df):
        if self.ids.status_bar.value < 100:
            self.ids.status_bar._set_value(self.ids.status_bar.value)
        else:
            self.ids.status_bar._set_value(100)


class BrexContextRule():
    def __init__(self, rule):
        self.xml = rule
        self.id = rule.attrib.get('id', None)
        obj_path = rule.find('objectPath')
        self.allowed_object_flag = obj_path.attrib.get(
            'allowedObjectFlag', "0")

        try:
            use = rule.find('objectUse')
            if use is not None:
                self.use = "".join(rule.find('objectUse').itertext())
                if not self.use and (use := list(use)):
                    self.use = use[0].tail
            self.use = self.use.replace('\n', ' ')
        except AttributeError:
            self.use = ""
        self.path_text = re.sub(
            r'(match|test)\(', r're:\1(', obj_path.text or list(obj_path)[0].tail)
        self.value_allowed = {ov.get("valueAllowed"): ov.get("valueForm", "single")
                              for ov in rule.findall("objectValue") if ov.get("valueAllowed") is not None}

    def validate_rule(self, xml):

        try:
            result = xml.xpath(self.path_text, namespaces=xml.nsmap)
        except etree.XPathEvalError:
            result = elementpath.select(
                xml, self.path_text, namespaces=xml.nsmap)

        if (self.allowed_object_flag == "0" and result) or \
                (self.allowed_object_flag == "1" and not result):
            if self.allowed_object_flag == "0":
                return f"{self.use} | INSTANCES FOUND: {len(result)}"
            return self.use
        elif (self.allowed_object_flag == "2" and result):
            if not self.value_allowed:
                return ""
            result_list = []
            for value in result:
                if isinstance(value, etree._Element):
                    value = value.text or ""
                for k, v in self.value_allowed.items():
                    if v == "pattern":
                        try:
                            if (match := re.match(k, value)) is not None:
                                if match.group(0) == value:
                                    break
                        except TypeError as e:
                            raise Exception(
                                f"TypeError checking against rule '{self.use}'. k={k}, value={value}")
                    elif v == "single":
                        if k == value:
                            break
                    elif v == 'range':
                        ranges = list(map(int, re.findall(r'\d+', k)))
                        rangevals = [i for i in range(ranges[0], ranges[1])]
                        if list(map(int, re.findall(r'\d+', value)))[0] in rangevals:
                            break

                else:
                    allowed_value_types = set(self.value_allowed.values())
                    if len(allowed_value_types) > 1:
                        v = "allowed"

                    result_list.append(
                        f"{self.use} | VALUE: {value} | {v.upper()}: ({', '.join(list(self.value_allowed.keys()))})")
                    # return f"{self.use} | VALUE: {value} | {v.upper()}: ({', '.join(list(self.value_allowed.keys()))})"
            return result_list
        return ""


class BrexContextRuleGroup():

    def __init__(self, rules_xml):
        self.schema = rules_xml.attrib.get(
            'rulesContext', 'ALL').split('/')[-1]
        self._rules = BrexContextRuleGroup.get_rules(rules_xml)

    @staticmethod
    def get_rules(rule_group):
        return list(map(BrexContextRule, rule_group.findall("structureObjectRuleGroup/structureObjectRule")))

    def validate_rules(self, xml):
        output = []
        for rule in self._rules:
            result = rule.validate_rule(xml)
            if result:
                if isinstance(result, list):
                    output.extend(result)
                else:
                    output.append(result)
        return output


class Brex():
    def __init__(self, root: etree._Element):
        self._context_rules = Brex.parse_context_rules(
            root.findall('content/brex/contextRules'))

    @staticmethod
    def parse_context_rules(context_rules):
        if not context_rules:
            raise RuntimeWarning("No context rules found!")

        return [BrexContextRuleGroup(rg) for rg in context_rules]

    def validate(self, root: etree._Element):
        schema = root.attrib['{%s}noNamespaceSchemaLocation' %
                             root.nsmap["xsi"]].split('/')[-1]
        output = []
        for cr in self._context_rules:
            if cr.schema in {'ALL', schema}:
                output.extend(cr.validate_rules(root))
        return output
