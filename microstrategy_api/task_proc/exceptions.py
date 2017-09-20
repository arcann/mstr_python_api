class MstrClientException(Exception):
    """
    Class used to raise errors in the MstrClient class
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class MstrReportException(Exception):
    """
    Class used to raise errors in the MstrReport class
    """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg