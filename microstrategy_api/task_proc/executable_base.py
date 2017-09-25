from bs4 import BeautifulSoup
from typing import Optional

from task_proc.task_proc import TaskProc
from task_proc.attribute import Attribute
from task_proc.exceptions import MstrReportException
from task_proc.message import Message
from task_proc.metadata_object import MetadataObject
from task_proc.prompt import Prompt
from task_proc.status import Status


class ExecutableBase(MetadataObject):
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

    def __init__(self, task_api_client: TaskProc, guid, name=None):
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

    @staticmethod
    def _get_tag_string(tag) -> Optional[str]:
        if tag is None:
            return None
        else:
            return tag.string

    @staticmethod
    def _format_element_prompts(prompts) -> dict:
        result = ''
        for prompt, values in prompts.items():
            if result:
                result += ","
            if values is not None:
                if isinstance(values, str):
                    values = [values]
                prefix = ";" + prompt.attribute.guid + ":"
                result += prompt.attribute.guid + ";" + prompt.attribute.guid + ":" + prefix.join(values)
            else:
                result += prompt.attribute.guid + ';'
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
            result = result + "<pa pt='5' pin='0' did='" + p.guid + \
                     "' tp='10'>" + s + "</pa>"
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
            task_api_client: TaskProc=None,
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
                      task_api_client: TaskProc = None,
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
        no prompts, this method raises an error.

        Returns:
            list: a list of Prompt objects

        Raises:
            MstrReportException:
                if a msgID could not be retrieved likely implying there are no prompts for this report.
        """
        if self._prompts is None:
            # Start execution to be able to get prompts
            message = self.execute_async()

            while message.status not in [Status.Prompt, Status.Result]:
                self.log.debug("get_prompts status = {}".format(message.status))
                message.update_status(max_wait_ms=1000)

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
                for prompt in response.prompts.contents:
                    if prompt.name == 'block':
                        attr_elem = prompt.find('orgn')
                        attr = None
                        if attr_elem is not None:
                            attr = Attribute(attr_elem.find('did').string,
                                             attr_elem.find('n').string)
                        name = ExecutableBase._get_tag_string(prompt.find('mn'))
                        required = ExecutableBase._get_tag_string(prompt.find('reqd'))
                        if required == 'true':
                            required = True
                        else:
                            required = False
                        loc = prompt.find('loc')
                        guid = None
                        if loc:
                            guid = ExecutableBase._get_tag_string(loc.find('did'))
                        prompt = Prompt(guid, name, required, attribute=attr)
                        prompt_dummy_answers[prompt] = []
                        prompts.append(prompt)
                self.execute_async(
                    arguments={self.message_id_param: message.guid},
                    element_prompt_answers=prompt_dummy_answers
                )
                self._prompts = prompts

        return self._prompts

    def execute(self,
                arguments: Optional[dict] = None,
                value_prompt_answers: Optional[list] = None,
                element_prompt_answers: Optional[dict] = None,
                refresh_cache: Optional[bool] = False,
                ):
        raise NotImplementedError
