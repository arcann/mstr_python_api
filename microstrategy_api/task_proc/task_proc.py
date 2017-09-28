import re
import urllib.parse


import warnings
from enum import Enum

import time
from fnmatch import fnmatch

from typing import Optional, List

import requests
import logging

from bs4 import BeautifulSoup

from microstrategy_api.task_proc.document import Document
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
        self.log.setLevel(logging.DEBUG)
        if 'TaskProc' in base_url:
            if base_url[-1] != '?':
                base_url += '?'
        self._base_url = base_url
        self.cookies = None
        self.trace = False
        if project_source is not None:
            warnings.warn('project_source parameter is deprecated, use server parameter instead')
            if server is None:
                server = project_source
            else:
                warnings.warn('both project_source deprecated param and server parameter provided!'
                              ' server parameter value used')
        else:
            if server is None:
                raise ValueError('Neither server nor project_source (depracated) parameter provided!')

        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.concurrent_max = concurrent_max
        self.server = server
        self.project_name = project_name
        self.username = username
        self.password = password
        if session_state is None:
            self.login()
        else:
            self._session = session_state

    def __str__(self):
        return 'MstrClient session: {}'.format(self._session)

    def login(self, server: str=None, project_name: str=None, username: str=None, password: str=None):
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
                'taskId':   'getSessionState',
                'server':   self.server,
                'project':  self.project_name,
                'uid':   self.username,
                'pwd': self.password,
                'rws': self.concurrent_max,
            }
        self.log.info("logging in.")
        response = self.request(arguments)
        if self.trace:
            self.log.debug("logging in returned %s" % response)
        # self._session_state = response.find('sessionState')
        self._session = response.find('max-state').string

    @property
    def session(self):
        return self._session

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
            if 'The folder name is unknown to the server.' in e.args[0]:
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
    def path_parts(path):
        # MSTR Paths should use \ separators, however, if the paths starts with / we'll try and use that
        if len(path) == 0:
            return []
        elif path[0] == '/':
            return re.split('[/\\\]', path)
        else:
            return re.split('[\\\]', path)

    def get_folder_contents_by_name(self,
                                    name,
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
                    raise FileNotFoundError("{} not found when processing path {} {}".format(folder_name, name, name_parts))
                else:
                    folder_contents = new_folder_contents
        return folder_contents

    def get_folder_contents(self,
                            name: str,
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
        folder_contents = self.get_folder_contents(folder_name, type_restriction=type_restriction, name_patterns_to_include=object_name)
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

    def get_matching_objects_list(self, path_list: list, type_restriction: set) -> List[FolderObject]:
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


        Returns
        -------
        A list of matching FolderObject
        """
        if isinstance(path_list, str):
            path_list = [path_list]
        result_list = list()
        for path in path_list:
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
                    self.log.warning("Path pattern {} returned no matches".format(path))
                result_list.extend(contents)
            else:
                # Non recursive pass last part as name_patterns_to_include
                path_parts = self.path_parts(path)
                contents = self.get_folder_contents(
                    name=path_parts[:-1],
                    name_patterns_to_include=path_parts[-1],
                    recursive=False,
                    flatten_structure=True,
                    type_restriction=type_restriction,
                )
                if len(contents) == 0:
                    self.log.warning("Path pattern {} returned no matches".format(path))
                result_list.extend(contents)
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

    def check_user_privileges(self, privilege_types="241"):
        arguments = {'taskId': 'checkUserPrivileges',
                     'privilegeTypes': privilege_types,
                     'sessionState':   self._session}
        response = self.request(arguments)
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
        response = self.request(arguments)
        return Attribute(response.find('dssid').string, response.find('n').string)

    def logout(self):
        arguments = {
            'taskId':       'logout',
            'sessionState': self._session,
        }
        arguments.update(BASE_PARAMS)
        result = self.request(arguments)
        self._session = None
        if self.trace:
            self.log.debug("logging out returned %s" % result)

    def request(self, arguments: dict, max_retries: int=None) -> BeautifulSoup:
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
            response = requests.get(request, cookies=self.cookies)
            if self.trace:
                self.log.debug("received response {}".format(response))
            if response.status_code != 200:
                exception = MstrClientException("Server response {response} given for request {request}.".format(
                    response=response.reason,
                    request=request)
                )
            else:
                self.cookies = response.cookies
            result_bs4 = BeautifulSoup(response.text, 'xml')
            task_response = result_bs4.find('taskResponse')
            if task_response['statusCode'] in ['400', '500']:
                self.log.error(response)
                self.log.error(task_response)
                error = task_response['errorMsg']
                exception = MstrClientException("Server error '{error}' given for request {request}.".format(
                    error=error,
                    request=request)
                )
                if 'automatically logged out' in error:
                    self.login()
            if exception is None:
                done = True
            else:
                if tries < max_retries:
                    self.log.debug("Request failed with error {}".format(exception))
                    time.sleep(self.retry_delay)
                    self.log.debug("Retrying. Tries={} < {} max".format(tries, max_retries))
                    tries += 1
                else:
                    raise exception

        return result_bs4
