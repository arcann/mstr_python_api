class MstrClientException(Exception):
    """
    Class used to raise errors in the MstrClient class
    """

    def __init__(self, msg, request=None):
        self.msg = msg
        self.request = request

    def __str__(self):
        return str(self.msg)

    def __repr__(self):
        return "{cls}(msg={msg}, request={request}".format(
            cls=self.__class__,
            msg=self.msg,
            request=self.request
        )


class MstrReportException(MstrClientException):
    """
    Class used to raise errors in the MstrReport class
    """
    pass


class MstrDocumentException(MstrClientException):
    """
    Class used to raise errors in the Document class
    """
    pass