from typing import Optional, Tuple

import requests

import microstrategy_api
from microstrategy_api.task_proc.exceptions import MstrDocumentException
from microstrategy_api.task_proc.executable_base import ExecutableBase
from microstrategy_api.task_proc.object_type import ObjectType


class Document(ExecutableBase):
    """
    Encapsulates a document in MicroStrategy

    The most common use case will be to execute a document.

    Args:
        task_api_client:
            client to be used to make requests
        guid:
            document guid
        name:
            Optional. Name of the doc/report
    """

    def __init__(self, task_api_client, guid, name=None):
        super().__init__(task_api_client, guid, name)
        self.object_type = ObjectType.DocumentDefinition
        self.obect_id_param = 'objectID'
        self.message_type = 55
        self.exec_task = 'RWExecute'
        self.message_id_param = 'messageID'
        self.refresh_cache_argument = 'freshExec'
        self.refresh_cache_value = 'True'
        self.prompt_args = {}  # Haven't found any that prevent document execution if no prompts.

    def execute(self,
                arguments: Optional[dict] = None,
                value_prompt_answers: Optional[list] = None,
                element_prompt_answers: Optional[dict] = None,
                refresh_cache: Optional[bool] = False,
                task_api_client: 'microstrategy_api.task_proc.task_prod.TaskProc' = None,
                ):
        """
        Execute a report.

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
        value_prompt_answers:
            list of (Prompts, strings) in order. If a value is to be left blank, the second argument in the tuple
            should be the empty string
        element_prompt_answers:
            element prompt answers represented as a dictionary of Prompt objects (with attr field specified)
            mapping to a list of attribute values to pass
        refresh_cache:
            Do a new run against the data source?
        arguments:
            Other arbitrary arguments to pass to TaskProc.
        task_api_client:
            Alternative task_api_client to use when executing

        Raises
        ------
            MstrReportException: if there was an error executing the report.
        """
        if arguments is None:
            arguments = dict()

        # The style to use to transform the ReportBean. If omitted, a simple MessageResult is generated.
        # RWDocumentViewStyle
        if 'styleName' not in arguments:
            arguments['styleName'] = 'RWDataVisualizationXMLStyle'
        # prevent columns from merging
        arguments['gridsResultFlags'] = '393216'
        response = self.execute_object(
            arguments=arguments,
            value_prompt_answers=value_prompt_answers,
            element_prompt_answers=element_prompt_answers,
            refresh_cache=refresh_cache,
            task_api_client=task_api_client,
        )
        return response

    @staticmethod
    def get_redirect_url(response):
        found_title = False
        errors = []
        for line in response.iter_lines():
            if not found_title:
                if b'<title' in line:
                    found_title = True
                    if b'WELCOME. MicroStrategy' in line:
                        errors.append('Got welcome page!')
                    elif b'Login. MicroStrategy' in line:
                        errors.append('Got login page!')
                    elif b'Executing' not in line:
                        return None
            else:
                if b'mstrAlert' in line:
                    errors.append(line.decode('ascii'))
                else:
                    # HTML to scan for
                    pos1 = line.find(b'submitLinkAsForm({href:')
                    if pos1 != -1:
                        pos2 = line.find(b"'", pos1 + 1)
                        if pos2 != -1:
                            pos3 = line.find(b"'", pos2 + 1)
                            if pos3 != -1:
                                return line[pos2 + 1:pos3 + 1].decode('ascii', errors='replace')
        if errors:
            raise MstrDocumentException('\n'.join(errors))
        return 'ERROR'

    def get_url_api_parts(
            self,
            arguments: Optional[dict] = None,
            value_prompt_answers: Optional[list] = None,
            element_prompt_answers: Optional[dict] = None,
            refresh_cache: Optional[bool] = False,
            is_dossier: Optional[bool] = False,
            ) -> Tuple[str, dict]:
        """
        See https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/eventHandlerRef/web.app.beans.ServletWebComponent.html#2048001

        Parameters
        -----------
        arguments:
        value_prompt_answers:
        element_prompt_answers:
        refresh_cache:
        task_api_client:
        is_dossier:

        Returns
        -------
        The resulting html document
        """
        if not arguments:
            arguments = dict()

        if is_dossier:
            arguments['evt'] = '3140'
            arguments['src'] = 'Main.aspx.3140'
        else:
            arguments['evt'] = '2048001'
            arguments['src'] = 'Main.aspx.2048001'
            arguments['currentViewMedia'] = '1'
            arguments['visMode'] = '0'

        arguments['usrSmgr'] = self._task_api_client.session
        # arguments['uid'] = self._task_api_client.username
        # arguments['pwd'] = self._task_api_client.password
        arguments['documentID'] = self.guid
        arguments['server'] = self._task_api_client.server
        arguments['project'] = self._task_api_client.project_name
        arguments['Port'] = '0'
        arguments['connmode'] = '1'
        arguments['ru'] = '1'
        arguments['share'] = '1'
        arguments['promptAnswerMode'] = '1'  # 1 = default for un-answered. 2= empty for un-answered

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

        main_url = self._task_api_client.base_url.replace('TaskProc', 'Main')

        return main_url, arguments

    def execute_url_api(self,
                        arguments: Optional[dict] = None,
                        value_prompt_answers: Optional[list] = None,
                        element_prompt_answers: Optional[dict] = None,
                        refresh_cache: Optional[bool] = False,
                        task_api_client: 'microstrategy_api.task_proc.task_proc.TaskProc' = None,
                        is_dossier: Optional[bool] = False,
                        ) -> bytes:
        """
        See https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/eventHandlerRef/web.app.beans.ServletWebComponent.html#2048001

        Parameters
        -----------
        arguments:
        value_prompt_answers:
        element_prompt_answers:
        refresh_cache:
        task_api_client:

        Returns
        -------
        The resulting html document
        """
        if task_api_client:
            self._task_api_client = task_api_client

        main_url, arguments = self.get_url_api_parts(
            arguments=arguments,
            value_prompt_answers=value_prompt_answers,
            element_prompt_answers=element_prompt_answers,
            refresh_cache=refresh_cache,
            is_dossier=is_dossier,
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Locust) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
        }

        response = requests.get(main_url,
                                params=arguments,
                                headers=headers,
                                cookies=self._task_api_client.cookies
                                )
        response.raise_for_status()
        sub_url = Document.get_redirect_url(response)
        if sub_url is not None:
            base_url = self._task_api_client.base_url.replace('TaskProc.aspx', '')
            sub_params = {'usrSmgr': self._task_api_client.session}
            done = False
            while not done:
                if sub_url == 'ERROR':
                    raise MstrDocumentException("timedRedirect with no url found")
                else:
                    print("timedRedirect call")
                    sub_url = base_url + '/MicroStrategy/asp/' + sub_url
                    sub_response = requests.get(url=sub_url,
                                                params=sub_params,
                                                headers=headers,
                                                cookies=self._task_api_client.cookies
                                                )
                    sub_url = Document.get_redirect_url(sub_response)
                    if not sub_url:
                        done = True

        return response.content
