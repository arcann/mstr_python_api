from task_proc.memoize_class import MemoizeClass


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

    def __init__(self, guid, prompt_str, required, attribute=None):
        self.guid = guid
        self.prompt_str = prompt_str
        self.attribute = attribute
        self.required = required

    def __repr__(self):
        return "<Prompt prompt_str='{self.prompt_str}' " \
               "attribute='{self.attribute}' required='{self.required}' guid='{self.guid}'"\
            .format(self=self)

    def __str__(self):
        return "[Prompt: {self.prompt_str} {self.attribute} ]".format(self=self)
