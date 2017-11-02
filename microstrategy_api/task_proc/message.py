import logging

from bs4 import BeautifulSoup
from typing import Optional, Set

from microstrategy_api.task_proc.exceptions import MstrReportException, MstrClientException
from microstrategy_api.task_proc.status import StatusIDDict, Status


class MessageBase(object):
    def __init__(self,
                 status: Status=None,
                 status_str: str=None,
                 ):
        self.status = status
        self.status_str = status_str

    def __str__(self) -> str:
        s = "{self.status} status str={self.status_str}".format(self=self)
        return s


class Message(MessageBase):
    """
    pollEmmaStatus to get status from message ID
    msgID =
    resultSetType = 3 (rpt) or 55 (doc)
    <taskResponse statusCode="200">
    <msg><id>A6F0E868424B2077AD474AB05D31FD6F</id><st>-1</st><status>1</status></msg>
    </taskResponse>
    """

    def __init__(self,
                 task_api_client,
                 message_type: int,  # 3 for rpts or 55 for docs
                 guid: str=None,
                 st: str=None,
                 status: Status = None,
                 status_str: str=None,
                 response: BeautifulSoup=None):
        super().__init__(status=status,
                         status_str=status_str,
                         )
        self.message_type = message_type
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.task_api_client = task_api_client
        self.guid = guid
        # https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLStatus.html
        self.st = st
        if response:
            self.set_from_response(response)

    def __str__(self):
        s = super().__str__()
        s += "and st={self.st} for msg guid {self.guid}".format(self=self)
        return s

    def set_from_response(self, response):
        message = response.find('msg')
        if not message:
            self.log.error("Error retrieving msgID. Got {}".format(response))
            raise MstrReportException("Error retrieving msgID.")
        else:
            self.guid = message.find('id').string
            self.st = int(message.find('st').string)
            self.status_str = message.find('status').string

            try:
                status_int = int(self.status_str)
                if status_int in StatusIDDict:
                    self.status = StatusIDDict[status_int]
            except ValueError:
                pass

    def update_status(self, max_wait_ms: Optional[int]=None):
        arguments = {'taskId':    'pollEmmaStatus',
                     'msgID':     self.guid,
                     'resultSetType': self.message_type,
                     'sessionState': self.task_api_client.session,
                     }
        if max_wait_ms:
            arguments['maxWait'] = max_wait_ms
        try:
            response = self.task_api_client.request(arguments, max_retries=3)
            self.set_from_response(response)
        except MstrClientException as e:
            self.log.exception(e)
            self.status = Status.ErrMsg
            self.status_str = str(e)
