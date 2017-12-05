from typing import Optional

from microstrategy_api.task_proc.attribute import Attribute
from microstrategy_api.task_proc.memoize_class import MemoizeClass


class Prompt(object, metaclass=MemoizeClass):
    """
    Object encapsulating a prompt on MicroStrategy

    A prompt object has a guid and string and is or is not
    required. A prompt also potentially has an Attribute
    associated with it if it is an element prompt.

    Args:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt

    Attributes:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt
    """

    def __init__(self, prompt_xml=None):
        self.guid = None
        self.title = None
        self.prompt_str = None
        self.attribute = None
        self.required = None
        self.ptp = None
        self.dptp = None
        self.pin = None
        self.ppin = None
        self.pt = None
        self.default_answers = list()
        if prompt_xml is not None:
            self.set_from_xml(prompt_xml)

    @staticmethod
    def _get_tag_string(tag) -> Optional[str]:
        if tag is None:
            return None
        else:
            return tag.string

    @staticmethod
    def _get_tag_int(tag) -> Optional[int]:
        if tag is None:
            return None
        else:
            try:
                return int(tag.string)
            except ValueError:
                return None

    def set_from_xml(self, xml):
        attr_elem = xml.find('orgn')
        if attr_elem is not None:
            self.attribute = Attribute(attr_elem.find('did').string,
                                       attr_elem.find('n').string
                                       )
            self.attribute.type = self._get_tag_int(attr_elem.find('t'))
            self.attribute.sub_type = self._get_tag_int(attr_elem.find('st'))
        self.title = self._get_tag_string(xml.find('ttl'))
        self.prompt_str = self._get_tag_string(xml.find('mn'))
        self.ptp = self._get_tag_string(xml.find('ptp'))
        self.dptp = self._get_tag_string(xml.find('dptp'))
        self.pin = self._get_tag_string(xml.find('pin'))

        required_str = self._get_tag_string(xml.find('reqd'))
        if required_str == 'true':
            self.required = True
        else:
            self.required = False
        loc = xml.find('loc')
        if loc:
            self.guid = self._get_tag_string(loc.find('did'))
            self.ppin = self._get_tag_string(loc.find('pin'))
            self.pt = self._get_tag_string(loc.find('t'))

        ans = xml.find('ans')
        if ans:
            for e in ans.find_all('e'):
                element = dict()
                if e.v:
                    _, element['ID'] = e.v.string.split(':')
                element['DESC'] = e.n.string
                element['t'] = e.t.string
                self.default_answers.append(element)

    def __repr__(self):
        return "<Prompt prompt_str='{self.prompt_str}' " \
               "attribute='{self.attribute}' required='{self.required}' guid='{self.guid}'"\
            .format(self=self)

    def __str__(self):
        return "[Prompt: {self.prompt_str} {self.attribute} ]".format(self=self)
