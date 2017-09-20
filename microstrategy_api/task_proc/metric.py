from task_proc.metadata_object import MetadataObject


class Metric(MetadataObject):
    """
    Object encapsulating a metric on MicroStrategy

    A metric represents computation on attributes. A metric
    is defined by its name and its guid. Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this metric
        name (str): the name of this metric

    Attributes:
        guid (str): guid for this metric
        name (str): the name of this metric
    """

    def __init__(self, guid, name):
        super().__init__(guid, name)
