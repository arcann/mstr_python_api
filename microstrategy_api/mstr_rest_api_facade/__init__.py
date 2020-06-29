import itertools
import json
import logging
import time
from collections import defaultdict
from fnmatch import fnmatch
from typing import List, Union, Optional

import requests

from microstrategy_api.task_proc.object_type import ObjectType

__version__ = '0.1.0'

from microstrategy_api.mstr_rest_api_facade.api_error import APIError
from microstrategy_api.timer import Timer


class MstrRestApiFacade(object):

    # TODO Change REST Call Fails/Errors to raise an exception that can be caught in actual View code

    def __init__(self,
                 mstr_rest_api_base_url,
                 mstr_username,
                 mstr_password,
                 api_version: int = 2,
                 ):

        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        log_level_name = logging.getLevelName(self.log.getEffectiveLevel())
        self.log.info('This modules logging level is {}'.format(log_level_name))
        self.mstr_rest_api_base_url = mstr_rest_api_base_url
        self.mstr_username = mstr_username
        self.mstr_password = mstr_password
        self.mstr_auth_token = None
        self.cookies = None
        self._server_status = None
        self.api_version = int(api_version)

        self.request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-MSTR-AuthToken': None
        }

    def set_cookies(self, cookies):
        self.cookies = cookies

    def set_mstr_auth_token(self, mstr_auth_token):
        self.mstr_auth_token = mstr_auth_token

    def set_request_headers(self, request_headers):
        self.request_headers = request_headers

    @staticmethod
    def _get_response_object(response):
        try:
            return response.json()
        except ValueError:
            # Default to returning None for all values
            return defaultdict(lambda: None)

    def make_request(
            self,
            rest_api_endpoint,
            headers: dict = None,
            query: dict = None,
            data: dict = None,
            method: str = 'get',
    ):
        merged_headers = dict(self.request_headers)
        if headers is not None:
            merged_headers.update(headers)
        if method.lower() == 'get':
            response = requests.get(
                rest_api_endpoint,
                headers=merged_headers,
                params=query,
                data=data,
                cookies=self.cookies,
            )
        elif method.lower() == 'post':
            response = requests.post(
                rest_api_endpoint,
                headers=merged_headers,
                params=query,
                data=data,
                cookies=self.cookies,
            )
        else:
            response = requests.request(
                method=method,
                url=rest_api_endpoint,
                headers=merged_headers,
                params=query,
                data=data,
                cookies=self.cookies,
            )
        json_object = MstrRestApiFacade._get_response_object(response)
        return response, json_object

    @staticmethod
    def error_response(response, json_object):
        return {
            'error_code': json_object["code"],
            'error_message': json_object["message"],
            'http_status_code': response.status_code,
        }

    def get_status(self, refresh: bool = False) -> dict:
        if self._server_status is None or refresh:
            rest_api_endpoint = f'{self.mstr_rest_api_base_url}/status'

            self._server_status = self.make_request_and_handle(
                'get_status',
                rest_api_endpoint,
                raise_exceptions=True,
                disable_error_log=False,
            )
        return self._server_status

    def get_web_version(self) -> str:
        return self.get_status()['webVersion']

    def get_iserver_version(self) -> str:
        return self.get_status()['iServerVersion']

    def get_uptime(self) -> str:
        return self.get_status(refresh=True)['upTimeText']

    def make_request_and_handle(
            self,
            log_name: str,
            rest_api_endpoint: str,
            headers: dict = None,
            query: dict = None,
            data: dict = None,
            method: str = 'get',
            log_message: str = None,
            raise_exceptions: bool = False,
            disable_error_log: bool = False,
            log_pre_call: bool = False,
    ):
        if log_pre_call:
            self.log.debug(
                f'MSTR REST API [{log_name}] Starting. '
                f'Endpoint: {rest_api_endpoint} {log_message}'
            )
        response, json_object = self.make_request(
            rest_api_endpoint,
            headers=headers,
            query=query,
            data=data,
            method=method,
        )
        if log_message is None:
            log_message = ''
        if response.ok:
            self.log.debug(
                f'MSTR REST API [{log_name}] Successful. '
                f'Endpoint: {rest_api_endpoint} {log_message}'
            )
            return json_object

        else:
            if 'message' in json_object:
                mstr_msg = json_object['message']
            else:
                mstr_msg = str(json_object)
            msg = (f'MSTR REST API  [{log_name}] Failed. '
                   f'Endpoint: {rest_api_endpoint} {log_message} {mstr_msg}')
            if not disable_error_log:
                self.log.warning(msg)
            if raise_exceptions:
                raise APIError(f'{msg} {response} {mstr_msg}')
            else:
                return MstrRestApiFacade.error_response(response, json_object)

    def login(self):
        rest_api_endpoint = self.mstr_rest_api_base_url + '/auth/login'

        request_body = {
            "username": self.mstr_username,
            "password": self.mstr_password,
            "loginMode": 1,
            "maxSearch": 1,
            "workingSet": 0,
            "changePassword": False,
            "newPassword": "string",
            "metadataLocale": "en_us",
            "warehouseDataLocale": "en_us",
            "displayLocale": "en_us",
            "messagesLocale": "en_us",
            "numberLocale": "en_us",
            "timeZone": "UTC",
            "applicationType": 35
        }

        login_result_details = {
            'mstr_auth_token': None,
            'http_status_code': None,
            'error_message': None,
            'status': None
        }

        response = requests.post(rest_api_endpoint, data=request_body)

        if response.ok:
            # self.cookies = dict(response.cookies)
            self.cookies = response.cookies
            self.log.debug('MSTR REST API [LOGIN] Successful. Endpoint: ' + rest_api_endpoint)
            self.mstr_auth_token = response.headers['x-mstr-authtoken']
            self.request_headers['X-MSTR-AuthToken'] = self.mstr_auth_token
            login_result_details['mstr_auth_token'] = self.mstr_auth_token
            login_result_details['status'] = 1
        else:
            self.log.info(f"'MSTR REST API [LOGIN] Failed. "
                          f'Endpoint: {rest_api_endpoint}  and Username: {self.mstr_username}. '
                          f"Http Response Code: {response.status_code} {response.text}")
            response_object = response.json()
            login_result_details['error_message'] = response_object["message"]
            login_result_details['status'] = 0

        login_result_details['http_status_code'] = response.status_code

        return login_result_details

    def logout(self):
        # For now 'error_message' is not being used because /auth/logout does not give any useful message error message
        logout_result_details = {
            'http_status_code': None,
            'error_message': None,
            'status': None
        }

        rest_api_endpoint = self.mstr_rest_api_base_url + '/auth/logout'
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)

        if response.ok:
            self.log.info('MSTR REST API [LOGOUT] Successful. '
                          f'Endpoint: {rest_api_endpoint} mstr_auth_token: {self.mstr_auth_token}')
            logout_result_details['status'] = 1

        else:
            self.log.info('MSTR REST API [LOGOUT] Failed. '
                          f'Endpoint: {rest_api_endpoint} mstr_auth_token: {self.mstr_auth_token}')
            logout_result_details['status'] = 0

        logout_result_details['http_status_code'] = response.status_code

        return logout_result_details

    def get_user_info_for_current_session(self):
        mstr_user_info = {
            'mstr_user_id': None,
            'mstr_user_full_name': None,
            'mstr_user_initials': None,
            'http_status_code': None,
            'error_code': None,
            'error_message': None
        }

        rest_api_endpoint = self.mstr_rest_api_base_url + '/sessions/userInfo'
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)

        response_object = MstrRestApiFacade._get_response_object(response)
        if response.ok:
            self.log.debug(
                f'MSTR REST API [/sessions/userInfo] Successful. '
                f'The mstr_auth_token: {self.mstr_auth_token} '
                f' corresponds to live session for mstr_user_id: {response_object["id"]}'
            )

            mstr_user_info['mstr_user_id'] = response_object["id"]
            mstr_user_info['mstr_user_full_name'] = response_object["fullName"]
            mstr_user_info['mstr_user_initials'] = response_object["initials"]

        else:
            self.log.info(
                'MSTR REST API [/sessions/userInfo] Failed. '
                f'mstr_user_id cannot be retrieved for mstr_auth_token: {self.mstr_auth_token}'
            )
            mstr_user_info['error_code'] = response_object["code"]
            mstr_user_info['error_message'] = response_object["message"]

        mstr_user_info['http_status_code'] = response.status_code

        return mstr_user_info

    def get_expiration_info(self, mstr_user_id):
        mstr_user_info = {
            'passwordExpirationDate': None,
            'mstr_user_full_name': None,
            'mstr_userid': None,
            'http_status_code': None,
            'error_code': None,
            'error_message': None
        }

        rest_api_endpoint = self.mstr_rest_api_base_url + '/users/' + mstr_user_id
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)
        response_object = MstrRestApiFacade._get_response_object(response)

        if response.ok:
            self.log.debug('MSTR REST API [/sessions/userInfo] Successful. The mstr user: ' + mstr_user_id)

            mstr_user_info['passwordExpirationDate'] = response_object["passwordExpirationDate"]
            mstr_user_info['mstr_user_full_name'] = response_object["fullName"]
            mstr_user_info['mstr_userid'] = response_object["id"]
        else:
            self.log.info(
                'MSTR REST API [/sessions/userInfo] Failed. '
                f'mstr_user_id cannot be retrieved for mstr user: {mstr_user_id}'
            )
            mstr_user_info['error_code'] = response_object["code"]
            mstr_user_info['error_message'] = response_object["message"]

        mstr_user_info['http_status_code'] = response.status_code

        return mstr_user_info

    def get_user_groups(self, mstr_user_id):
        mstr_user_groups_info = {
            'mstr_user_groups': [],
            'http_status_code': None,
            'error_code': None,
            'error_message': None
        }

        rest_api_endpoint = self.mstr_rest_api_base_url + '/users/' + mstr_user_id
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)
        response_object = MstrRestApiFacade._get_response_object(response)

        if response.ok:
            self.log.debug(
                'MSTR REST API [GET USER GROUPS] Successful. '
                f'Endpoint: {rest_api_endpoint} mstr_user_id: {mstr_user_id}'
            )
            mstr_user_groups_info['mstr_user_groups'] = response_object["memberships"]

        else:
            self.log.info(
                'MSTR REST API [GET USER GROUPS] Failed. '
                f'Endpoint: {rest_api_endpoint} mstr_user_id: {mstr_user_id}'
            )
            mstr_user_groups_info['error_code'] = response_object["code"]
            mstr_user_groups_info['error_message'] = response_object["message"]

        mstr_user_groups_info['http_status_code'] = response.status_code
        return mstr_user_groups_info

    def get_users_in_group(self, mstr_group_id):
        mstr_users_in_group_info = {
            'mstr_users': [],
            'http_status_code': None,
            'error_code': None,
            'error_message': None
        }

        rest_api_endpoint = self.mstr_rest_api_base_url + '/usergroups/' + mstr_group_id + '/members/'
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)
        response_object = MstrRestApiFacade._get_response_object(response)

        if response.ok:
            self.log.debug(
                'MSTR REST API [GET USERS IN GROUP] Successful. '
                f'Endpoint: {rest_api_endpoint} mstr_group_id: {mstr_group_id}'
            )
            mstr_users_in_group_info['mstr_users'] = response_object

        else:
            self.log.info(
                'MSTR REST API [GET USERS IN GROUP] Failed. '
                f'Endpoint: {rest_api_endpoint} mstr_group_id: {mstr_group_id}'
            )
            mstr_users_in_group_info['error_code'] = response_object["code"]
            mstr_users_in_group_info['error_message'] = response_object["message"]

        mstr_users_in_group_info['http_status_code'] = response.status_code
        return mstr_users_in_group_info

    def disable_user(self, mstr_id):
        mstr_users_in_group_info = {
            'mstr_users': [],
            'http_status_code': None,
            'error_code': None,
            'error_message': None
        }

        request_body = {
            "operationList": [
                {
                    "op": "replace",
                    "path": "/enabled",
                    "value": False
                }
            ]
        }

        request_as_json = json.dumps(request_body)

        rest_api_endpoint = self.mstr_rest_api_base_url + '/users/' + mstr_id
        response = requests.patch(
            rest_api_endpoint,
            headers=self.request_headers,
            cookies=self.cookies,
            data=request_as_json
        )
        response_object = MstrRestApiFacade._get_response_object(response)

        if response.ok:
            self.log.debug(
                'MSTR REST API [DISABLE USER] Successful. '
                f'Endpoint: {rest_api_endpoint}  mstr_id: {mstr_id}'
            )
            mstr_users_in_group_info['mstr_users'] = response_object

        else:
            self.log.info(
                'MSTR REST API [DISABLE USER] Failed. '
                f'Endpoint: {rest_api_endpoint}  mstr_id: {mstr_id}'
            )
            mstr_users_in_group_info['error_code'] = response_object["code"]
            mstr_users_in_group_info['error_message'] = response_object["message"]

        mstr_users_in_group_info['http_status_code'] = response.status_code
        return mstr_users_in_group_info

    def is_user_in_group(self, mstr_user_id, user_group_name):
        rest_api_endpoint = self.mstr_rest_api_base_url + '/users/' + mstr_user_id
        response = requests.get(rest_api_endpoint, headers=self.request_headers, cookies=self.cookies)
        response_object = MstrRestApiFacade._get_response_object(response)

        if response.ok:
            self.log.debug(
                'MSTR REST API [IS USER IN GROUP] Successful. '
                f'Endpoint: {rest_api_endpoint} mstr_user_id: {mstr_user_id}'
            )
            mstr_user_groups = response_object["memberships"]

            self.log.debug(
                f'Verifying whether user with mstr_user_id: {mstr_user_id} is in group_name: {user_group_name}'
            )
            for user_group in mstr_user_groups:
                if user_group.get("name") == user_group_name:
                    return True
        else:
            self.log.info(
                'MSTR REST API [IS USER IN GROUP] Failed. '
                f'Endpoint: {rest_api_endpoint} mstr_user_id: {mstr_user_id} group_name: {user_group_name}'
            )
            return False

        return False

    # If this method returns 'None' (null) then the validate_session did not succeed
    @staticmethod
    def validate_session(mstr_rest_api_url, cookies):
        # current_session_details = {
        #     'http_status_code': None,
        #     'status': None,
        #     'mstr_user_id': None,
        #     'mstr_user_full_name': None,
        #     'mstr_user_initials': None,
        #     'error_code': None,
        #     'error_message': None
        # }
        log = logging.getLogger("forms.mstr_auth_svc_rest.mstr_rest_api_facade.MstrRestApiFacade.validate_session")

        if len(cookies) < 1:
            return None
            # current_session_details['status'] = 0
            # current_session_details['error_message'] = 'No Cookies have been provided to validate session using REST API'
            # return current_session_details

        cookie_keys_list = dict(cookies).keys()

        if 'mstrAuthToken' not in cookie_keys_list or 'JSESSIONID' not in cookie_keys_list or 'iSession' not in cookie_keys_list:
            return None
            # current_session_details['status'] = 0
            # current_session_details['error_message'] = '1 or more cookies missing (and needed) to validate session using REST API'
            # return current_session_details

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-MSTR-AuthToken': cookies['mstrAuthToken']
        }

        rest_api_endpoint = mstr_rest_api_url + '/sessions'
        response = requests.get(rest_api_endpoint, headers=headers, cookies=cookies)

        if response.ok:
            log.debug('MSTR REST API [VALIDATE SESSION] Successful. mstr_auth_token: ' + cookies[
                'mstrAuthToken'] + ' corresponds to a live session')
            # current_session_details['status'] = 1
            # current_session_details['mstr_user_id'] = json.loads(response.text)["id"]
            # current_session_details['mstr_user_full_name'] = json.loads(response.text)["fullName"]
            # current_session_details['mstr_user_initials'] = json.loads(response.text)["initials"]

            # TODO Make sure we are seeing the id, fullName, and initials in the response before creating this object
            mstr_rest_facade_object = MstrRestApiFacade(mstr_rest_api_url, None, None)
            mstr_rest_facade_object.set_cookies(cookies)
            mstr_rest_facade_object.set_mstr_auth_token(cookies['mstrAuthToken'])
            mstr_rest_facade_object.set_request_headers(headers)
            return mstr_rest_facade_object

        else:
            log.info('MSTR REST API [VALIDATE SESSION] Failed. mstr_auth_token: ' + cookies[
                'mstrAuthToken'] + ' DOES NOT correspond to a live session')
            return None

    def get_folder_contents(self, project_id, folder_id: str = None, raise_exceptions: bool = False) -> List[dict]:
        if folder_id is not None:
            rest_api_endpoint = f'{self.mstr_rest_api_base_url}/folders/{folder_id}'
        else:
            rest_api_endpoint = f'{self.mstr_rest_api_base_url}/folders'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }

        log_message = f'project_id = {project_id} folder_id = {folder_id}'

        return self.make_request_and_handle(
            'get_folder_contents',
            rest_api_endpoint,
            headers=headers,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
        )

    def get_predefined_folder_contents(
            self,
            project_id,
            folder_type: str,
            raise_exceptions: bool = False
    ) -> List[dict]:
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/folders/preDefined/{folder_type}'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }

        log_message = f'project_id = {project_id} folder_type = {folder_type}'

        return self.make_request_and_handle(
            'get_predefined_folder_contents',
            rest_api_endpoint,
            headers=headers,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
        )

    def get_my_personal_folder(self, project_id, raise_exceptions: bool = False) -> List[dict]:
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/folders/myPersonalObjects'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }

        log_message = f'project_id = {project_id}'

        return self.make_request_and_handle(
            'get_my_personal_folder',
            rest_api_endpoint,
            headers=headers,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
        )

    def list_projects(self, raise_exceptions: bool = False) -> List[dict]:
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/projects'

        return self.make_request_and_handle(
            'List Projects',
            rest_api_endpoint,
            raise_exceptions=raise_exceptions,
        )

    def get_project_by_name(
            self,
            project_name,
            raise_exceptions: bool = True,
            disable_error_log: bool = False
    ) -> dict:
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/projects/{project_name}'

        log_message = f'project_name = {project_name}'

        return self.make_request_and_handle(
            'get_project_by_name',
            rest_api_endpoint,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
        )

    @staticmethod
    def path_parts(path) -> List[str]:
        # MSTR Paths should use \ separators, however, if the paths starts with / we'll try and use that
        if len(path) == 0:
            return []
        elif path[0] == '/':
            return path.split('/')
        else:
            return path.split('\\')

    def get_project_id(
            self,
            project_id: str = None,
            project_name: str = None,
            raise_exceptions: bool = True,
    ):
        if project_id is None:
            if project_name is None:
                raise ValueError('method requires either project_id or project_name')
            project_info = self.get_project_by_name(
                project_name=project_name,
                raise_exceptions=raise_exceptions,
                disable_error_log=True,
            )
            project_id = project_info['id']
        return project_id

    def get_objects_by_path(
            self,
            object_path: Union[str, List[str]],
            project_id: str = None,
            project_name: str = None,
            type_restriction: Optional[set] = None,
            subtype_restriction: Optional[set] = None,
            name_patterns_to_include: Optional[List[str]] = None,
            name_patterns_to_exclude: Optional[List[str]] = None,
            raise_exceptions: bool = False,
    ) -> list:

        project_id = self.get_project_id(project_id, project_name)

        if isinstance(object_path, str):
            name_parts = MstrRestApiFacade.path_parts(object_path)
        else:
            # Blindly assume it's an iterable type
            name_parts = object_path

        if isinstance(type_restriction, str):
            type_restriction = set(type_restriction.split(','))
        if isinstance(subtype_restriction, str):
            subtype_restriction = set(subtype_restriction.split(','))
        if isinstance(name_patterns_to_include, str):
            name_patterns_to_include = [name_patterns_to_include]
        if isinstance(name_patterns_to_exclude, str):
            name_patterns_to_exclude = [name_patterns_to_exclude]

        folder_contents = self.get_folder_contents(project_id=project_id, raise_exceptions=raise_exceptions)

        path_so_far = list()
        for folder_name in name_parts:
            if folder_name == '':
                pass
            else:
                found = False
                new_folder_contents = None
                for sub_folder in folder_contents:
                    if sub_folder['name'] == folder_name:
                        found = True
                        if sub_folder['type'] == ObjectType.Folder.value:
                            new_folder_contents = self.get_folder_contents(
                                project_id=project_id,
                                folder_id=sub_folder['id'],
                                raise_exceptions=raise_exceptions,
                            )
                        else:
                            new_folder_contents = [sub_folder]
                if not found:
                    name_list = [folder['name'] for folder in folder_contents]
                    raise FileNotFoundError(f"{folder_name} not found when processing path {object_path}. "
                                            f"At /{'/'.join(path_so_far)}. "
                                            f"objects are: {name_list}")
                folder_contents = new_folder_contents
                path_so_far.append(folder_name)

        if type_restriction is not None:
            folder_contents = [folder for folder in folder_contents if folder['type'] in type_restriction]
        if subtype_restriction is not None:
            folder_contents = [folder for folder in folder_contents if folder['subtype'] in subtype_restriction]
        if name_patterns_to_include is not None:
            matched_folders = list()
            for folder in folder_contents:
                for include_pattern in name_patterns_to_include:
                    if fnmatch(folder['name'].lower(), include_pattern.lower()):
                        matched_folders.append(folder)
                        break
            folder_contents = matched_folders
        if name_patterns_to_exclude is not None:
            matched_folders = list()
            for folder in folder_contents:
                for exclude_pattern in name_patterns_to_exclude:
                    if not fnmatch(folder['name'].lower(), exclude_pattern.lower()):
                        matched_folders.append(folder)
                        break
            folder_contents = matched_folders

        return folder_contents

    def get_report_definition(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            raise_exceptions: bool = False,
            disable_error_log: bool = False
    ) -> dict:
        """
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:
        :param raise_exceptions:
        :param disable_error_log:
        :return:

        {'name': 'Report Name',
        'id': '5075CDA44620BA93A033ADBF090EF6E5',
        'definition': {
            'grid': {
                'crossTab': True,
                'metricsPosition': {'axis': 'rows', 'index': 2},
                'pageBy': [...]
                'sorting': [...]
                'thresholds': [...]
                'rows': [
                    {'name': 'Operating Unit',
                     'id': '7039371C4B5CC07DC6682D9C0EC8F45C',
                     'type': 'attribute',
                     'forms': [
                            {
                            'id': 'CCFBE2A5EADB4F50941FB879CCF1721C',
                            'name': 'DESC',
                            'dataType': 'varChar',
                            'baseFormCategory': 'DESC',
                            'baseFormType': 'text'
                            }
                        ]
                    },
                    {
                       'name': 'Metrics',
                       'id': '00000000000000000000000000000000',
                       'type': 'templateMetrics',
                       'elements': [
                            {'name': 'Value',
                             'id': '5F1CEBF741FA1B19F3187D96FD747DD9',
                             'type': 'metric',
                             'dataType': 'reserved'
                             },
                             {'name': 'Target',
                              'id': '595F0F224E9886FEFE09FE939E5FDF4E',
                              'type': 'metric',
                              'dataType': 'reserved'
                              },
                             ...
                       ]
                    }
                    ...
                ]
                'columns': [
                    ...
                ]
            'availableObjects': {
                'attributes': [ { see example from grid.row 1 above } ],
                'metrics': [ { see example from grid row 2 above } ],
                'customGroups': [],
                'consolidations': [],
                'hierarchies': []
                }
            } # End of definition
        }
        """

        project_id = self.get_project_id(project_id, project_name)

        if report_id is None:
            if report_path is None:
                raise ValueError('get_report_definition requires either report_id or report_path')
            else:
                object_list = self.get_objects_by_path(project_id=project_id, object_path=report_path)
                if len(object_list) != 1:
                    raise ValueError(f'get_report_definition found {len(object_list)} objects at {report_path}')
                else:
                    report_id = object_list[0]['id']

        # Note: Requires MSTR 2020 for v2 support
        if self.api_version >= 2:
            version = 'v2'
        else:
            version = ''
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/{version}/reports/{report_id}'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }

        log_message = f'project_id = {project_id} report_id = {report_id} report_path={report_path}'

        return self.make_request_and_handle(
            'get_report_definition',
            rest_api_endpoint,
            headers=headers,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
        )

    def create_report_instance(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            filters: dict = None,
            offset: int = 0,
            limit: int = None,
            raise_exceptions: bool = False,
            disable_error_log: bool = False
    ) -> dict:
        """

        :param limit:
        :param offset:
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:
        :param filters:
        :param raise_exceptions:
        :param disable_error_log:
        :return:

        {
            'id': '5075CDA44620BA93A033ADBF090EF6E5',
            'status': 2,
            'instanceId': '77440EB443B2B1987B65A7B9ED0A9B29'
        }
        """
        project_id = self.get_project_id(project_id, project_name)

        if report_id is None:
            if report_path is None:
                raise ValueError('run_report requires either report_id or report_path')
            else:
                object_list = self.get_objects_by_path(project_id=project_id, object_path=report_path)
                if len(object_list) != 1:
                    raise ValueError(f'get_report_definition found {len(object_list)} objects at {report_path}')
                else:
                    report_id = object_list[0]['id']

        if limit is None:
            limit = 5000

        # Note: Requires MSTR 2020 for v2 support
        if self.api_version >= 2:
            version = 'v2'
        else:
            version = ''
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/{version}/reports/{report_id}/instances'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }
        query = {
            'offset': offset,
            'limit': limit,
        }

        log_message = f'project_id = {project_id} report_id = {report_id} report_path={report_path}'

        return self.make_request_and_handle(
            'create_report_instance',
            rest_api_endpoint,
            method='post',
            headers=headers,
            query=query,
            data=filters,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
            log_pre_call=True,
        )

    def get_report_instance_data(
            self,
            project_id: str,
            report_id: str,
            instance_id: str,
            filters: dict = None,
            offset: int = 0,
            limit: int = None,
            raise_exceptions: bool = False,
            disable_error_log: bool = False
    ) -> dict:

        if limit is None:
            limit = 10**9

        log_message = f'project_id = {project_id} instance_id = {instance_id} offset={offset} limit={limit}'

        # Note: Requires MSTR 2020 for v2 support
        if self.api_version >= 2:
            version = 'v2'
        else:
            version = ''
        rest_api_endpoint = f'{self.mstr_rest_api_base_url}/{version}/reports/{report_id}/instances/{instance_id}'

        headers = {
            'X-MSTR-ProjectID': project_id,
        }

        query = {
            'offset': offset,
            'limit': limit,
        }

        return self.make_request_and_handle(
            'get_report_instance_data',
            rest_api_endpoint,
            query=query,
            headers=headers,
            data=filters,
            log_message=log_message,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
            log_pre_call=True,
        )

    def run_report_raw(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            filters: dict = None,
            limit: int = 1000,
            offset: int = None,
            time_limit_seconds: int = 600,
            raise_exceptions: bool = False,
            disable_error_log: bool = False
    ) -> dict:
        """

        :param raise_exceptions:
        :param offset:
        :param limit:
        :param time_limit_seconds:
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:
        :param filters:
        :param disable_error_log:
        :return:

        {
            'name': 'Expenditure and Budget Dataset - DW',
            'id': '7CA05F0B4766A661ED9C64A2C2392B32',
            'instanceId': '2156F95C42562E219E3BA28A8053FF67',
            'status': 1,
            'definition': { see get_report_definition },
            'data':  {
                'currentPageBy: [],
                'paging: {'total': 1750, 'current': 1750, 'offset': 0, 'limit': 5000}
                'headers: {
                    'rows': [
                        [0, 0],
                        [0, 1],
                        [0, 2],
                        ...
                    'columns': [
                        [0,0,0,1,1,1,2,2,2],
                        [1,2,3,1,2,3,1,2,3]
                        ]
                'metricValues': {
                    'raw': [
                        [None,  304000.0,  None,  None,  None],
                        ...

                    ],
                    'formatted': [
                        ['',  '$304,000',  '',  '',  ''],
                        ...
                    ],
                    'extras': [{},{},{},{}]
                }
            }

            }

        """
        project_id = self.get_project_id(
            project_id=project_id,
            project_name=project_name,
            raise_exceptions=raise_exceptions,
        )

        instance_results = self.create_report_instance(
            project_id=project_id,
            report_path=report_path,
            report_id=report_id,
            filters=filters,
            limit=limit,
            offset=offset,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
        )
        # Add the project ID in case the caller needs it
        instance_results['project_id'] = project_id
        instance_id = instance_results['instanceId']
        report_id = instance_results['id']

        if instance_results['status'] == '2':
            # TODO: Supply if we have prompt answers
            # /api/reports/{reportId}/instances/{instanceId}/prompts/answers
            # TODO: It would be nice to cancel report if no answers available, but API doesn't seem to include that yet
            raise ValueError('Report needs prompt answers')

        time_waited = 0
        sleep_interval = 2
        # Wait for the report to finish, if it has not
        while not instance_results['status'] == 1:
            if time_waited > time_limit_seconds:
                raise TimeoutError(f"Timeout after {time_waited} seconds")
            instance_results = self.get_report_instance_data(
                    project_id=project_id,
                    report_id=report_id,
                    instance_id=instance_id,
                    limit=limit,
                    offset=offset,
                    raise_exceptions=raise_exceptions,
                )
            time.sleep(sleep_interval)
            time_waited += sleep_interval
        return instance_results

    def run_report_raw_all_data(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            filters: dict = None,
            chuck_size: int = 10**9,
            time_limit_seconds: int = 600,
            raise_exceptions: bool = False,
            disable_error_log: bool = False,
    ) -> dict:
        """

        :param raise_exceptions:
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:
        :param filters:
        :param filters:
                {
                  "requestedObjects": {
                    "attributes": [
                      {
                        "id": "8D679D3511D3E4981000E787EC6DE8A4"
                      },
                      {
                        "id": "8D679D3711D3E4981000E787EC6DE8A4"
                      }
                    ],
                    "metrics": [
                      {
                        "id": "4C051DB611D3E877C000B3B2D86C964F"
                      }
                    ]
                  },
                  "viewFilter": {
                    "operator": "And",
                    "operands": [
                      {
                        "operator": "In",
                        "operands": [
                          {
                            "type": "attribute",
                            "id": "8D679D3711D3E4981000E787EC6DE8A4",
                            "name": "Category"
                          },
                          {
                            "type": "elements",
                            "elements": [
                              {
                                "name": "Electronics",
                                "id": "8D679D3711D3E4981000E787EC6DE8A4:2"
                              },
                              {
                                "name": "Movies",
                                "id": "8D679D3711D3E4981000E787EC6DE8A4:3"
                              }
                            ]
                          }
                        ]
                      }
                    ]
                  },
                  "metricLimits": {
                    "4C051DB611D3E877C000B3B2D86C964F": {
                      "operator": "And",
                      "operands": [
                        {
                          "operator": "Greater",
                          "operands": [
                            {
                              "type": "metric",
                              "id": "4C051DB611D3E877C000B3B2D86C964F",
                              "name": "Profit"
                            },
                            {
                              "type": "constant",
                              "dataType": "Real",
                              "value": "123"
                            }
                          ]
                        }
                      ]
                    }
                  }
                }
        :param chuck_size:
        :param time_limit_seconds:
        :param disable_error_log:
        :return:
        """
        offset = 0

        project_id = self.get_project_id(
            project_id=project_id,
            project_name=project_name,
            raise_exceptions=raise_exceptions,
        )

        main_results_instance = self.run_report_raw(
            project_id=project_id,
            report_path=report_path,
            report_id=report_id,
            filters=filters,
            limit=chuck_size,
            offset=offset,
            time_limit_seconds=time_limit_seconds,
            raise_exceptions=raise_exceptions,
            disable_error_log=disable_error_log,
        )
        report_id = main_results_instance['id']

        total_rows = main_results_instance['data']['paging']['total']
        total_rows_downloaded = main_results_instance['data']['paging']['current']

        del main_results_instance['data']['paging']['current']

        if total_rows_downloaded != len(main_results_instance['data']['headers']['rows']):
            raise ValueError(f"REST API Error.  "
                             f"Got {len(main_results_instance['data']['headers']['rows'])} row header records "
                             f"but expected {total_rows_downloaded} in this pass")

        if total_rows_downloaded != len(main_results_instance['data']['headers']['rows']):
            raise ValueError(f"REST API Error.  "
                             f"Got {len(main_results_instance['data']['metricValues']['raw'])} metric value records "
                             f"but expected {total_rows_downloaded} in this pass")

        if total_rows_downloaded != len(main_results_instance['data']['headers']['rows']):
            raise ValueError(f"REST API Error.  "
                             f"Got {len(main_results_instance['data']['metricValues']['formatted'])} "
                             f"metric formatted value records "
                             f"but expected {total_rows_downloaded} in this pass")

        while total_rows_downloaded < total_rows:
            raise APIError(
                f'The report contains {total_rows} rows '
                f'and {chuck_size} is the maximum this API can process.'
            )

            # TODO: The main_results_instance['definition']['grid']['rows'] and
            #           next_results_instance['definition']['grid']['rows'] do not have to match
            #       So in order to properly process the next chunk we need to turn element numbers
            #       into actual lists of form values for each chunk independently before appending new rows.
            #       The same is true of results_instance['definition']['grid']['colmns']
            #       and results_instance['data']['headers']['columns']
            #       Which also means that if any attributes are in columns, the total report may have more
            #       columns than any given chunk.

            # offset += chuck_size
            # next_results_instance = self.get_report_instance_data(
            #         project_id=project_id,
            #         report_id=report_id,
            #         instance_id=main_results_instance['instanceId'],
            #         raise_exceptions=raise_exceptions,
            #         limit=chuck_size,
            #         offset=offset,
            #     )
            # total_rows_downloaded += next_results_instance['data']['paging']['current']
            #
            # for row_header_num, main_row_header_defn in enumerate(main_results_instance['definition']['grid']['rows']):
            #     next_row_header_defn = next_results_instance['definition']['grid']['rows'][row_header_num]
            #     if main_row_header_defn['name'] != next_row_header_defn['name']:
            #         raise ValueError(f"Initial chunk row header {row_header_num} "
            #                          f"was '{main_row_header_defn['name']}' vs "
            #                          f"next chunk with '{main_row_header_defn['name']}'"
            #                          )
            #     main_element_set = set(tuple([tuple(element['formValues']) for element in main_row_header_defn['elements']]))
            #     next_element_set = set(tuple([tuple(element['formValues']) for element in next_row_header_defn['elements']]))
            #     diff_1 = main_element_set - next_element_set
            #     diff_2 = next_element_set - main_element_set
            #     if len(diff_1) > 0 or len(diff_2) > 0:
            #         raise ValueError(f"Initial chunk row header {row_header_num} "
            #                          f"was {len(main_element_set)} elements vs "
            #                          f"next chunk with {len(next_element_set)} elements"
            #                          f"first A-B diffs = {list(diff_1)[0:10]}"
            #                          f"first B-A diffs = {list(diff_2)[0:10]}"
            #                          )
            #
            # main_results_instance['data']['headers']['rows'].extend(
            #     next_results_instance['data']['headers']['rows'])
            # main_results_instance['data']['metricValues']['raw'].extend(
            #     next_results_instance['data']['metricValues']['raw'])
            # main_results_instance['data']['metricValues']['formatted'].extend(
            #     next_results_instance['data']['metricValues']['formatted'])

        return main_results_instance

    @staticmethod
    def _get_column_names(pivot_entry: dict) -> list:
        if pivot_entry['type'] == 'attribute':
            return [f"{pivot_entry['name']} {form['name']}" for form in pivot_entry['forms']]
        else:
            return [pivot_entry['name']]

    @staticmethod
    def _get_column_headers(results_instance: dict) -> list:
        header_cols = []
        for row_header in results_instance['definition']['grid']['rows']:
            header_cols.extend(MstrRestApiFacade._get_column_names(row_header))

        # Process values pivoted to columns
        column_list = []
        # Note the zip function takes the multiple lists of values and pivots them into 1 row per column
        for col_element_values in zip(*results_instance['data']['headers']['columns']):
            column_name_parts = []
            for col_object_num, col_element_value in enumerate(col_element_values):
                col_object_defn = results_instance['definition']['grid']['columns'][col_object_num]
                if col_object_defn['type'] == 'attribute':
                    # Note: We use [0] meaning we use the first form only of any attributes
                    # print(col_object_defn['name'], col_object_defn['elements'][col_element_value]['formValues'][0])
                    column_name_parts.append(col_object_defn['elements'][col_element_value]['formValues'][0])
                else:
                    # print(col_object_defn['name'], col_object_defn['elements'][col_element_value]['name'])
                    column_name_parts.append(col_object_defn['elements'][col_element_value]['name'])
            # Join together the parts of the name using spaces
            column_list.append(' '.join(column_name_parts))
        header_cols.extend(column_list)

        return header_cols

    @staticmethod
    def _csv_quote(entry: str, escape: bool) -> str:
        if entry is None:
            return ''
        if isinstance(entry, str):
            if escape:
                entry = entry.replace('"', '""')
            else:
                entry = entry.replace('"', '')
        return f'"{entry}"'

    @staticmethod
    def _csv_quote_list(entries: list, escape: bool) -> list:
        return [MstrRestApiFacade._csv_quote(e, escape) for e in entries]

    def run_report_csv(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            filters: dict = None,
            delimiter: str = ',',
            get_formatted: bool = False,
            escape: bool = True,
            time_limit_seconds: int = 600,
            disable_error_log: bool = False
    ) -> str:
        """
        :param filters:
        :param get_formatted:
        :param escape:
        :param delimiter:
        :param time_limit_seconds:
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:

        :param disable_error_log:
        :return:

        csv results
        """

        timer = Timer('REST api calls')

        try:
            results_instance = self.run_report_raw_all_data(
                project_id=project_id,
                project_name=project_name,
                report_path=report_path,
                report_id=report_id,
                filters=filters,
                time_limit_seconds=time_limit_seconds,
                disable_error_log=disable_error_log,
                raise_exceptions=True,
            )
            self.log.info(timer.message())

            timer = Timer('CSV formatting calls')

            result_lines = []

            # Header row
            header_cols = MstrRestApiFacade._get_column_headers(results_instance)
            header_cols = MstrRestApiFacade._csv_quote_list(header_cols, escape)
            result_lines.append(delimiter.join(header_cols))

            header_row_cnt = len(results_instance['data']['headers']['rows'])
            metric_values_cnt = len(results_instance['data']['metricValues']['raw'])
            if header_row_cnt != metric_values_cnt:
                raise ValueError(f'Error from REST API. '
                                 f'We got {header_row_cnt} header rows and {metric_values_cnt} metric value rows')

            # Data rows
            for row_number, data_row in enumerate(results_instance['data']['headers']['rows']):
                row_value_list = []

                # TODO: Handle Page By. We could at least pre-pend the intial page values to each row
                #       For now it's best to use datasets with no page by attributes
                # rslt_all['data']['currentPageBy']
                # rslt_all['definition']['grid']['pageBy'][0]['elements'][44]['formValues']

                for row_header_num, row_header_element_num in enumerate(data_row):
                    row_header_defn = results_instance['definition']['grid']['rows'][row_header_num]
                    row_header_entry = row_header_defn['elements'][row_header_element_num]
                    if 'formValues' in row_header_entry:
                        values = row_header_entry['formValues']
                    else:
                        values = [row_header_entry['name']]
                    row_value_list.extend(values)
                if get_formatted:
                    row_value_list.extend(results_instance['data']['metricValues']['formatted'][row_number])
                else:
                    row_value_list.extend(results_instance['data']['metricValues']['raw'][row_number])
                row_value_list = MstrRestApiFacade._csv_quote_list(row_value_list, escape)
                result_lines.append(delimiter.join(row_value_list))

            self.log.info(timer.message())

            return '\n'.join(result_lines)
        except APIError as e:
            return f'Error: {e}'

    def get_report_definition_csv(
            self,
            project_id: str = None,
            project_name: str = None,
            report_path: str = None,
            report_id: str = None,
            delimiter: str = ',',
            disable_error_log: bool = False
    ) -> str:
        """
        :param delimiter:
        :param project_id:
        :param project_name:
        :param report_path:
        :param report_id:

        :param disable_error_log:
        :return:

        csv results
        """

        try:
            full_report_definition = self.get_report_definition(
                project_id=project_id,
                project_name=project_name,
                report_path=report_path,
                report_id=report_id,
                disable_error_log=disable_error_log,
                raise_exceptions=True,
            )
            report_definition = full_report_definition['definition']

            result_lines = [delimiter.join(['Pivot', 'Type', 'Name'])]

            for page_by_val in report_definition['grid']['pageBy']:
                for sub_header in self._get_column_names(page_by_val):
                    result_lines.append(delimiter.join(['pageBy_NOT_SENT_TO_CSV', page_by_val['type'], sub_header]))

            for row_header in report_definition['grid']['rows']:
                for sub_header in self._get_column_names(row_header):
                    result_lines.append(delimiter.join(['row', row_header['type'], sub_header]))

            all_col_options = []
            col_types = []
            for column in report_definition['grid']['columns']:
                col_types.append(column['type'])
                if column['type'] == 'attribute':
                    # Note: We use [0] meaning we use the first form only of any attributes
                    this_col_options = [f"<{column['name']} {column['forms'][0]['name']}>"]
                else:
                    this_col_options = [sub_element['name'] for sub_element in column['elements']]
                all_col_options.append(this_col_options)

            for combination in itertools.product(*all_col_options):
                result_lines.append(delimiter.join([
                    'column',
                    ' '.join(col_types),
                    ' '.join(combination),
                ]))

            return '\n'.join(result_lines)
        except APIError as e:
            return f'Error: {e}'