from microstrategy_api.task_proc.metadata_object import MetadataObject


class Attribute(MetadataObject):
    """
    Object encapsulating an attribute on MicroStrategy

    An attribute can take many values, all of which are elements
    of that attribute. An attribute is defined by its name and
    its guid. Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this attribute
        name (str): the name of this attribute

    Attributes:
        guid (str): attribute guid
        name (str): attribute name
    """

    def __init__(self, guid, name):
        super().__init__(guid, name, 'Attribute')
