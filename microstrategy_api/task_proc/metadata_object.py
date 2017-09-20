import logging

from task_proc.memoize_class import MemoizeClass


class MetadataObject(object, metaclass=MemoizeClass):
    """
    Object encapsulating a generic metadata object on MicroStrategy

    Args:
        guid (str): guid for this object
        name (str): the name of this object

    Attributes:
        guid (str): guid for this object
        name (str): the name of this object
    """

    def __init__(self, guid, name, metadata_object_type=None):
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.log.setLevel(logging.DEBUG)
        self.guid = guid
        self.name = name
        if metadata_object_type:
            self._type = metadata_object_type
        else:
            self._type = self.__class__.__name__

    def __repr__(self):
        return "<{self._type} name='{self.name}' guid='{self.guid}'".format(self=self)

    def __str__(self):
        if self.name:
            return "[{self._type}: {self.name}]".format(self=self)
        else:
            return self.__repr__()