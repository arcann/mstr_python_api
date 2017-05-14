import urllib.parse

import functools
import requests
import logging

from bs4 import BeautifulSoup

"""
This API only supports xml format, as it relies on the format for parsing
the data into python data structures

Forked from https://github.com/infoscout/py-mstr

* Converted to support python 3
* Renamed from MstrClient to TaskProc
* Converted XML parsing from pyQuery to BeautifulSoup 4

Original license:

The MIT License (MIT)

Copyright (c) 2014 InfoScout

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

BASE_PARAMS = {'taskEnv': 'xml', 'taskContentType': 'xml'}
BASE_URL = 'http://hostname/MicroStrategy/asp/TaskProc.aspx?'


class TaskProc(object):
    """
    Class encapsulating base logic for the MicroStrategy Task Proc API
    """

    def __init__(self,
                 base_url,
                 username=None,
                 password=None,
                 project_source=None,
                 project_name=None,
                 session_state=None):
        """
        Initialize the MstrClient by logging in and retrieving a session.

        Args:
            base_url (str): base url of form http://hostname/MicroStrategy/asp/TaskProc.aspx?
            username (str): username for project
            password (str): password for project
            project_source (str): project source of form ip-####
            project_name (str): name of project
        """
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.log.setLevel(logging.DEBUG)
        self._base_url = base_url
        self.cookies = None
        self.trace = False
        if session_state is None:
            self._session = self.login(project_source, project_name, username, password)
        else:
            self._session = session_state

    def __str__(self):
        return 'MstrClient session: {}'.format(self._session)

    def login(self, project_source, project_name, username, password):
        arguments = {
            'taskId':   'login',
            'server':   project_source,
            'project':  project_name,
            'userid':   username,
            'password': password
        }
        self.log.info("logging in.")
        response = self._request(arguments)
        session_state = response.find('sessionState')
        return session_state.string

    @property
    def session(self):
        return self._session

    def get_report(self, report_id):
        """Returns a report object.

        Args:
            report_id (str): report guid for the report
        """
        return Report(self, report_id)

    def get_folder_contents(self, folder_id=None):
        """Returns a dictionary with folder name, GUID, and description.

        Args:
            folder_id (str): guid of folder to list contents. If not supplied,
                returns contents of root folder

        Returns:
            list: list of dictionaries with keys id, name, description, and type
                as keys
        """

        arguments = {'sessionState': self._session,
                     'taskID':       'folderBrowse'
                     }
        if folder_id:
            arguments.update({'folderID': folder_id})
        response = self._request(arguments)
        result = []
        for folder in response('folders'):
            for obj in folder('obj'):
                result.append({
                    'name':        obj.find('n').string,
                    'description': obj.find('d').string,
                    'id':          obj.find('id').string,
                    'type':        obj.find('t').string
                })
        return result

    def list_elements(self, attribute_id):
        """
        Returns the elements associated with the given attribute id.

        Note that if the call fails (i.e. MicroStrategy returns an
        out of memory stack trace) the returned list is empty

        Args:
            attribute_id (str): the attribute guid

        Returns:
            list: a list of strings containing the names for attribute values
        """

        arguments = {'taskId':       'browseElements', 'attributeID': attribute_id,
                     'sessionState': self._session}
        response = self._request(arguments)
        result = []
        for attr in response('block'):
            if attr.find('n').string:
                result.append(attr.find('n').string)
        return result

    def check_user_privileges(self, privilege_types="241"):
        arguments = {'taskId':         'checkUserPrivileges',
                     'privilegeTypes': privilege_types,
                     'sessionState':   self._session}
        response = self._request(arguments)
        priv_dict = dict()
        for privilege in response.find('privilege'):
            priv_dict[privilege['type']] = privilege['value']
        return priv_dict

    def get_attribute(self, attribute_id):
        """ 
        Returns the attribute object for the given attribute id.

        Args:
            attribute_id (str): the attribute guid

        Returns:
            Attribute: Attribute object for this guid

        Raises:
            MstrClientException: if no attribute id is supplied
        """

        if not attribute_id:
            raise MstrClientException("You must provide an attribute id")
        arguments = {'taskId':       'getAttributeForms',
                     'attributeID':  attribute_id,
                     'sessionState': self._session
                     }
        response = self._request(arguments)
        return Attribute(response.find('dssid').string, response.find('n').string)

    def logout(self):
        arguments = {
            'taskId':       'logout',
            'sessionState': self._session,
        }
        arguments.update(BASE_PARAMS)
        result = self._request(arguments)
        logging.info("logging out returned %s" % result)

    def _request(self, arguments: dict) -> BeautifulSoup:
        """
        Assembles the url and performs a get request to
        the MicroStrategy Task Service API

        Args:
            arguments (dict): Maps get key parameters to values

        Returns:
            str: the xml text response
        """

        arguments.update(BASE_PARAMS)
        if self.trace:
            self.log.debug("arguments {}".format(arguments))
        request = self._base_url + urllib.parse.urlencode(arguments)
        if self.trace:
            self.log.debug("submitting request {}".format(request))
        response = requests.get(request, cookies=self.cookies)
        if self.trace:
            self.log.debug("received response {}".format(response))
        if response.status_code != 200:
            raise MstrClientException(response.reason)
        doc = BeautifulSoup(response.text, 'xml')
        taskresponse = doc.find('taskResponse')
        if taskresponse['statusCode'] in ['400', '500']:
            raise MstrClientException(taskresponse['errorMsg'])
        self.cookies = response.cookies
        return doc


class MemoizeClass(type):
    """
    Memoize parent class to preserve memory.

    Objects are considered to be the same, and thus a new object
    does not need to be instantiated, if an object with given parameters.
    """

    @functools.lru_cache(maxsize=5000)
    def __call__(cls, *args, **kwargs):
        """Called when a new Singleton object is created.

        Singleton class checks to see if there is already a copy
        of the object in the class instances, and if so returns
        that object. Otherwise, it creates a new object of that
        subclass type.
        """
        return super(MemoizeClass, cls).__call__(*args, **kwargs)


class Attribute(object, metaclass=MemoizeClass):
    """ Object encapsulating an attribute on MicroStrategy

    An attribute can take many values, all of which are elements
    of that attribute. An attribute is defined by its name and
    its guid. Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this attribute
        name (str): the name of this attribute

    Attributes:
        guid (str): attribute guid
        name (str): attribute name
    """

    def __init__(self, guid, name):
        self.guid = guid
        self.name = name

    def __repr__(self):
        return "<Attribute name='{self.name}' guid='{self.guid}'".format(self=self)

    def __str__(self):
        return "[Attribute: {self.name}]".format(self=self)


class AttributeForm(object, metaclass=MemoizeClass):
    """ 
    Object encapsulating an attribute form on MicroStrategy

    Each attribute can have multiple forms (diffferent sets of source columns).
    Its __metaclass__ is Singleton.

    Args:
        guid (str): guid for this attribute
        name (str): the name of this attribute

    Attributes:
        attribute: An instance of Attribute
        name (str): attribute name
    """
    def __init__(self, attribute, form_guid, form_name):
        self.attribute = attribute
        self.form_guid = form_guid
        self.form_name = form_name

    def __repr__(self):
        return "{attr}@{form_name}".format(attr=repr(self.attribute), form_name=self.form_name)

    def __str__(self):
        return "{attr}@{form_name}".format(attr=str(self.attribute), form_name=self.form_name)


class Metric(object, metaclass=MemoizeClass):
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
        self.guid = guid
        self.name = name

    def __repr__(self):
        return "<Metric name='{self.name}' guid='{self.guid}'".format(self=self)

    def __str__(self):
        return "[Metric: {self.name}]".format(self=self)


class Prompt(object, metaclass=MemoizeClass):
    """ 
    Object encapsulating a prompt on MicroStrategy

    A prompt object has a guid and string and is or is not
    required. A prompt also potentially has an Attribute
    associated with it if it is an element prompt.

    Args:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt

    Attributes:
        guid (str): guid for the prompt
        prompt_str (str): string for the prompt that is displayed
            when the user uses the web interface
        required (bool): indicates whether or not the prompt is required
        attribute (Attribute): Attribute object associated with the
            prompt if it is an element prompt
    """

    def __init__(self, guid, prompt_str, required, attribute=None):
        self.guid = guid
        self.prompt_str = prompt_str
        self.attribute = attribute
        self.required = required

    def __repr__(self):
        return "<Prompt prompt_str='{self.prompt_str}' " \
               "attribute='{self.attribute}' required='{self.required}' guid='{self.guid}'"\
            .format(self=self)

    def __str__(self):
        return "[Prompt: {self.prompt_str} {self.attribute} ]".format(self=self)


class Value(object):
    def __init__(self, header, value):
        self.header = header
        self.value = value

    def __repr__(self):
        return '{self.header}={self.value}'.format(self=self)

    def __str__(self):
        return '{self.header}={self.value}'.format(self=self)


class Report(object):
    """
    Encapsulates a report in MicroStrategy

    The most common use case will be to execute a report.

    Args:
        mstr_client (TaskProc): client to be used to
            make requests
        report_id (str): report guid
    """

    def __init__(self, mstr_client, report_id):
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self._mstr_client = mstr_client
        self._id = report_id
        self._args = {'reportID': self._id, 'sessionState': mstr_client._session}
        self._attributes = []
        self._attribute_forms = []
        self._metrics = []
        self._headers = []
        self._values = None
        self._executed = False

    def __str__(self):
        return 'Report with id %s' % self._id

    def get_prompts(self):
        """ 
        Returns the prompts associated with this report. If there are
        no prompts, this method raises an error.

        Returns:
            list: a list of Prompt objects

        Raises:
            MstrReportException: if a msgID could not be retrieved
                likely implying there are no prompts for this report.
        """

        arguments = {'taskId': 'reportExecute'}
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        message = response.find('msg')
        message_id = message.find('id')
        if not message:
            self.log.error("failed retrieval of msgID in response %s" % response)
            raise MstrReportException("Error retrieving msgID for report. Most"
                                      + " likely the report does not have any prompts.")
            return
        arguments = {
            'taskId':       'getPrompts',
            'objectType':   '3',
            'msgID':        message_id.string,
            'sessionState': self._mstr_client._session
        }
        response = self._mstr_client._request(arguments)
        # There are many ways that prompts can be returned. This api
        # currently supports a prompt that uses pre-created prompt objects.
        prompts = []
        for prompt in response.find_all('prompts'):
            data = prompt.find('orgn')
            attr = None
            if data is not None:
                attr = Attribute(data.find('did').string,
                                 data.find('n').string)
            s = prompt.find('mn').string
            required = prompt.find('reqd').string
            guid = prompt.find('loc').find('did').string
            prompts.append(Prompt(guid, s, required, attribute=attr))

        return prompts

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
        arguments = {'taskId': 'browseAttributeForms', 'contentType': 3}
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
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
        arguments = {'taskId': 'browseAttributeForms', 'contentType': 3}
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        self._parse_attributes(response)
        return self._attributes

    def _parse_attributes(self, response):
        d = pq(response)
        self._attributes = []
        self._attribute_forms = []
        for attr_element in d('a'):
            attr = Attribute(attr_element.find('did').string, attr_element.find('n').string)
            self._attributes.append(attr)
            # Look for multiple attribute forms
            for form_element in attr_element.find('form'):
                attr_form = AttributeForm(attr, form_element.attr('id'), form_element('name'))
                self._attribute_forms.append(attr)

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
                start_row=0,
                start_col=0,
                max_rows=100000,
                max_cols=10,
                value_prompt_answers=None,
                element_prompt_answers=None):
        """
        Execute a report.

        Executes a report with the specified parameters. Default values
        are chosen so that most likely all rows and columns will be
        retrieved in one call. However, a client could use pagination
        by cycling through calls of execute and changing the min and max
        rows. Pagination is usefull when there is a risk of the amount of
        data causing the MicroStrategy API to run out of memory. The report
        supports any combination of optional/required value prompt answers
        and element prompt answers.

        Args:
            start_row (int): first row number to be returned
            start_col (int): first column number to be returned
            max_rows (int): maximum number of rows to return
            max_cols (int): maximum number of columns to return
            value_prompt_answers (list): list of (Prompts, strings) in order. If
                a value is to be left blank, the second argument in the tuple
                should be the empty string
            element_prompt_answers: (dict) element prompt answers represented as a
                dictionary of Prompt objects (with attr field specified)
                mapping to a list of attribute values to pass

        Raises:
            MstrReportException: if there was an error executing the report.
        """
        arguments = {
            'taskId':      'reportExecute',
            'startRow':    start_row,
            'startCol':    start_col,
            'maxRows':     max_rows,
            'maxCols':     max_cols,
            'styleName':   'ReportDataVisualizationXMLStyle',
            'resultFlags': '393216'  # prevent columns from merging
        }
        if value_prompt_answers and element_prompt_answers:
            arguments.update(self._format_xml_prompts(value_prompt_answers,
                                                      element_prompt_answers)
                            )
        elif value_prompt_answers:
            arguments.update(self._format_value_prompts(value_prompt_answers))
        elif element_prompt_answers:
            arguments.update(self._format_element_prompts(element_prompt_answers))
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        self._executed = True
        self._values = self._parse_report(response)

    def _format_xml_prompts(self, v_prompts, e_prompts):
        result = "<rsl>"
        for p, s in v_prompts:
            result = result + "<pa pt='5' pin='0' did='" + p.guid + \
                     "' tp='10'>" + s + "</pa>"
        result += "</rsl>"
        d = self._format_element_prompts(e_prompts)
        d['promptsAnswerXML'] = result
        return d

    def _format_value_prompts(self, prompts):
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

    def _format_element_prompts(self, prompts):
        result = ''
        for prompt, values in prompts.items():
            if result:
                result += ","
            if values:
                if isinstance(values, str):
                    values = [values]
                prefix = ";" + prompt.attribute.guid + ":"
                result = result + prompt.attribute.guid + ";" + prompt.attribute.guid + ":" + \
                         prefix.join(values)
            else:
                result += prompt.attribute.guid + ";"
        return {'elementsPromptAnswers': result}

    def _parse_report(self, response):
        if self._report_errors(response):
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
                row_values.append(Value(header= self._headers[index], value= val.string))
        return results

    def _report_errors(self, response: BeautifulSoup):
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

