from task_proc.metadata_object import MetadataObject


class AttributeForm(MetadataObject):
    """
    Object encapsulating an attribute form on MicroStrategy

    Each attribute can have multiple forms (different sets of source columns).
    Its __metaclass__ is Singleton.

    Args:
        attribute:
            An instance of Attribute
        guid:
            guid for this attrib
        attribute: ute form
        name:
            the name of this attribute form

    Attributes:
            An instance of Attribute
        guid:
            GUID for the form
        name:
            Name of the form
    """
    def __init__(self, attribute, guid, name):
        super().__init__(guid, name, 'AttributeForm')
        self.attribute = attribute

    def __repr__(self):
        return "{attr}@{form_name}".format(attr=repr(self.attribute), form_name=self.name)

    def __str__(self):
        return "{attr}@{form_name}".format(attr=str(self.attribute), form_name=self.name)