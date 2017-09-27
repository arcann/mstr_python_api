from typing import Optional

from microstrategy_api.task_proc.executable_base import ExecutableBase
from microstrategy_api.task_proc.object_type import ObjectType
from microstrategy_api.task_proc.task_proc import TaskProc


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

    def execute(self,
                arguments: Optional[dict] = None,
                value_prompt_answers: Optional[list] = None,
                element_prompt_answers: Optional[dict] = None,
                refresh_cache: Optional[bool] = False,
                task_api_client: TaskProc = None,
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
