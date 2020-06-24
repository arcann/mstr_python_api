import re
import urllib.parse


import warnings
from enum import Enum

import time
from fnmatch import fnmatch

from typing import Optional, List, Set, Union

import requests
import logging

from bs4 import BeautifulSoup

from microstrategy_api.task_proc.document import Document
from microstrategy_api.task_proc.privilege_types import PrivilegeTypes, PrivilegeTypesIDDict
from microstrategy_api.task_proc.report import Report
from microstrategy_api.task_proc.attribute import Attribute
from microstrategy_api.task_proc.bit_set import BitSet
from microstrategy_api.task_proc.exceptions import MstrClientException
from microstrategy_api.task_proc.executable_base import ExecutableBase
from microstrategy_api.task_proc.object_type import ObjectType, ObjectTypeIDDict, ObjectSubTypeIDDict, ObjectSubType

BASE_PARAMS = {'taskEnv': 'xml', 'taskContentType': 'xml'}


class TaskProc(object):
    """
    Class encapsulating base logic for the MicroStrategy Task Proc API
    """

    def __init__(self,
                 base_url,
                 username=None,
                 password=None,
                 server=None,
                 project_source=None,  # deprecated
                 project_name=None,
                 session_state=None,
                 concurrent_max=5,
                 max_retries=3,
                 retry_delay=2,
                 ):
        """
        Initialize the MstrClient by logging in and retrieving a session.

        Arguments
        ----------
        base_url (str):
            base url of form http://hostname/MicroStrategy/asp/TaskProc.aspx
        username (str):
            username for project
        password (str):
            password for project
        server (str):
            The machine name (or IP) of the MicroStrategy Intelligence Server to connect to.
        project_name (str):
            The name of the MicroStrategy project to connect to.
        """
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        if 'TaskProc' in base_url:
            if base_url[-1] != '?':
                base_url += '?'
        self._base_url = base_url
        self.cookies = None
        self.trace = False
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.concurrent_max = concurrent_max
        self.server = server
        self.project_name = project_name
        self.username = username
        self.password = password
        self.__messages_to_retry_list = None

        if session_state is None:
            if project_source is not None:
                warnings.warn('project_source parameter is deprecated, use server parameter instead')
                if self.server is None:
                    self.server = project_source
                else:
                    warnings.warn('both project_source deprecated param and server parameter provided!'
                                  ' server parameter value used')
            else:
                if self.server is None:
                    raise ValueError('Neither server nor project_source (deprecated) parameter provided!')
            if self.username is not None:
                self.login()
            else:
                self.login_guest()
        else:
            self._session = session_state

    def __str__(self):
        return 'MstrClient session: {}'.format(self._session)

    @property
    def _messages_to_retry(self):
        if self.__messages_to_retry_list is None:
            regex_list = \
                [
                    'There are too many auditor handles at the moment. Please try again later.',
                    'There is possible deadlock. Please try to run the report later.',
                    'Failed to create job.',
                    '.* Number of jobs has exceeded maximum for project .*',
                    'Maximum number of executing jobs exceeded .*',
                ]
            self.__messages_to_retry_list = [re.compile(pattern) for pattern in regex_list]
        return self.__messages_to_retry_list

    @property
    def base_url(self):
        return self._base_url

    def login(self,
              server: str=None,
              project_name: str=None,
              username: str=None,
              password: str=None,
              ):
        """
        Login to taskproc API

        Arguments
        ----------
        server (str):
            The machine name (or IP) of the MicroStrategy Intelligence Server to connect to.
        project_name (str):
            The name of the MicroStrategy project to connect to.
        username (str):
            username for project
        password (str):
            password for project

        """
        if server:
            self.server = server
        if project_name:
            self.project_name = project_name
        if username:
            self.username = username
        if password:
            self.password = password

        # getSessionState is used instead of login because we can set the rws parameter that way.
        # arguments = {
        #     'taskId':   'login',
        #     'server':   self.server,
        #     'project':  self.project_name,
        #     'userid':   self.username,
        #     'password': self.password
        # }

        arguments = {
                'taskId': 'getSessionState',
                'server': self.server,
                'project': self.project_name,
                'uid': self.username,
                'pwd': self.password,
                'rws': self.concurrent_max,
            }
        self.log.debug("logging in.")
        response = self.request(arguments)
        if self.trace:
            self.log.debug("logging in returned %s" % response)
        # self._session_state = response.find('sessionState')
        self._session = response.find('max-state').string

    def login_guest(self,
                    server: str=None,
                    project_name: str=None,
                    ):
        """
        Login to taskproc API

        Arguments
        ----------
        server (str):
            The machine name (or IP) of the MicroStrategy Intelligence Server to connect to.
        project_name (str):
            The name of the MicroStrategy project to connect to.

        """
        if server:
            self.server = server
        if project_name:
            self.project_name = project_name

        arguments = {
                'taskId':   'getSessionState',
                'server':   self.server,
                'project':  self.project_name,
                'authMode':   8,
                'rws': self.concurrent_max,
            }
        self.log.debug("logging in as guest")
        response = self.request(arguments)
        if self.trace:
            self.log.debug("logging in returned %s" % response)
        # self._session_state = response.find('sessionState')
        self._session = response.find('max-state').string

    @property
    def session(self):
        return self._session

    class SystemFolders(Enum):  # EnumDSSXMLFolderNames
        """
        This interface defines the enumeration constants used to specify the folder names internally defined in MicroStrategy 7.
        """

        PublicObjects = 1  # DssXmlFolderNamePublicObjects Specifies the folder "Public Objects".
        PublicConsolidations = 2  # DssXmlFolderNamePublicConsolidations Specifies the folder "Consolidations" under the folder "Public Objects".
        PublicCustomGroups = 3  # DssXmlFolderNamePublicCustomGroups Specifies the folder "Custom Groups" under the folder "Public Objects".
        PublicFilters = 4  # DssXmlFolderNamePublicFilters Specifies the folder "Filters" under the folder "Public Objects".
        PublicMetrics = 5  # DssXmlFolderNamePublicMetrics Specifies the folder "Metrics" under the folder "Public Objects".
        PublicPrompts = 6  # DssXmlFolderNamePublicPrompts Specifies the folder "Prompts" under the folder "Public Objects".
        PublicReports = 7  # DssXmlFolderNamePublicReports Specifies the folder "Reports" under the folder "Public Objects".
        PublicSearches = 8  # DssXmlFolderNamePublicSearches Specifies the folder "Searches" under the folder "Public Objects".
        PublicTemplates = 9  # DssXmlFolderNamePublicTemplates Specifies the folder "Templates" under the folder "Public Objects".
        TemplateObjects = 10  # DssXmlFolderNameTemplateObjects Specifies the folder "Template Objects".
        TemplateConsolidations = 11  # DssXmlFolderNameTemplateConsolidations Specifies the folder "Consolidations" under the folder "Template Objects".
        TemplateCustomGroups = 12  # DssXmlFolderNameTemplateCustomGroups Specifies the folder "Custom Groups" under the folder "Template Objects".
        TemplateFilters = 13  # DssXmlFolderNameTemplateFilters Specifies the folder "Filters" under the folder "Template Objects".
        TemplateMetrics = 14  # DssXmlFolderNameTemplateMetrics Specifies the folder "Metrics" under the folder "Template Objects".
        TemplatePrompts = 15  # DssXmlFolderNameTemplatePrompts Specifies the folder "Prompts" under the folder "Template Objects".
        TemplateReports = 16  # DssXmlFolderNameTemplateReports Specifies the folder "Reports" under the folder "Template Objects".
        TemplateSearches = 17  # DssXmlFolderNameTemplateSearches Specifies the folder "Searches" under the folder "Template Objects".
        TemplateTemplates = 18  # DssXmlFolderNameTemplateTemplates Specifies the folder "Templates" under the folder "Template Objects".
        ProfileObjects = 19  # DssXmlFolderNameProfileObjects Specifies the folder "Profile" of a user.
        ProfileReports = 20  # DssXmlFolderNameProfileReports Specifies the folder "Reports" under the folder "Profile" of a user.
        ProfileAnswers = 21  # DssXmlFolderNameProfileAnswers Specifies the folder "Answers" under the folder "Profile" of a user.
        ProfileFavorites = 22  # DssXmlFolderNameProfileFavorites Specifies the folder "Favorites" under the folder "Profile" of a user.
        ProfileOther = 23  # DssXmlFolderNameProfileOther Specifies the folder "Other" under the folder "Profile" of a user.
        SchemaObjects = 24  # DssXmlFolderNameSchemaObjects Specifies the folder "Schema Objects".
        SchemaAttributeForms = 25  # DssXmlFolderNameSchemaAttributeForms Specifies the folder "Attribute Forms" under the folder "Schema Objects".
        SchemaAttributes = 26  # DssXmlFolderNameSchemaAttributes Specifies the folder "Attributes" under the folder "Schema Objects".
        SchemaColumns = 27  # DssXmlFolderNameSchemaColumns Specifies the folder "Columns" under the folder "Schema Objects".
        SchemaDataExplorer = 28  # DssXmlFolderNameSchemaDataExplorer Specifies the folder "Data Explorer" under the folder "Schema Objects".
        SchemaFacts = 29  # DssXmlFolderNameSchemaFacts Specifies the folder "Facts" under the folder "Schema Objects".
        SchemaFunctions = 30  # DssXmlFolderNameSchemaFunctions Specifies the folder "Functions" under the folder "Schema Objects".
        SchemaHierarchies = 31  # DssXmlFolderNameSchemaHierarchies Specifies the folder "Hierarchies" under the folder "Schema Objects".
        SchemaPartitionFilters = 32  # DssXmlFolderNameSchemaPartitionFilters Specifies the folder "Partition Filters" under the folder "Schema Objects".
        SchemaPartitionMappings = 33  # DssXmlFolderNameSchemaPartitionMappings Specifies the folder "Partition Mappings" under the folder "Schema Objects".
        SchemaSubtotals = 34  # DssXmlFolderNameSchemaSubtotals Specifies the folder"Subtotals" under the folder "Schema Objects".
        SchemaTables = 35  # DssXmlFolderNameSchemaTables Specifies the folder "Tables" under the folder "Schema Objects".
        SchemaWarehouseTables = 36  # DssXmlFolderNameSchemaWarehouseTables Specifies the folder "Warehouse Tables" under the folder "Schema Objects".
        SchemaTransformationAttributes = 37  # DssXmlFolderNameSchemaTransformationAttributes Specifies the folder "Transformation Attributes" under the folder "Schema Objects".
        SchemaTransformations = 38  # DssXmlFolderNameSchemaTransformations Specifies the folder "Transformations" under the folder "Schema Objects".
        Root = 39  # DssXmlFolderNameRoot Specifies the root folder of the project.
        SchemaFunctionsNested = 40  # DssXmlFolderNameSchemaFunctionsNested Specifies the "Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaBasicFunctions = 41  # DssXmlFolderNameSchemaBasicFunctions Specifies the "Basic Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaDateAndTimeFunctions = 42  # DssXmlFolderNameSchemaDateAndTimeFunctions Specifies the "Date and Time Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaInternalFunctions = 43  # DssXmlFolderNameSchemaInternalFunctions Specifies the "Internal Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaNullZeroFunctions = 44  # DssXmlFolderNameSchemaNullZeroFunctions Specifies the "Null/Zero Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaOlapFunctions = 45  # DssXmlFolderNameSchemaOlapFunctions Specifies the "OLAP Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaRankAndNTileFunctions = 46  # DssXmlFolderNameSchemaRankAndNTileFunctions Specifies the "Rank and NTile Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaStringFunctions = 47  # DssXmlFolderNameSchemaStringFunctions Specifies the "String Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaOperators = 48  # DssXmlFolderNameSchemaOperators Specifies the "Operators" folder nested several levels deep in the "Schema Objects" folder.
        SchemaArithmeticOperators = 49  # DssXmlFolderNameSchemaArithmeticOperators Specifies the "Arithmetic Operators" folder nested several levels deep in the "Schema Objects" folder.
        SchemaComparisonOperators = 50  # DssXmlFolderNameSchemaComparisonOperators Specifies the "Comparison Operators" folder nested several levels deep in the "Schema Objects" folder.
        SchemaComparisonForRankOperators = 51  # DssXmlFolderNameSchemaComparisonForRankOperators Specifies the "Comparison Operators for Rank" folder nested several levels deep in the "Schema Objects" folder.
        SchemaLogicalOperators = 52  # DssXmlFolderNameSchemaLogicalOperators Specifies the "Logical Operators" folder nested several levels deep in the "Schema Objects" folder.
        SchemaPlugInPackages = 53  # DssXmlFolderNameSchemaPlugInPackages Specifies the "Plug-In Packages" folder nested several levels deep in the "Schema Objects" folder.
        SchemaFinancialFunctions = 54  # DssXmlFolderNameSchemaFinancialFunctions Specifies the "Financial Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaMathFunctions = 55  # DssXmlFolderNameSchemaMathFunctions Specifies the "Math Functions" folder nested several levels deep in the "Schema Objects" folder.
        SchemaStatisticalFunctions = 56  # DssXmlFolderNameSchemaStatisticalFunctions Specifies the "Statistical Functions" folder nested several levels deep in the "Schema Objects" folder.
        AutoStyles = 57  # DssXmlFolderNameAutoStyles Specifies the "AutoStyles" folder in the "Public Objects" folder.
        ConfigureMonitors = 58  # DssXmlFolderNameConfigureMonitors Specifies the "Monitors" folder in the Configuration.
        ConfigureServerDefs = 59  # DssXmlFolderNameConfigureServerDefs Specifies the "Server Definitions" folder in the Configuration.
        TemplateDocuments = 60  # DssXmlFolderNameTemplateDocuments Specifies the "Template Documents" folder.
        SystemObjects = 61  # DssXmlFolderNameSystemObjects Specifies the "System Objects" folder.
        SystemLinks = 62  # DssXmlFolderNameSystemLinks Specifies the "System Links" folder.
        SystemPropertySets = 63  # DssXmlFolderNameSystemPropertySets Specifies the "System Property sets" folder.
        SystemParserFolder = 64  # DssXmlFolderNameSystemParserFolder Specifies the "System Parser" folder.
        SystemSchemaFolder = 65  # DssXmlFolderNameSystemSchemaFolder Specifies the "System Schema" folder.
        SystemWarehouseCatalog = 66  # DssXmlFolderNameSystemWarehouseCatalog Specifies the "System Warehouse catalog" folder.
        SystemSystemHierarchy = 67  # DssXmlFolderNameSystemSystemHierarchy Specifies the "System Hierarchy" folder.
        SystemDrillMap = 68  # DssXmlFolderNameSystemDrillMap Specifies the "System Drill Map" folder.
        SystemMDSecurityFilters = 69  # DssXmlFolderNameSystemMDSecurityFilters Specifies the "System MD Security Filters" folder.
        SystemDummyPartitionTables = 70  # DssXmlFolderNameSystemDummyPartitionTables Specifies the "System Dummy Partition Tables" folder.
        SystemSystemPrompts = 71  # DssXmlFolderNameSystemSystemPrompts Specifies the "System Prompts" folder.
        Events = 72  # DssXmlFolderNameEvents None
        ConfigureDBRoles = 73  # DssXmlFolderNameConfigureDBRoles None
        Locales = 74  # DssXmlFolderNameLocales None
        PropertySets = 75  # DssXmlFolderNamePropertySets Specifies the folder where Property Sets are stored
        DBMS = 76  # DssXmlFolderNameDBMS None
        Projects = 77  # DssXmlFolderNameProjects Specifies the folder where Projects are stored
        Users = 78  # DssXmlFolderNameUsers Specifies the folder where Users are stored
        UserGroups = 79  # DssXmlFolderNameUserGroups Specifies the folder where User Groups are stored
        SecurityRoles = 80  # DssXmlFolderNameSecurityRoles Specifies the folder where Security Roles are stored
        DBConnections = 81  # DssXmlFolderNameDBConnections None
        DBLogins = 82  # DssXmlFolderNameDBLogins None
        Links = 83  # DssXmlFolderNameLinks Specifies the folder where Links are stored
        ScheduleObjects = 84  # DssXmlFolderNameScheduleObjects Specifies the folder where Schedules are stored
        ScheduleTriggers = 85  # DssXmlFolderNameScheduleTriggers Specifies the folder where Schedule Triggers are stored
        TableSources = 86  # DssXmlFolderNameTableSources None
        VersionUpdateHistory = 87  # DssXmlFolderNameVersionUpdateHistory Specifies the folder where the Version Update History is stored
        Devices = 88  # DssXmlFolderNameDevices Specifies the folder where Devices are stored
        Transmitters = 89  # DssXmlFolderNameTransmitters Specifies the folder where Transmitters are stored
        TemplateDashboards = 90  # DssXmlFolderNameTemplateDashboards Specifies the folder where Template Dashboards are stored
        SystemDimension = 91  # DssXmlFolderNameSystemDimension Specifies the DSS ID of the system dimension object
        ProfileSegments = 92  # DssXmlFolderNameProfileSegments None
        TemplateAnalysis = 93  # DssXmlFolderNameTemplateAnalysis Specifies "Analysis" folder under "Template Objects"
        Palettes = 94  # DssXmlFolderNamePalettes Palettes folder
        Themes = 95  # DssXmlFolderNameThemes Themes folder
        MyDossiers = 96  # DssXmlFolderNameMyDossiers Personal Dossiers folder
        MySharedDossiers = 97  # DssXmlFolderNameMySharedDossiers Shared Dossiers folder
        Maximum = 98  # DssXmlFolderNameMaximum Acts as a current maximum value. This should only be used as its symbolic name, not a hardcoded enumeration value, because it may change as more folder names are added.
        BlackListed = 1000  # DssXmlFolderNameBlackListed Special value that will allow black listed folders to be treated uniquely

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

    class FolderObject(object):
        def __init__(self, guid, name, path, description, object_type, object_subtype):
            self.guid = guid
            self.name = name
            self.path = path
            self.description = description
            self.contents = None

            try:
                object_type = int(object_type)
                if object_type in ObjectTypeIDDict:
                    object_type = ObjectTypeIDDict[object_type]
            except ValueError:
                pass
            self.object_type = object_type

            try:
                object_subtype = int(object_subtype)
                if object_subtype in ObjectSubTypeIDDict:
                    object_subtype = ObjectSubTypeIDDict[object_subtype]
            except ValueError:
                pass
            self.object_subtype = object_subtype

        def path_str(self):
            return '\\' + '\\'.join(self.path)

        def full_name(self):
            return self.path_str() + '\\' + self.name

        def __str__(self) -> str:
            return self.full_name()

        def __repr__(self) -> str:
            return "'{}'\t\t   type={} subtype={} guid={}".format(self.full_name(),
                                                                  self.object_type,
                                                                  self.object_subtype, self.guid)

    def get_folder_contents_by_guid(self,
                                    folder_guid: str=None,
                                    system_folder: Optional[SystemFolders]=None,
                                    type_restriction: Optional[set]=None,
                                    sort_key: Optional[FolderSortOrder]=None,
                                    sort_ascending: Optional[bool]=True,
                                    name_patterns_to_include: Optional[List[str]]=None,
                                    name_patterns_to_exclude: Optional[List[str]]=None,
                                    ):
        """Returns a dictionary with folder name, GUID, and description.

        Args
        ----
        folder_guid:
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

        name_patterns_to_include:
            A list of file name patterns (using * wildcards) to include. Not case sensitive.

        name_patterns_to_exclude:
            A list of file name patterns (using * wildcards) to exclude. Not case sensitive.


        Returns
        -------
            list: list of dictionaries with keys id, name, description, and type
                as keys
        """
        if isinstance(name_patterns_to_include, str):
            name_patterns_to_include = [name_patterns_to_include]
        if isinstance(name_patterns_to_exclude, str):
            name_patterns_to_exclude = [name_patterns_to_exclude]

        arguments = {'sessionState': self._session,
                     'taskID': 'folderBrowse',
                     'includeObjectDesc': 'true',
                     'showObjectTags': 'true',
                     }
        if folder_guid:
            arguments['folderID'] = folder_guid
        if system_folder:
            if isinstance(system_folder, TaskProc.SystemFolders):
                system_folder = system_folder.value
            arguments['systemFolder'] = system_folder

        if type_restriction is None:
            # Note: Type 776 is added to the defaults to include cubes
            type_restriction = '2048,768,769,774,776,14081'
        elif not isinstance(type_restriction, str):
            type_restriction_codes = set()
            # noinspection PyTypeChecker
            for type_restriction_val in type_restriction:
                if isinstance(type_restriction_val, ObjectSubType):
                    type_restriction_codes.add(str(type_restriction_val.value))
                else:
                    type_restriction_codes.add(str(type_restriction_val))
            type_restriction = ','.join(type_restriction_codes)
        arguments['typeRestriction'] = type_restriction

        if sort_key:
            arguments['sortKey'] = sort_key
        if not sort_ascending:
            arguments['asc'] = 'false'
        try:
            response = self.request(arguments)
        except MstrClientException as e:
            if 'The folder name is unknown to the server.' in e.msg:
                raise FileNotFoundError("Folder ID {} not found".format(folder_guid))
            else:
                raise e
        result = []
        for folder in response('folders'):
            path_list = list()
            for seq_num, path_folder in enumerate(folder.path.find_all('folder')):
                path_folder_name = path_folder.string
                if seq_num == 0 and path_folder_name == 'Shared Reports':
                    path_list.append('Public Objects')
                    path_folder_name = 'Reports'
                path_list.append(path_folder_name)
            folder_name = folder.attrs['name']
            if len(path_list) == 0 and folder_name == 'Shared Reports':
                path_list.append('Public Objects')
                folder_name = 'Reports'
            path_list.append(folder_name)
            for obj in folder('obj'):
                name = obj.find('n').string
                if name_patterns_to_include is None:
                    name_ok = True
                else:
                    name_ok = False
                    for include_pattern in name_patterns_to_include:
                        if fnmatch(name.lower(), include_pattern.lower()):
                            name_ok = True
                if name_patterns_to_exclude is not None:
                    for exclude_pattern in name_patterns_to_exclude:
                        if fnmatch(name.lower(), exclude_pattern.lower()):
                            name_ok = False

                if name_ok:
                    obj_inst = TaskProc.FolderObject(
                                  guid=obj.find('id').string,
                                  name=name,
                                  path=path_list,
                                  description=obj.find('d').string,
                                  object_type=obj.find('t').string,
                                  object_subtype=obj.find('st').string,
                               )
                    result.append(obj_inst)
        return result

    @staticmethod
    def path_parts(path) -> List[str]:
        # MSTR Paths should use \ separators, however, if the paths starts with / we'll try and use that
        if len(path) == 0:
            return []
        elif path[0] == '/':
            return re.split('[/\\\]', path)
        else:
            return re.split('[\\\]', path)

    def get_folder_contents_by_name(self,
                                    name: Union[str, List[str]],
                                    type_restriction: Optional[set] = None,
                                    sort_key: Optional[FolderSortOrder] = None,
                                    sort_ascending: Optional[bool] = True,
                                    name_patterns_to_include: Optional[List[str]] = None,
                                    name_patterns_to_exclude: Optional[List[str]] = None,
                                    ):
        if isinstance(name, str):
            name_parts = TaskProc.path_parts(name)
        else:
            # Blindly assume it's an iterable type
            name_parts = name
        if isinstance(type_restriction, str):
            type_restriction = set(type_restriction.split(','))
        folder_contents = []
        intermediatefolder_type_restriction = {'2048'}
        for folder_name in name_parts:
            if folder_name == '':
                pass
            elif folder_name == 'Public Objects':
                folder_contents = self.get_folder_contents_by_guid(system_folder=TaskProc.SystemFolders.PublicObjects,
                                                                   type_restriction=intermediatefolder_type_restriction,
                                                                   sort_key=sort_key,
                                                                   sort_ascending=sort_ascending,
                                                                   )
            else:
                found = False
                new_folder_contents = None
                for sub_folder in folder_contents:
                    if sub_folder.name == folder_name:
                        found = True
                        if sub_folder.object_type == ObjectType.Folder:
                            # If this is the last folder use the passed type_restriction and name patterns
                            if folder_name == name_parts[-1]:
                                new_folder_contents = self.get_folder_contents_by_guid(
                                    folder_guid=sub_folder.guid,
                                    type_restriction=type_restriction,
                                    sort_key=sort_key,
                                    sort_ascending=sort_ascending,
                                    name_patterns_to_include=name_patterns_to_include,
                                    name_patterns_to_exclude=name_patterns_to_exclude,
                                )
                            else:
                                new_folder_contents = self.get_folder_contents_by_guid(
                                    folder_guid=sub_folder.guid,
                                    type_restriction=intermediatefolder_type_restriction,
                                    sort_key=sort_key,
                                    sort_ascending=sort_ascending,
                                )

                        else:
                            new_folder_contents = sub_folder
                if not found:
                    if isinstance(name, str):
                        msg = f'"{folder_name}" not found when processing path {name}\nParts={name_parts}'
                    else:
                        msg = f'"{folder_name}" not found when processing path {name}'
                    raise FileNotFoundError(msg)
                else:
                    folder_contents = new_folder_contents
        return folder_contents

    def get_folder_contents(self,
                            name: Union[str, List[str]],
                            type_restriction: Optional[set] = None,
                            sort_key: Optional[FolderSortOrder] = None,
                            sort_ascending: Optional[bool] = True,
                            recursive: Optional[bool] = True,
                            flatten_structure: Optional[bool] = True,
                            name_patterns_to_include: Optional[List[str]] = None,
                            name_patterns_to_exclude: Optional[List[str]] = None,
                            ) -> List[FolderObject]:
        if type_restriction is not None:
            sub_type_restriction = type_restriction.copy()
            if recursive:
                sub_type_restriction.add(ObjectSubType.Folder)
        else:
            sub_type_restriction = None

        if isinstance(name, str) and len(name) == 32 and '/' not in name and '\\' not in name:
            folder_contents = self.get_folder_contents_by_guid(folder_guid=name,
                                                               type_restriction=sub_type_restriction,
                                                               sort_key=sort_key,
                                                               sort_ascending=sort_ascending,
                                                               name_patterns_to_include=name_patterns_to_include,
                                                               name_patterns_to_exclude=name_patterns_to_exclude,
                                                               )
        else:
            folder_contents = self.get_folder_contents_by_name(name,
                                                               type_restriction=sub_type_restriction,
                                                               sort_key=sort_key,
                                                               sort_ascending=sort_ascending,
                                                               name_patterns_to_include=name_patterns_to_include,
                                                               name_patterns_to_exclude=name_patterns_to_exclude,
                                                               )
        if recursive:
            for item in folder_contents:
                if item.object_type == ObjectType.Folder:
                    try:
                        contents = self.get_folder_contents(
                                     name=item.guid,
                                     type_restriction=type_restriction,
                                     sort_key=sort_key,
                                     sort_ascending=sort_ascending,
                                     recursive=recursive,
                                     flatten_structure=flatten_structure,
                                     name_patterns_to_include=name_patterns_to_include,
                                     name_patterns_to_exclude=name_patterns_to_exclude,
                                   )
                    except FileNotFoundError as e:
                        contents = e

                    if flatten_structure:
                        if isinstance(contents, list):
                            folder_contents.extend(contents)
                    else:
                        item.contents = contents

        if flatten_structure:
            if type_restriction is not None:
                folder_contents = [sub for sub in folder_contents if sub.object_subtype in type_restriction]

        return folder_contents

    def get_folder_object(self,
                          name: str,
                          type_restriction: Optional[set] = None,
                          ) -> FolderObject:
        name_parts = TaskProc.path_parts(name)
        folder_name = '/'.join(name_parts[:-1])
        object_name = name_parts[-1]
        folder_contents = self.get_folder_contents(folder_name, type_restriction=type_restriction, name_patterns_to_include=[object_name])
        if len(folder_contents) == 0:
            raise FileNotFoundError("Folder {} does not contain {} (that matches type {})".format(
                folder_name, object_name, type_restriction
            ))
        elif len(folder_contents) > 1:
            raise FileNotFoundError("Folder {} does contains multiple matches for {} (that match type {})\n {}".format(
                folder_name, object_name, type_restriction, folder_contents,
            ))
        else:
            return folder_contents[0]

    def get_matching_objects_list(self, path_list: list, type_restriction: set, error_list=None) -> List[FolderObject]:
        """
        Get a list of matching FolderObjects based on a list of object name patterns.
        Patterns accept wildcards:
        - * for any set of characters. Allowed in the object name part of the path but not the folder name part.
        - Patterns that end in [r] will match objects in any sub folder. Any non / characters immediately before
          the [r] will be considered as an object name pattern to match in all sub folders.

        Parameters
        ----------
        path_list:
            A list of path patterns
        type_restriction:
            A set of ObjectSubType values to allow.
        error_list:
            Option list to return path errors (FileNotFoundError) in. If not passed, then errors are raised.


        Returns
        -------
        A list of matching FolderObject
        """
        if isinstance(path_list, str):
            path_list = [path_list]
        result_list = list()
        for path in path_list:
            path = path.strip()
            try:
                if path == '':
                    pass
                elif path[-3:].lower() == '[r]':
                    # Ends in [r] so recursive search is needed
                    path_parts = self.path_parts(path)
                    folder = path_parts[:-1]
                    file_name = path_parts[-1][:-3]
                    if file_name == '':
                        file_name_list = None
                    else:
                        file_name_list = [file_name]
                    contents = self.get_folder_contents(
                        name=folder,
                        name_patterns_to_include=file_name_list,
                        recursive=True,
                        flatten_structure=True,
                        type_restriction=type_restriction,
                    )
                    if len(contents) == 0:
                        msg = f"Path pattern {path} returned no matches"
                        if error_list is not None:
                            error_list.append(msg)
                        else:
                            self.log.warning(msg)
                    result_list.extend(contents)
                else:
                    # Non recursive pass last part as name_patterns_to_include
                    path_parts = self.path_parts(path)
                    contents = self.get_folder_contents(
                        name=path_parts[:-1],
                        name_patterns_to_include=[path_parts[-1]],
                        recursive=False,
                        flatten_structure=True,
                        type_restriction=type_restriction,
                    )
                    if len(contents) == 0:
                        self.log.warning("Path pattern {} returned no matches".format(path))
                    result_list.extend(contents)
            except FileNotFoundError as e:
                if error_list is None:
                    raise e
                else:
                    error_list.append(f'{path} yields {e}')
        return result_list

    def get_executable_object(self, folder_obj: FolderObject) -> ExecutableBase:
        # Check based on object type
        if folder_obj.object_subtype == ObjectSubType.ReportWritingDocument:
            # Document
            return Document(self, guid=folder_obj.guid, name=folder_obj.full_name())
        elif folder_obj.object_subtype == ObjectSubType.ReportCube:
            # Cube
            return Report(self, guid=folder_obj.guid, name=folder_obj.full_name())
        else:
            # Regular report
            return Report(self, guid=folder_obj.guid, name=folder_obj.full_name())

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

        arguments = {'taskId':       'browseElements',
                     'attributeID':  attribute_id,
                     'sessionState': self._session}
        response = self.request(arguments)
        result = []
        for attr in response('block'):
            if attr.find('n').string:
                result.append(attr.find('n').string)
        return result

    def check_user_privileges(self, privilege_types: Set[PrivilegeTypes]=None) -> dict:
        if privilege_types is None:
            privilege_types = {PrivilegeTypes.WebExecuteAnalysis}
        arguments = {'taskId': 'checkUserPrivileges',
                     'privilegeTypes': privilege_types,
                     'sessionState':   self._session}
        response = self.request(arguments)
        priv_dict = dict()
        priv_entries = response.find_all('privilege')
        for privilege in priv_entries:
            priv = privilege['type']
            try:
                priv = int(priv)
                if priv in PrivilegeTypesIDDict:
                    priv = PrivilegeTypesIDDict[priv]
            except ValueError:
                pass
            value = privilege['value']
            if value == '1':
                value = True
            elif value == '0':
                value = False
            else:
                raise ValueError("Priv value {} is not valid in {}".format(value, priv_entries))
            priv_dict[priv] = value
        return priv_dict

    def get_user_info(self):
        profile_objects = self.get_folder_contents_by_guid(system_folder=TaskProc.SystemFolders.ProfileObjects)
        profile_first_object = profile_objects[0]
        profile_name = profile_first_object.path[-1]
        # For example John Adams (jadams)
        full_name, user_id = profile_name.split('(', 1)
        user_id = user_id[:-1]
        return full_name, user_id

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
        response = self.request(arguments)
        return Attribute(response.find('dssid').string, response.find('n').string)

    def logout(self):
        arguments = {
            'taskId':       'logout',
            'sessionState': self._session,
        }
        arguments.update(BASE_PARAMS)
        try:
            result = self.request(arguments, max_retries=0)
        except Exception as e:
            result = str(e)
        self._session = None
        if self.trace:
            self.log.debug("logging out returned %s" % result)

    def request(self, arguments: dict, max_retries: int = None) -> BeautifulSoup:
        """
        Assembles the url and performs a get request to
        the MicroStrategy Task Service API

        Arumgents
        ---------
        arguments:
            Maps get key parameters to values
        max_retries:
            Optional. Number of retries to allow. Default = 1.

        Returns:
            The xml response as a BeautifulSoup 4 object.
        """

        if max_retries is None:
            max_retries = self.max_retries

        arguments.update(BASE_PARAMS)
        for arg_name, arg_value in arguments.items():
            if isinstance(arg_value, str):
                pass
            elif isinstance(arg_value, Enum):
                arguments[arg_name] = str(arg_value.value)
            elif isinstance(arg_value, BitSet):
                arguments[arg_name] = arg_value.combine()
            elif isinstance(arg_value, list) or isinstance(arg_value, set):
                if len(arg_value) == 0:
                    arguments[arg_name] = ''
                elif isinstance(list(arg_value)[0], Enum):
                    new_arg_value = set()
                    for arg_sub_value in arg_value:
                        if isinstance(arg_sub_value, Enum):
                            new_arg_value.add(str(arg_sub_value.value))
                        else:
                            new_arg_value.add(str(arg_sub_value))
                    arg_value = new_arg_value
                arguments[arg_name] = ','.join(arg_value)
            else:
                arguments[arg_name] = str(arg_value)

        if self.trace:
            self.log.debug("arguments {}".format(arguments))
        request = self._base_url + urllib.parse.urlencode(arguments)
        if self.trace:
            self.log.debug("submitting request {}".format(request))
        result_bs4 = None
        done = False
        tries = 0
        exception = None
        while not done:
            try:
                response = requests.get(request, cookies=self.cookies)
                if self.trace:
                    self.log.debug(f"received response {response}")
                if response.status_code != 200:
                    exception = MstrClientException(
                        msg=f"Server response {response}.",
                        request=request
                    )
                else:
                    self.cookies = response.cookies
                result_bs4 = BeautifulSoup(response.text, 'xml')
                task_response = result_bs4.find('taskResponse')
                if task_response is None:
                    self.log.error(response)
                    self.log.error(task_response)
                    error = f"Unexpected server response with no taskResponse tag {result_bs4.prettify()}"
                    exception = MstrClientException(
                        msg=f"Server error '{error}'",
                        request=request
                    )
                else:
                    if task_response.attrs is None or 'statusCode' not in task_response.attrs:
                        self.log.error(response)
                        self.log.error(task_response)
                        error = f"Unexpected server response with no statusCode in taskResponse tag {task_response}"
                        exception = MstrClientException(
                            msg=f"Server error '{error}'",
                            request=request
                        )
                    else:
                        if task_response['statusCode'] in ['400', '500']:
                            self.log.error(response)
                            self.log.error(task_response)
                            error = task_response['errorMsg']
                            exception = MstrClientException(
                                msg=f"Server error '{error}'",
                                request=request
                            )
            except requests.packages.urllib3.exceptions.NewConnectionError as e:
                exception = e

            if exception is None:
                done = True
            else:
                error = exception.msg
                messages_to_retry = self._messages_to_retry
                time.sleep(1)
                if isinstance(exception, requests.packages.urllib3.exceptions.NewConnectionError):
                    if tries < max_retries:
                        self.log.info("Request failed with error {}".format(repr(exception)))
                        time.sleep(self.retry_delay)
                        self.log.info("Retrying. Tries={} < {} max".format(tries, max_retries))
                        # Count these as 1/1000 of a try (allows 5 minutes of retries) for each max_retries
                        tries += (1/300)
                    else:
                        self.log.error('. Tries limit {} reached'.format(tries))
                        raise exception
                elif 'automatically logged out' in error:
                    if tries < max_retries:
                        tries += 1
                        # We can't re-login if we don't have a username (ie. we authenticated with a session_state value)
                        if self.username is not None:
                            self.log.info("Request failed with error {}".format(repr(exception)))
                            time.sleep(self.retry_delay)
                            self.log.info("Logging back in. Tries= {} < {} max".format(tries, max_retries))
                            try:
                                self.logout()
                            except MstrClientException:
                                pass
                            self.login()
                        else:
                            exception.msg += '. Re-login not possible without username.'
                            raise exception
                    else:
                        self.log.error('. Tries limit {} reached'.format(tries))
                        raise exception
                elif any(regex_pattern.match(error) for regex_pattern in messages_to_retry):
                    if tries < max_retries:
                        self.log.info("Request failed with error {}".format(repr(exception)))
                        time.sleep(self.retry_delay)
                        self.log.info("Retrying. Tries={} < {} max".format(tries, max_retries))
                        tries += 1
                    else:
                        self.log.error('. Tries limit {} reached'.format(tries))
                        raise exception
                else:
                    self.log.debug("Request failed with error {}".format(repr(exception)))
                    raise exception

        return result_bs4


def get_task_client_from_config(config, config_section) -> TaskProc:
    task_url = config[config_section]['task_url'].strip()
    server = config[config_section]['server_name'].strip()
    project = config[config_section]['project'].strip()
    user_id = config[config_section]['user_id']
    password = config[config_section].get('password')
    if password is None:
        keyring_section = config[config_section]['keyring_section'].strip()
        try:
            import keyring
            password = keyring.get_password(keyring_section, user_id)
        except ImportError:
            raise ValueError("Password not provided and keyring not installed")
    concurrent_max = config[config_section].get('concurrent_max', 10)
    max_retries = config[config_section].get('max_retries', 10)
    retry_delay = config[config_section].get('retry_delay', 10)

    return TaskProc(
        base_url=task_url,
        server=server,
        project_name=project,
        username=user_id,
        password=password,
        concurrent_max=concurrent_max,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )