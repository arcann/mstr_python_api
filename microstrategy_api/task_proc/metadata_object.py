import logging

from microstrategy_api.task_proc.memoize_class import MemoizeClass
from microstrategy_api.task_proc.object_type import ObjectType, ObjectTypeIDDict, ObjectSubType, ObjectSubTypeIDDict


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
        self._type = None
        self._sub_type = None
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
    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value is None:
            self._type = value
        elif isinstance(value, ObjectType):
            self._type = value
        elif isinstance(value, int):
            self._type = ObjectTypeIDDict[value]
        elif isinstance(value, str):
            self._type = ObjectType[value]
        else:
            raise ValueError("{v} is not ObjectType, int, or str".format(v=value))

    @property
    def sub_type(self):
        return self._sub_type

    @sub_type.setter
    def sub_type(self, value):
        if value is None:
            self._sub_type = value
        elif isinstance(value, ObjectSubType):
            self._sub_type = value
        elif isinstance(value, int):
            self._sub_type = ObjectSubTypeIDDict[value]
        elif isinstance(value, str):
            self._sub_type = ObjectSubType[value]
        else:
            raise ValueError("{v} is not ObjectSubType, int, or str".format(v=value))



