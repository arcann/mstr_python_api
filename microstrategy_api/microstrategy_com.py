"""
NOTE: This COM library can only be loaded by a 32 bit instance of Python
"""
import logging
import re
import sys
from datetime import timedelta, datetime, timezone

import pythoncom
from pywintypes import com_error
from win32com.client import gencache, CastTo

DSSCOMMaster = gencache.EnsureModule('{7E62D941-9778-11D1-A792-00A024D1C490}', 0, 1, 0)
DSSDataSource = DSSCOMMaster.DSSDataSource
IDSSSession = DSSCOMMaster.IDSSSession
IDSSSource = DSSCOMMaster.IDSSSource
IDSSFolder = DSSCOMMaster.IDSSFolder
IDSSSearch = DSSCOMMaster.IDSSSearch
IDSSUser = DSSCOMMaster.IDSSUser

constants = DSSCOMMaster.constants


class MicroStrategyCom(object):
    def __init__(self, server: str, user_id: str, password: str, new_password=None):
        pythoncom.CoInitialize()
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.log.debug('Creating MicroStrategyCom({server},{user_id}'.format(server=server, user_id=user_id))
        if sys.maxsize > 2**32:
            raise RuntimeError("MicroStrategyCom only works on 32bit Python "
                               "due to the MicroStrategy COM API being 32 bit")
        self._object_server = self.get_server_connection(server, user_id, password, new_password=new_password)
        self._session = None
        self._object_source = None
        self._enter_called = False

    def __enter__(self) -> 'MicroStrategyCom':
        self._enter_called = True
        return self

    def __exit__(self, exit_type, exit_value, exit_traceback):
        self.close()

    def get_server_connection(self, server: str, user_id: str, password: str, new_password=None) -> DSSDataSource:
        object_server = DSSDataSource()
        object_server.Type = constants.DssDataSourceTypeServer
        object_server.Location = server
        object_server.Mode = constants.DssConnectionModeServerAccess
        object_server.AuthMode = constants.DssAuthStandard
        object_server.login = user_id
        if password is None:
            raise MicrostrategyConnectionError("Password required")
        object_server.Passwd = password
        if new_password:
            object_server.NewPasswd = new_password
        try:
            object_server.Init()
            self.log.info("Connected")
        except com_error as e:
            self.log.debug('connect exception= {}'.format(e))
            if e.hresult == -2147352567:
                message = e.excepinfo[2]
                if message == '':
                    message = str(e)
                self.log.error('connect error message= "{}"'.format(message))
                raise MicrostrategyConnectionError(str(message))
            else:
                self.log.error("Unexpected result error type")
                self.log.exception(e)
                raise MicrostrategyUnexpectedError("Unexpected error")
        return object_server

    @staticmethod
    def change_password(server: str, user_id: str, old_password: str, new_password: str):
        # Connect and supply new password
        object_server = MicroStrategyCom(server, user_id, old_password, new_password)
        # Disconnect
        object_server.close()

    @property
    def object_server(self):
        return self._object_server

    @property
    def session(self) -> IDSSSession:
        if self._session is None:
            self._session = self.object_server.CreateSession()
        return self._session

    @property
    def object_source(self) -> IDSSSource:
        if self._object_source is None:
            self._object_source = self.object_server.ObjectSource()
        return self._object_source

    def close(self):
        if self._object_server is not None:
            self._object_server.Reset()

    def users_search(self, name_pattern: str=None, id_pattern: str=None) -> IDSSFolder:
        # See usage
        # https://lw.microstrategy.com/msdz/MSDL/104/docs/DevLib/sdk_iserver/api_ref/interface_i_d_s_s_search-members.html
        search = self.object_source.NewObject(Type=constants.DssTypeSearch,
                                              Flags=0,
                                              pUserRuntime=self.session.UserRuntime)
        search = CastTo(search, "IDSSSearch")
        if id_pattern:
            search.AbbreviationPattern = id_pattern
        if name_pattern:
            search.NamePattern = name_pattern
        search.Types.Clear()
        search.Types.Add(constants.DssTypeUser)
        search.Domain = constants.DssSearchConfiguration
        # search.MaxObjects = 1

        # TODO: This gets an error: TypeError: The Python instance can not be converted to a COM object
        results = self.object_source.ExecuteSearch(
            pSearchObject=search,
            FirstObject=0,
            pExistingFolder=0,
            pUserRuntime=self.session.UserRuntime,
            Cookie=0,
            UserData=0
            )
        return results

    def list_groups(self):
        acct_services = self.session.ClientServices.UserAcctSvcs
        groups = acct_services.Groups
        for i in range(1, groups.Count() + 1):
            print(groups.Item(i).Name)

    def list_users(self, id_pattern = None, name_pattern = None):
        acct_services = self.session.ClientServices.UserAcctSvcs
        users = acct_services.Users
        for i in range(1, users.Count() + 1):
            user = users.Item(i)

            match = True
            if id_pattern is not None:
                match = re.search(id_pattern, user.Abbreviation)
            if match and name_pattern is not None:
                match = re.search(name_pattern, user.Abbreviation)

            if match:
                # This returns a IDSSObjectInfo instance and not an IDSSUSer, but it can be cast to one
                userinfo = CastTo(user, "IDSSUser")
                print([user.Name,
                       user.Abbreviation,
                       user.ID,
                       userinfo.UserAccount.Enabled,
                       str(userinfo.UserAccount.PasswordExpirationDate),
                       userinfo.UserAccount.PasswordModifiable]
                      )

    def get_user_account(self, user_id):
        acct_services = self.session.ClientServices.UserAcctSvcs
        users = acct_services.Users
        found = False
        user_id_lower = user_id.lower()
        for i in range(1, users.Count() + 1):
            user = users.Item(i)
            if user.Abbreviation.lower() == user_id_lower:
                user_info = CastTo(user, "IDSSUser")
                self.log.debug("Found {} ID={}".format(user.Name, user.Abbreviation))
                return user, user_info
        if not found:
            raise ValueError("User {} not found".format(user_id))

    def reset_password(self, user_id, new_password, require_new_password=False):
        user, userinfo = self.get_user_account(user_id)
        try:
            user_account_v10 = CastTo(userinfo.UserAccount, "IDSSUserAccount5")
            user_account_v10.SetPassword(new_password)
            freq = user_account_v10.PasswordExpirationFrequency
            if freq > 0:
                self.log.debug("User password delta set to {}".format(freq))
                new_date = datetime.now(timezone(offset=timedelta(0))) + timedelta(days=freq)
                self.log.debug("User password exp date set to {}".format(new_date))
                user_account_v10.PasswordExpirationDate = new_date
            user_account_v10.Enabled = True
            user_account_v10.RequiresNewPassword = require_new_password
            user_account_v10.Info.Save()
        except com_error as e:
            if e.hresult == -2147352567:
                message = e.excepinfo[2]
                raise MicrostrategyPasswordError(message)
            else:
                raise MicrostrategyUnexpectedError(str(e))
        except Exception as e:
            raise MicrostrategyUnexpectedError(str(e))

    def find_object_by_id(self, object_id: str, object_type: int):
        """

        Parameters
        ----------
        object_id:
            The object ID to find
        object_type:
            See constants list here:
            https://lw.microstrategy.com/msdz/MSDL/104/docs/DevLib/sdk_iserver/api_ref/_d_s_s_enum_8idl.html#a3993
            They should be in the constants object

        Returns
        -------
        found_object
        """

        return self.object_source.FindObject(
            object_id,
            object_type,
            # https://lw.microstrategy.com/msdz/MSDL/104/docs/DevLib/sdk_iserver/api_ref/_d_s_s_enum_8idl.html#a4014
            (constants.DssSourceDefn | constants.DssSourceDoNotCache | constants.DssSourceBrowser),
            None,
            0,
            0)


class MicrostrategyConnectionError(Exception):
    pass


class MicrostrategyUnexpectedError(Exception):
    pass


class MicrostrategyPasswordError(Exception):
    pass



