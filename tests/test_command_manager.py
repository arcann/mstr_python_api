import textwrap
import unittest
from unittest import mock

import subprocess

import microstrategy_api.command_manager


class TestCommandManager(unittest.TestCase):

    def setUp(self):
        self.project_source = 'test'
        self.connect_user_id = 'test_user'
        self.connect_password = 'Pass123'

    def test_init_no_args(self):
        self.assertRaises(ValueError,
                          microstrategy_api.command_manager.CommandManager)

    def test_init_no_password(self):
        self.assertRaises(ValueError,
                          microstrategy_api.command_manager.CommandManager,
                          {'project_source': 'test',
                           'connect_user_id': 'test_user',
                           })

    def _get_cmd(self):
        return microstrategy_api.command_manager.CommandManager(
            project_source=self.project_source,
            connect_user_id=self.connect_user_id,
            connect_password=self.connect_password,
        )

    def test_init_good(self):
        cmd = self._get_cmd()
        self.assertEquals(cmd.project_source, self.project_source)
        self.assertEquals(cmd.connect_user_id, self.connect_user_id)
        self.assertEquals(cmd.connect_password, self.connect_password)

    def test_execute_nothing(self):
        cmd = self._get_cmd()
        with mock.patch('microstrategy_api.command_manager.subprocess.check_output') as check_output:
            with mock.patch('microstrategy_api.command_manager.open',
                            mock.mock_open(read_data=''),
                            create=True):
                cmd.execute("test script code")

    def test_execute_noresults(self):
        cmd = self._get_cmd()
        read_data = textwrap.dedent("""\
        3/15/17 12:25:02 PM EDT Version 10.0.0 (Build 10.0.0000.0000)
        3/15/17 12:25:03 PM EDT Connected:user_id@project_source
        3/15/17 12:25:03 PM EDT Executing task(s)...
        3/15/17 12:25:03 PM EDT Checking syntax...
        3/15/17 12:25:03 PM EDT Syntax is correct.
        3/15/17 12:25:03 PM EDT Syntax checking has been completed.
        3/15/17 12:25:03 PM EDT Successfully disconnected. (MSTR) project_source: user_id
        3/15/17 12:25:03 PM EDT No results returned.
        3/15/17 12:25:03 PM EDT Task(s) execution completed successfully.
        3/15/17 12:25:03 PM EDT Execution Time: 00:00:01
        ###################################################################

        """)
        with mock.patch('microstrategy_api.command_manager.subprocess.check_output'):
            with mock.patch('microstrategy_api.command_manager.open',
                            mock.mock_open(read_data=read_data),
                            create=True):
                results = cmd.execute("test script code", return_output=True)
                self.assertEquals(results,[])

    def test_execute_pw_error(self):
        cmd = self._get_cmd()
        read_data = textwrap.dedent("""\
        3/15/17 12:31:34 PM EDT Version 10.4.0 (Build 10.4.0026.0049)
        3/15/17 12:31:34 PM EDT Connected:password_change_tool@development
        3/15/17 12:31:34 PM EDT Executing task(s)...
        3/15/17 12:31:34 PM EDT Checking syntax...
        3/15/17 12:31:34 PM EDT Syntax is correct.
        3/15/17 12:31:34 PM EDT Syntax checking has been completed.
        3/15/17 12:31:34 PM EDT (You do not have Monitor Cluster privilege that is required to perform the task.)
        3/15/17 12:31:34 PM EDT No results returned.
        3/15/17 12:31:34 PM EDT Task(s) execution completed with errors.
        3/15/17 12:31:34 PM EDT Execution Time: 00:00:00
        3/15/17 12:31:35 PM EDT Successfully disconnected. (MSTR) development: password_change_tool
        ###################################################################


        """)
        with mock.patch('microstrategy_api.command_manager.subprocess.check_output') as check_output:
            with mock.patch('microstrategy_api.command_manager.open',
                            mock.mock_open(read_data=read_data),
                            create=True):
                check_output.side_effect = subprocess.CalledProcessError(
                    returncode=4,
                    cmd='',
                    output='Incorrect login/password.'.encode('ascii')
                    )
                try:
                    cmd.execute("test script code", return_output=True)
                    self.fail('CommandManagerException not raised')
                except microstrategy_api.command_manager.CommandManagerException as e:
                    self.assertIn('Incorrect login/password.', e.args[0])

    def test_execute_perm_error(self):
        cmd = self._get_cmd()
        read_data = textwrap.dedent("""\
        3/15/17 12:31:34 PM EDT Version 10.4.0 (Build 10.4.0026.0049)
        3/15/17 12:31:34 PM EDT Connected:password_change_tool@development
        3/15/17 12:31:34 PM EDT Executing task(s)...
        3/15/17 12:31:34 PM EDT Checking syntax...
        3/15/17 12:31:34 PM EDT Syntax is correct.
        3/15/17 12:31:34 PM EDT Syntax checking has been completed.
        3/15/17 12:31:34 PM EDT (You do not have Monitor Cluster privilege that is required to perform the task.)
        3/15/17 12:31:34 PM EDT No results returned.
        3/15/17 12:31:34 PM EDT Task(s) execution completed with errors.
        3/15/17 12:31:34 PM EDT Execution Time: 00:00:00
        3/15/17 12:31:35 PM EDT Successfully disconnected. (MSTR) development: password_change_tool
        ###################################################################


        """)
        with mock.patch('microstrategy_api.command_manager.subprocess.check_output') as check_output:
            with mock.patch('microstrategy_api.command_manager.open',
                            mock.mock_open(read_data=read_data),
                            create=True):
                check_output.side_effect = subprocess.CalledProcessError(returncode=8,
                                                                         cmd='',
                                                                         output=''
                                                                         )
                try:
                    cmd.execute("test script code", return_output=True)
                    self.fail('CommandManagerException not raised')
                except microstrategy_api.command_manager.CommandManagerException as e:
                    self.assertIn('You do not have Monitor Cluster privilege that is required to perform the task.',
                                  e.args[0]
                                  )

    def test_execute_list_projects(self):
        cmd = self._get_cmd()
        read_data = textwrap.dedent("""\
        3/15/17 12:31:34 PM EDT Version 10.4.0 (Build 10.4.0026.0049)
        3/15/17 12:31:34 PM EDT Connected:password_change_tool@development
        3/15/17 12:31:34 PM EDT Executing task(s)...
        3/15/17 12:31:34 PM EDT Checking syntax...
        3/15/17 12:31:34 PM EDT Syntax is correct.
        3/15/17 12:31:34 PM EDT Syntax checking has been completed.
        Name = Enterprise Manager
        Load On Startup = False
        Active = Loaded
        Name = My Project
        Load On Startup = True
        Active = Loaded
        =================================================
        3/15/17 12:31:34 PM EDT Task(s) execution completed successfully.
        3/15/17 12:31:34 PM EDT Execution Time: 00:00:00
        3/15/17 12:31:35 PM EDT Successfully disconnected. (MSTR) development: password_change_tool
        ###################################################################


        """)
        with mock.patch('microstrategy_api.command_manager.subprocess.check_output') as check_output:
            with mock.patch('microstrategy_api.command_manager.open',
                            mock.mock_open(read_data=read_data),
                            create=True):
                results = cmd.execute("test script code", return_output=True)
                self.assertEquals(results[0]['Name'], 'Enterprise Manager')
                self.assertEquals(results[0]['Active'], 'Loaded')
                self.assertEquals(results[0]['Load On Startup'], 'False')

                self.assertEquals(results[1]['Name'], 'My Project')
                self.assertEquals(results[1]['Active'], 'Loaded')
                self.assertEquals(results[1]['Load On Startup'], 'True')


