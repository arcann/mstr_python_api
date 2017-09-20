import logging
from typing import Optional

from task_proc.exceptions import MstrReportException, MstrClientException
from task_proc.status import StatusIDDict, Status


class Message(object):
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
                 status: str=None,
                 response: str=None):
        self.message_type = message_type
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.task_api_client = task_api_client
        self.guid = guid
        # https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLStatus.html
        self.status = status
        self.st = st
        if response:
            self.set_from_response(response)

    def __str__(self):
        return "{self.status} and st={self.st} for msg guid {self.guid}".format(self=self)

    def set_from_response(self, response):
        message = response.find('msg')
        if not message:
            self.log.error("Error retrieving msgID. Got {}".format(response))
            raise MstrReportException("Error retrieving msgID.")
        else:
            self.guid = message.find('id').string
            self.st = int(message.find('st').string)
            self.status = message.find('status').string

            try:
                self.status = int(self.status)
                if self.status in StatusIDDict:
                    self.status = StatusIDDict[self.status]
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
            self.status = Status.ErrMsg
