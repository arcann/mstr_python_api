# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from pprint import pprint

import typing
from bs4 import BeautifulSoup
from typing import Optional, Tuple

from microstrategy_api.task_proc.attribute import Attribute
from microstrategy_api.task_proc.exceptions import MstrReportException
from microstrategy_api.task_proc.message import Message
from microstrategy_api.task_proc.metadata_object import MetadataObjectNonMemo
from microstrategy_api.task_proc.prompt import Prompt
from microstrategy_api.task_proc.status import Status

if typing.TYPE_CHECKING:
    import microstrategy_api


class ExecutableBase(MetadataObjectNonMemo):
    """
    Encapsulates an executable object in MicroStrategy

    Args:
        task_api_client):
            client to be used to make requests
        guid:
            object guid
        name:
            Optional. Name of the doc/report
    """

    def __init__(self, task_api_client: microstrategy_api.task_proc.task_proc.TaskProc, guid, name=None):
        super().__init__(guid, name)
        self.object_type = None
        self.obect_id_param = 'objectID'
        self.message_id_param = None
        self._task_api_client = task_api_client
        self.message_type = None
        self.exec_task = None
        self.refresh_cache_value = None
        self.refresh_cache_argument = None
        self._prompts = None
        self.prompt_args = {}

    @staticmethod
    def _get_tag_string(tag) -> Optional[str]:
        if tag is None:
            return None
        else:
            return tag.string

    @staticmethod
    def _format_element_prompts(prompts) -> dict:
        result = ''
        prompt_element_dict = dict()
        for prompt, values in prompts.items():
            if isinstance(prompt, Attribute):
                prompt_element_dict = prompts
                break

            if prompt is None:
                break

            if prompt.attribute in prompt_element_dict:
                # check for different answer
                if prompt_element_dict[prompt.attribute] != values:
                    pprint(prompts)
                    raise ValueError("Inconsistent prompt answers {} != {} see above for more details".format(
                        prompt_element_dict[prompt.attribute],
                        values
                        )
                    )
            else:
                prompt_element_dict[prompt.attribute] = values

        for attribute, values in prompt_element_dict.items():
            attribute_guid = attribute.guid
            if result:
                result += ","
            if values is not None:
                if isinstance(values, str):
                    values = [values]
                # Check for a zero length list which will be the same as valus = None
                if len(values) > 0:
                    prefix = ";" + attribute_guid + ":"
                    result += attribute_guid + ";" + attribute_guid + ":" + prefix.join(values)
                else:
                    result += attribute_guid + ';'
            else:
                result += attribute_guid + ';'
        return {'elementsPromptAnswers': result}

    @staticmethod
    def _format_value_prompts(prompts) -> dict:
        result = ''
        for i, (prompt, s) in enumerate(prompts):
            if i > 0:
                result += '^'
            if s:
                result += s
            elif not (s == '' and type(prompt) == Prompt):
                raise MstrReportException("Invalid syntax for value prompt " +
                                          "answers. Must pass (Prompt, string) tuples")
        return {'valuePromptAnswers': result}

    @staticmethod
    def _format_xml_prompts(v_prompts, e_prompts) -> dict:
        result = "<rsl>"
        for p, s in v_prompts:
            # Value prompt has pt=5
            result += "<pa pt='5' pin='0' did='{prompt_guid}' tp='10'>{value}</pa>".format(
                prompt_guid=p.guid,
                value=s,
            )
            # TODO: Support element prompt answers here so that we can have different answers for different attributes
            # Although I'm not sure how often that would be useful
            # Note: Put a text field with {&PROMPTXML} on any doc to see an examples of what this xml looks like
            # Element prompt has pt=7 and needs sub items
            """
            ##  Prompt type         Prompt guid
            <pa pt="7" pin="0" did="5C21F4D24F0312951BBE4A9DD2E6FF90" tp="10">
                <mi>
                    <es> 
                        ##       Attribute guid
                        <at did="7039371C4B5CC07DC6682D9C0EC8F45C" tp="12"/>
                        ##             element ID (attr:ID)
                        <e emt="1" ei="7039371C4B5CC07DC6682D9C0EC8F45C:HfVjCurKxh2" art="1" disp_n="Kenya"/>
                        ## Additional elements go as additional <e> tags right here
                    </es>
                </mi>
            </pa>
            """
        result += "</rsl>"
        d = ExecutableBase._format_element_prompts(e_prompts)
        d['promptsAnswerXML'] = result
        return d

    def execute_object(
            self,
            arguments: Optional[dict] = None,
            value_prompt_answers: Optional[list] = None,
            element_prompt_answers: Optional[dict] = None,
            refresh_cache: Optional[bool] = False,
            task_api_client: 'microstrategy_api.task_proc.task_proc.TaskProc' = None,
            ) -> BeautifulSoup:
        """
        Execute a report/document. Returns a bs4 document.

        Executes a report with the specified parameters. Default values
        are chosen so that most likely all rows and columns will be
        retrieved in one call. However, a client could use pagination
        by cycling through calls of execute and changing the min and max
        rows. Pagination is useful when there is a risk of the amount of
        data causing the MicroStrategy API to run out of memory. The report
        supports any combination of optional/required value prompt answers
        and element prompt answers.

        Arguments
        ---------
        arguments:
            Arguments to pass to exec routine
        value_prompt_answers:
            list of (Prompts, strings) in order. If a value is to be left blank, the second argument in the tuple
            should be the empty string
        element_prompt_answers:
            element prompt answers represented as a dictionary of Prompt objects (with attr field specified)
            mapping to a list of attribute values to pass
        refresh_cache:
            Rebuild the cache (Fresh execution)
        task_api_client:
            Alternative task_api_client to use when executing

        Raises
        ------
            MstrReportException: if there was an error executing the report.
        """
        if task_api_client:
            self._task_api_client = task_api_client

        if not arguments:
            arguments = dict()
        arguments['taskId'] = self.exec_task
        arguments[self.obect_id_param] = self.guid
        arguments['sessionState'] = self._task_api_client.session
        if value_prompt_answers and element_prompt_answers:
            arguments.update(
                ExecutableBase._format_xml_prompts(
                    value_prompt_answers,
                    element_prompt_answers)
                )
        elif value_prompt_answers:
            arguments.update(
                ExecutableBase._format_value_prompts(value_prompt_answers)
            )
        elif element_prompt_answers:
            arguments.update(
                ExecutableBase._format_element_prompts(element_prompt_answers)
            )
        if refresh_cache:
            arguments[self.refresh_cache_argument] = self.refresh_cache_value
        response = self._task_api_client.request(arguments)
        return response

    def execute_async(self,
                      arguments: Optional[dict] = None,
                      value_prompt_answers: Optional[list] = None,
                      element_prompt_answers: Optional[dict] = None,
                      refresh_cache: Optional[bool] = False,
                      max_wait_secs: Optional[int] = 1,
                      task_api_client: 'microstrategy_api.task_proc.task_proc.TaskProc' = None,
                      ) -> Message:
        """
        Execute a report/document without waiting. Returns a Message.

        Executes a report with the specified parameters. Default values
        are chosen so that most likely all rows and columns will be
        retrieved in one call. However, a client could use pagination
        by cycling through calls of execute and changing the min and max
        rows. Pagination is useful when there is a risk of the amount of
        data causing the MicroStrategy API to run out of memory. The report
        supports any combination of optional/required value prompt answers
        and element prompt answers.

        Arguments
        ---------
        arguments:
            Arguments to pass to exec routine
        value_prompt_answers:
            list of (Prompts, strings) in order. If a value is to be left blank, the second argument in the tuple
            should be the empty string
        element_prompt_answers:
            element prompt answers represented as a dictionary of Prompt objects (with attr field specified)
            mapping to a list of attribute values to pass
        refresh_cache:
            Rebuild the cache (Fresh execution)
        max_wait_secs:
            How long to wait for the report to finish (min 1 sec). Default 1 sec.
        task_api_client:
            Alternative task_api_client to use when executing

        Raises
        ------
            MstrReportException: if there was an error executing the report.
        """
        if arguments is None:
            arguments = dict()
        arguments['maxWait'] = max_wait_secs
        response = self.execute_object(
            arguments=arguments,
            value_prompt_answers=value_prompt_answers,
            element_prompt_answers=element_prompt_answers,
            refresh_cache=refresh_cache,
            task_api_client=task_api_client,
        )
        return Message(self._task_api_client, message_type=self.message_type, response=response)

    def get_prompts(self):
        """
        Returns the prompts associated with this report. If there are
        no prompts, this method runs the report anyway!

        Returns:
            list: a list of Prompt objects

        Raises:
            MstrReportException:
                if a msgID could not be retrieved likely implying there are no prompts for this report.
        """
        if self._prompts is None:
            # Start execution to be able to get prompts
            message = self.execute_async(arguments=self.prompt_args)

            while message.status not in [Status.Prompt, Status.Result]:
                self.log.debug("get_prompts status = {}".format(message.status))
                message.update_status(max_wait_ms=1000)
                if message.status == Status.ErrMsg:
                    raise MstrReportException(message.status_str)

            if message.status == Status.Result:
                return []
            else:
                arguments = {
                    'taskId':       'getPrompts',
                    'objectType':   self.object_type,
                    'msgID':        message.guid,
                    'sessionState': self._task_api_client.session
                }
                response = self._task_api_client.request(arguments, max_retries=3)

                # There are many ways that prompts can be returned. This api
                # currently supports a prompt that uses pre-created prompt objects.
                prompts = []
                prompt_dummy_answers = dict()
                for prompt_xml in response.prompts.contents:
                    if prompt_xml.name == 'block':
                        prompt_obj = Prompt(prompt_xml)
                        prompt_dummy_answers[prompt_obj.attribute] = ''
                        prompts.append(prompt_obj)
                self.execute_async(
                    arguments={self.message_id_param: message.guid},
                    element_prompt_answers=prompt_dummy_answers
                )
                self._prompts = prompts

        return self._prompts

    def get_prompted_attributes(self) -> set:
        attributes = set()
        prompts = self.get_prompts()
        for prompt in prompts:
            if prompt.attribute not in attributes:
                attributes.add(prompt.attribute)
        return attributes

    def execute(self,
                arguments: Optional[dict] = None,
                value_prompt_answers: Optional[list] = None,
                element_prompt_answers: Optional[dict] = None,
                refresh_cache: Optional[bool] = False,
                ):
        raise NotImplementedError()

    def get_url_api_parts(
            self,
            arguments: Optional[dict] = None,
            value_prompt_answers: Optional[list] = None,
            element_prompt_answers: Optional[dict] = None,
            refresh_cache: Optional[bool] = False,
            is_dossier: Optional[bool] = False,
    ) -> Tuple[str, dict]:
        raise NotImplementedError()

    def execute_url_api(self,
                        arguments: Optional[dict] = None,
                        value_prompt_answers: Optional[list] = None,
                        element_prompt_answers: Optional[dict] = None,
                        refresh_cache: Optional[bool] = False,
                        task_api_client: 'microstrategy_api.task_proc.task_proc.TaskProc' = None,
                        ) -> bytes:
        raise NotImplementedError()
