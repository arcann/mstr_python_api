import re
import urllib.parse

import functools
from enum import Enum

from typing import Optional

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

    class SystemFolders(Enum):
        PublicObjects = 1
        Consolidations = 2
        CustomGroups = 3
        Filters = 4
        Metrics = 5
        Prompts = 6
        Reports = 7
        Searches = 8
        Templates = 9

    class ObjectType(Enum):
        # https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLObjectTypes.html#DssXmlTypeLayer
        Generic = -2
        Unknown = -1
        AggMetric = 7
        Attribute = 12
        AttributeForm = 21
        Blob = 63
        Catalog = 24
        CatalogDefn = 25
        ChangeJournal = 66
        Column = 26
        Configuration = 36
        Consolidation = 47
        ConsolidationElement = 48
        DBConnection = 31
        DBLogin = 30
        DBMS = 57
        DBRole = 29
        Datamart = 41
        DatamartReport = 16
        DbTable = 53
        Device = 9
        Dimension = 14
        DocumentDefinition = 55
        DossierPersonalView = 73
        DrillMap = 56
        ExternalShortcut = 67
        ExternalShortcutTarget = 68
        Fact = 13
        FactGroup = 17
        Filter = 1
        Folder = 8
        Format = 23
        Function = 11
        FunctionPackageDefinition = 42
        Layer = 70
        Link = 52
        Locale = 45
        MDSecurityFilter = 58
        Metric = 4
        Monitor = 20
        ObjectTag = 65
        Palette = 71
        Project = 32
        Prompt = 10
        PromptAnswer = 59
        PromptAnswers = 60
        PropertySet = 28
        Reconciliation = 69
        ReportDefinition = 3
        Request = 37
        Reserved = 0
        ReservedLastOne = 74
        Resolution = 19
        Role = 43
        ScheduleEvent = 49
        ScheduleObject = 50
        ScheduleTrigger = 51
        Schema = 22
        Script = 38
        Search = 39
        SearchFolder = 40
        SecurityRole = 44
        ServerDef = 33
        Shortcut = 18
        Style = 6
        SubscriptionDevice = 9
        Table = 15
        TableSource = 54
        Template = 2
        Thresholds = 72
        Transmitter = 35

    ObjectTypeIDDict = {member.value: member for member in ObjectType}

    class ObjectSubType(Enum):
        # https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/webapi/EnumDSSXMLObjectSubTypes.html
        MetricTraining = 1028
        AggMetric = 1792
        Attribute = 3072
        AttributeAbstract = 3075
        AttributeForm = 5376
        AttributeRecursive = 3076
        AttributeRole = 3073
        AttributeTransformation = 3074
        BlobExcel = 16132
        BlobHTMLTemplate = 16133
        BlobImage = 16130
        BlobOther = 16129
        BlobProjectPackage = 16131
        BlobUnknown = 16128
        Catalog = 6144
        CatalogDefn = 6400
        ChangeJournal = 16896
        ChangeJournalSearch = 15872
        Column = 6656
        Configuration = 9216
        Consolidation = 12032
        ConsolidationElement = 12288
        ConsolidationManaged = 12033
        CustomGroup = 257
        DBConnection = 7936
        DBLogin = 7680
        DBMS = 14592
        DBRole = 7424
        DBRoleGenericDataConnector = 7430
        DBRoleOAuth = 7427
        DBTable = 13568
        DBTablePMT = 13569
        DashboardTemplate = 16384
        Datamart = 10496
        DatamartReport = 4096
        DerivedAttribute = 3077
        Device = 2304
        DimensionOrdered = 3586
        DimensionSystem = 3584
        DimensionUser = 3585
        DimensionUserHierarchy = 3587
        DocumentDefinition = 14080
        DocumentTheme = 14082
        DrillMap = 14336
        ExternalShortcutSnapshot = 17154
        ExternalShortcutTarget = 17408
        ExternalShortcutURL = 17153
        ExternalShortcutUnknown = 17152
        Fact = 3328
        FactGroup = 4352
        Filter = 256
        Flag = 16640
        Folder = 2048
        FormNormal = 5378
        FormSystem = 5377
        Format = 5888
        Function = 2816
        FunctionPackageDefinition = 10752
        GraphStyle = 15616
        InBox = 11520
        InBoxMsg = 11776
        Link = 13312
        MDSecurityFilter = 14848
        Metric = 1024
        MetricDMX = 1027
        MonitorDBConnections = 15107
        MonitorJobs = 15105
        MonitorPerformance = 15104
        MonitorUserConnections = 15106
        PaletteCustom = 17921
        PaletteSystem = 17920
        Project = 8192
        Prompt = 2560
        PromptAnswer = 15232
        PromptAnswerBigDecimal = 15243
        PromptAnswerBoolean = 15233
        PromptAnswerDate = 15237
        PromptAnswerDimty = 15242
        PromptAnswerDouble = 15236
        PromptAnswerElements = 15239
        PromptAnswerExpression = 15240
        PromptAnswerExpressionDraft = 15241
        PromptAnswerInt64 = 15244
        PromptAnswerLong = 15234
        PromptAnswerObjects = 15238
        PromptAnswerString = 15235
        PromptAnswers = 15360
        PromptBigDecimal = 2571
        PromptBoolean = 2561
        PromptDate = 2565
        PromptDimty = 2570
        PromptDouble = 2564
        PromptElements = 2567
        PromptExpression = 2568
        PromptExpressionDraft = 2569
        PromptLong = 2562
        PromptObjects = 2566
        PromptString = 2563
        PropertyGroup = 6912
        PropertySet = 7168
        Reconciliation = 17664
        ReportBase = 773
        ReportCube = 776
        ReportDatamart = 772
        ReportEmmaCube = 779
        ReportEmmaIncrementalRefresh = 780
        ReportEngine = 770
        ReportGraph = 769
        ReportGrid = 768
        ReportGridAndGraph = 774
        ReportIncrementalRefresh = 777
        ReportNonInteractive = 775
        ReportText = 771
        ReportTransaction = 778
        ReportWritingDocument = 14081
        Request = 9472
        Reserved = 0
        Resolution = 4864
        Role = 11008
        RoleTransformation = 11009
        ScheduleEvent = 12544
        ScheduleObject = 12800
        ScheduleTrigger = 13056
        Schema = 5632
        Search = 9984
        SearchFolder = 10240
        SecurityRole = 11264
        ServerDef = 8448
        Style = 1536
        SubscriptionAddress = 65281
        SubscriptionContact = 65282
        SubscriptionInstance = 65283
        SubtotalDefinition = 1025
        SystemSubtotal = 1026
        Table = 3840
        TablePartitionMD = 3841
        TablePartitionWH = 3842
        TableSource = 13824
        Template = 512
        Thresholds = 18432
        Transmitter = 8705
        Unknown = -1
        User = 8704

    ObjectSubTypeIDDict = {member.value: member for member in ObjectSubType}

    class FolderSortOrder(Enum):
        # https://lw.microstrategy.com/msdz/MSDL/GARelease_Current/docs/ReferenceFiles/reference/com/microstrategy/web/objects/EnumWebObjectSort.html
        ModificationTime = 7
        NoSort = -1
        ObjectDescription = 3
        ObjectName = 2
        ObjectNameFoldersFirst = 6
        ObjectOwner = 4
        ObjectType = 1
        ObjectTypeDisplayOrder = 5

    def get_folder_contents(self,
                            folder_id: str=None,
                            system_folder: Optional[SystemFolders]=7,
                            type_restriction: Optional[set]=None,
                            sort_key: Optional[FolderSortOrder]=None,
                            sort_ascending: Optional[bool]=True,
                            ):
        """Returns a dictionary with folder name, GUID, and description.

        Args
        ----
        folder_id:
            guid of folder to list contents.
            If not supplied, returns contents of system root folder as specified in system_folder

        system_folder:
            The numeric ID of the System Folder to inspect. Values correspond to the fields of the
            EnumDSSXMLFolderNames interface. If omitted, then the Shared Reports folder ('7') is used.

        type_restriction:
            A set of the object SubTypes to include in the contents.

        sort_key:
            How the elements of the folder are sorted. Sort keys are specified as integers, as described
            by the EnumWebObjectSort interface. If omitted, then WebObjectSortObjectNameFoldersFirst is used.

        sort_ascending:
            Sort the results in ascending order, if False, then descending order will be used.


        Returns
        -------
            list: list of dictionaries with keys id, name, description, and type
                as keys
        """

        arguments = {'sessionState': self._session,
                     'taskID': 'folderBrowse',
                     'includeObjectDesc': 'true',
                     'showObjectTags': 'true',
                     }
        if folder_id:
            arguments.update({'folderID': folder_id})
        if system_folder:
            if isinstance(system_folder, TaskProc.SystemFolders):
                system_folder = system_folder.value
            arguments.update({'systemFolder': system_folder})

        if type_restriction is None:
            # Note: Type 776 is added to the defaults to include cubes
            type_restriction = '2048,768,769,774,776,14081'
        elif not isinstance(type_restriction, str):
            type_restriction = ','.join([str(item) for item in set(type_restriction)])
        arguments.update({'typeRestriction': type_restriction})

        if sort_key:
            if isinstance(sort_key, TaskProc.FolderSortOrder):
                sort_key = sort_key.value
            arguments.update({'sortKey': sort_key})
        if not sort_ascending:
            arguments.update({'asc': 'false'})
        try:
            response = self._request(arguments)
        except MstrClientException as e:
            if 'The folder name is unknown to the server.' in e.args[0]:
                raise FileNotFoundError("Folder ID {} not found".format(folder_id))
            else:
                raise e
        result = []
        for folder in response('folders'):
            path_list = [path_folder.string for path_folder in folder.path.find_all('folder')]
            for obj in folder('obj'):
                object_dict = {
                    'name':        obj.find('n').string,
                    'path':        path_list,
                    'description': obj.find('d').string,
                    'guid':        obj.find('id').string,
                    'type':        obj.find('t').string,
                    'subtype':     obj.find('st').string,
                }
                # for child in obj.children:
                #     if child.name is not None:
                #         if child.name not in ['n','d','id','t','st']:
                #             print(child.name, child)
                try:
                    object_dict['type'] = int(object_dict['type'])
                    if object_dict['type'] in TaskProc.ObjectTypeIDDict:
                        object_dict['type'] = TaskProc.ObjectTypeIDDict[object_dict['type']]
                except ValueError:
                    pass
                try:
                    object_dict['subtype'] = int(object_dict['subtype'])
                    if object_dict['subtype'] in TaskProc.ObjectSubTypeIDDict:
                        object_dict['subtype'] = TaskProc.ObjectSubTypeIDDict[object_dict['subtype']]
                except ValueError:
                    pass
                result.append(object_dict)
        return result

    def get_folder_contents_by_name(self,
                                    name,
                                    type_restriction: Optional[set] = None,
                                    sort_key: Optional[FolderSortOrder] = None,
                                    sort_ascending: Optional[bool] = True,
                                    ):
        name_parts = re.split('[/\\\]', name)
        if isinstance(type_restriction, str):
            type_restriction = set(type_restriction.split(','))
        folder_contents = []
        sub_type_restriction = '2048'
        for folder_name in name_parts:
            if folder_name == 'Public Objects':
                folder_contents = self.get_folder_contents(system_folder=TaskProc.SystemFolders.PublicObjects,
                                                           type_restriction=sub_type_restriction,
                                                           sort_key=sort_key,
                                                           sort_ascending=sort_ascending,
                                                           )
            else:
                found = False
                for sub_folder in folder_contents:
                    if sub_folder['name'] == folder_name:
                        found = True
                        if sub_folder['type'] == TaskProc.ObjectType.Folder:
                            # If this is the last folder use the passed type_restriction
                            if folder_name == name_parts[-1]:
                                sub_type_restriction = type_restriction
                            folder_contents = self.get_folder_contents(folder_id=sub_folder['guid'],
                                                                       type_restriction=sub_type_restriction,
                                                                       sort_key=sort_key,
                                                                       sort_ascending=sort_ascending,
                                                                       )
                        else:
                            folder_contents = sub_folder
                if not found:
                    raise FileNotFoundError("{} not found when reading folder {}".format(folder_name, name))
        return folder_contents

    def get_folder_recursive_contents(self,
                                      guid: str = None,
                                      name: str = None,
                                      type_restriction: Optional[set] = None,
                                      sort_key: Optional[FolderSortOrder] = None,
                                      sort_ascending: Optional[bool] = True,
                                      ):
        if guid is not None:
            folder_contents = self.get_folder_contents(folder_id=guid,
                                                       type_restriction=type_restriction,
                                                       sort_key=sort_key,
                                                       sort_ascending=sort_ascending,
                                                       )
        elif name is not None:
            folder_contents = self.get_folder_contents_by_name(name,
                                                               type_restriction=type_restriction,
                                                               sort_key=sort_key,
                                                               sort_ascending=sort_ascending,
                                                               )
        else:
            raise ValueError("get_folder_recursive_contents requires name or guid")

        for item in folder_contents:
            if item['type'] == TaskProc.ObjectType.Folder:
                try:
                    item['contents'] = self.get_folder_recursive_contents(guid=item['guid'])
                except FileNotFoundError as e:
                    item['contents'] = e
        return folder_contents

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
        arguments = {'taskId': 'checkUserPrivileges',
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
    does not need to be instantiated, if an object with given parameters already exists.
    """

    @functools.lru_cache(maxsize=5000)
    def __call__(cls, *args, **kwargs):
        """
        Called when a new Singleton object is created.

        Singleton class checks to see if there is already a copy
        of the object in the class instances, and if so returns
        that object. Otherwise, it creates a new object of that
        subclass type.
        """
        return super(MemoizeClass, cls).__call__(*args, **kwargs)


class Attribute(object, metaclass=MemoizeClass):
    """
    Object encapsulating an attribute on MicroStrategy

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

    Each attribute can have multiple forms (different sets of source columns).
    Its __metaclass__ is Singleton.

    Args:
        form_guid (str): guid for this attribute
        form_name (str): the name of this attribute

    Attributes:
        attribute: An instance of Attribute
        form_guid:
            GUID for the form
        form_name:
            Name of the form
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


def _format_element_prompts(prompts) -> dict:
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


def _format_xml_prompts(v_prompts, e_prompts) -> dict:
    result = "<rsl>"
    for p, s in v_prompts:
        result = result + "<pa pt='5' pin='0' did='" + p.guid + \
                 "' tp='10'>" + s + "</pa>"
    result += "</rsl>"
    d = _format_element_prompts(e_prompts)
    d['promptsAnswerXML'] = result
    return d


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

    class ExecutionFlags(Enum):
        Fresh = 1
        UseCache = 128
        UpdateCache = 256
        Default = 384
        CheckWebCache = 16777216
        UseWebCacheOnly = 33554432

    def execute(self,
                start_row: int=0,
                start_col: int=0,
                max_rows: int=100000,
                max_cols: int=10,
                value_prompt_answers: Optional[list]=None,
                element_prompt_answers: Optional[dict]=None,
                execution_flags: Optional[set]=None,
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

        execution_flags:
            Integer combination of values from

        Raises
        ------
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
            arguments.update(_format_xml_prompts(value_prompt_answers,
                                                 element_prompt_answers)
                             )
        elif value_prompt_answers:
            arguments.update(_format_value_prompts(value_prompt_answers))
        elif element_prompt_answers:
            arguments.update(_format_element_prompts(element_prompt_answers))
        if execution_flags:
            arguments['execFlags'] = execution_flags
        arguments.update(self._args)
        response = self._mstr_client._request(arguments)
        self._executed = True
        self._values = self._parse_report(response)

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

