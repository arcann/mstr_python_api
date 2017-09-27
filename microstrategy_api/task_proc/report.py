from bs4 import BeautifulSoup
from typing import Optional

from microstrategy_api.task_proc.attribute import Attribute
from microstrategy_api.task_proc.attribute_form import AttributeForm
from microstrategy_api.task_proc.exceptions import MstrReportException
from microstrategy_api.task_proc.executable_base import ExecutableBase
from microstrategy_api.task_proc.metric import Metric
from microstrategy_api.task_proc.object_type import ObjectType
from microstrategy_api.task_proc.task_proc import TaskProc


class Value(object):
    def __init__(self, header, value):
        self.header = header
        self.value = value

    def __repr__(self):
        return '{self.header}={self.value}'.format(self=self)

    def __str__(self):
        return '{self.header}={self.value}'.format(self=self)


class Report(ExecutableBase):
    """
    Encapsulates a report in MicroStrategy

    The most common use case will be to execute a report.

    Args:
        task_api_client (TaskProc): client to be used to
            make requests
        guid (str): report guid
    """

    def __init__(self, task_api_client, guid, name=None):
        super().__init__(task_api_client, guid, name)
        self._attributes = []
        self._attribute_forms = []
        self._metrics = []
        self._headers = []
        self._values = None
        self._executed = False
        self.object_type = ObjectType.ReportDefinition
        self.obect_id_param = 'reportID'
        self.message_id_param = 'msgID'
        self.message_type = 3
        self.exec_task = 'reportExecute'
        self.refresh_cache_argument = 'execFlags'
        self.refresh_cache_value = str(1 | 256)  # DssXmlExecutionFresh & DssXmlExecutionUpdateCache
        self.max_wait = 500

    def get_headers(self):
        """
        Returns the column headers for the report. A report must have
        been executed before calling this method

        Returns:
            list: a list of Attribute/Metric objects
        """

        if self._executed:
            return self._headers
        else:
            self.log.error("Attempted to retrieve the headers for a report without" +
                           " prior successful execution.")
            raise MstrReportException("Execute a report before viewing the headers")

    def get_attributes(self):
        """
        Returns the attribute objects for the columns of this report.

        If a report has not been executed, there exists an api call
        to retrieve just the attribute objects in a Report.

        Returns:
            list: list of Attribute objects
        """
        if self._attributes:
            self.log.info("Attributes have already been retrieved. Returning " +
                          "saved objects.")
            return self._attributes
        arguments = {'taskId':       'browseAttributeForms',
                     'contentType':  3,
                     'reportID':     self.guid,
                     'sessionState': self._task_api_client.session,
                     }
        response = self._task_api_client.request(arguments)
        self._parse_attributes(response)
        return self._attributes

    def get_attribute_forms(self):
        """
        Returns the AttributeForm objects for the columns of this report.

        If a report has not been executed, there exists an api call
        to retrieve just the attribute objects in a Report.

        Returns:
            list: list of AttributeForm objects
        """
        if self._attribute_forms:
            self.log.info("AttributesForms have already been retrieved. Returning " +
                          "saved objects.")
            return self._attribute_forms
        arguments = {'taskId':       'browseAttributeForms',
                     'contentType':  3,  # See EnumDSSXMLAxesBitMap
                     'reportID':     self.guid,
                     'sessionState': self._task_api_client.session,
                     }
        response = self._task_api_client.request(arguments)
        self._parse_attributes(response)
        return self._attributes

    def _parse_attributes(self, response):
        self._attributes = []
        self._attribute_forms = []
        for attr_element in response('a'):
            attr = Attribute(attr_element.find('did').string, attr_element.find('n').string)
            self._attributes.append(attr)
            # Look for multiple attribute forms
            forms_elements = attr_element.find('fms')
            if forms_elements:
                for form_element in forms_elements:
                    attr_form = AttributeForm(attr,
                                              form_element.find('did').string,
                                              form_element.find('n').string)
                    self._attribute_forms.append(attr_form)

    def get_values(self):
        """
        Returns the rows for a prompt that has been executed.

        A report must have been executed for this method to run.

        Returns:
            list: list of lists containing tuples of the (Attribute/Metric, value)
            pair, where the Attribute/Metric is the object for the column header,
            and the value is that cell's value

        Raises:
            MstrReportException: if execute has not been called on this report
        """
        if self._values is not None:
            return self._values
        raise MstrReportException("Execute a report before viewing the rows")

    def get_metrics(self):
        """
        Returns the metric objects for the columns of this report.

        A report must have already been executed for this method to run.

        Returns:
            list: list of Metric objects

        Raises:
            MstrReportException: if execute has not been called on this report
        """
        if self._executed:
            return self._metrics
        else:
            self.log.error("Attempted to retrieve the metrics for a report without" +
                           " prior successful execution.")
            raise MstrReportException("Execute a report before viewing the metrics")

    def execute(self,
                start_row: int = 0,
                start_col: int = 0,
                max_rows: int = 100000,
                max_cols: int = 10,
                refresh_cache: Optional[bool] = False,
                value_prompt_answers: Optional[list] = None,
                element_prompt_answers: Optional[dict] = None,
                arguments: Optional[dict] = None,
                task_api_client: TaskProc = None,
                ):
        """
        Execute a report and returns results.

        Executes a report with the specified parameters. Default values
        are chosen so that most likely all rows and columns will be
        retrieved in one call. However, a client could use pagination
        by cycling through calls of execute and changing the start_row.
        Pagination is useful when there is a risk of the amount of
        data causing the MicroStrategy API to run out of memory. The report
        supports any combination of optional/required value prompt answers
        and element prompt answers.

        Arguments
        ---------
        start_row:
            first row number to be returned
        start_col:
            first column number to be returned
        max_rows:
            maximum number of rows to return
        max_cols:
            maximum number of columns to return
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
        arguments.update({
            'startRow':     start_row,
            'startCol':     start_col,
            'maxRows':      max_rows,
            'maxCols':      max_cols,
            # The style to use to transform the ReportBean. If omitted, a simple MessageResult is generated.
            'styleName':    'ReportDataVisualizationXMLStyle',
            'resultFlags':  '393216',  # prevent columns from merging
        })
        response = self.execute_object(
            value_prompt_answers=value_prompt_answers,
            element_prompt_answers=element_prompt_answers,
            refresh_cache=refresh_cache,
            arguments=arguments,
            task_api_client=task_api_client,
        )
        self._executed = True
        self._values = self._parse_report(response)

    def _parse_report(self, response):
        if Report._report_errors(response):
            return None
        if not self._headers:
            self._get_headers(response)
        # iterate through the columns while iterating through the rows
        # and create a list of tuples with the attribute and value for that
        # column for each row

        results = list()
        for row in response('r'):
            row_values = list()
            results.append(row_values)
            for index, val in enumerate(row.children):
                row_values.append(Value(header=self._headers[index], value=val.string))
        return results

    @staticmethod
    def _report_errors(response: BeautifulSoup):
        """
        Performs error checking on the result from the execute call.

        Specifically, this method is looking for the <error> tag
        returned by MicroStrategy.

        Args:
            response

        Returns:
            bool: indicates whether or not there was an error.
            If there was an error, an exception should be raised.

        Raises:
            MstrReportException: if there was an error executing
            the report.
        """
        error = response('error')
        if error:
            raise MstrReportException("There was an error running the report." +
                                      "Microstrategy error message: " + error[0].string)
        return False

    def _get_headers(self, doc):
        objects = doc.find('objects')
        headers = doc.find('headers')
        self._attribute_forms = []
        self._attributes = []
        self._metrics = []
        for col in headers.children:
            elem = objects.find(['attribute', 'metric'], attrs={'rfd': col['rfd']})
            if elem.name == 'attribute':
                attr = Attribute(elem['id'], elem['name'])
                self._attributes.append(attr)
                # Look for multiple attribute forms
                for form_element in elem('form'):
                    attr_form = AttributeForm(attr, form_element['id'], form_element['name'])
                    self._attribute_forms.append(attr_form)
                    self._headers.append(attr_form)
            else:
                metric = Metric(elem['id'], elem['name'])
                self._metrics.append(metric)
                self._headers.append(metric)
