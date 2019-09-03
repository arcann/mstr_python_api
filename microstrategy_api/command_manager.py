import logging
import os.path
import subprocess
import sys
import textwrap
from configparser import ConfigParser
from tempfile import TemporaryDirectory


class CommandManager(object):
    """
    MicroStrategy Command Manager abstraction layer

    Parameters
    ----------
    project_source:
        The MicroStrategy project source to connect to.
        Optional. Can also be included in the ConfigParser object passed to config.
    connect_user_id:
        The user ID to connect to Command Manager with.
        Optional. Can also be included in the ConfigParser object passed to config.
    connect_password:
        The user password to connect to Command Manager with.
        Optional. Can also be included in keyring, or the ConfigParser object passed to config.
    cmdmgr_path:
        The path to the cmdmgr executable.
        Optional. Can also be included in keyring, or the ConfigParser object passed to config.
        Defaults to 'cmdmgr' expecting OS to find it in the search paths.
    config:
        ConfigParser container with the relevant settings not provided on __init__.
        Settings used from that container:
            project_source
            connect_user_id
            connect_password
            cmdmgr
    config_section:
        The section of config (ConfigParser) to find settings in.
    output_logging_level:
        Optional, default = NOTSET
        What level of messages should be sent to logging module for script output.
    error_logging_level:
        Optional, default = NOTSET
        What level of messages should be sent to logging module for script error output.
    """
    SETTING_SECTION = 'MSTR'
    SETTING_PROJECT_SOURCE = 'project_source'
    SETTING_CONNECT_USER_ID = 'connect_user_id'
    SETTING_CONNECT_PASSWORD = 'connect_password'
    SETTING_CMDMGR = 'cmdmgr'

    def __init__(self,
                 project_source: str = None,
                 connect_user_id: str = None,
                 connect_password: str = None,
                 cmdmgr_path: str = None,
                 config: ConfigParser = None,
                 config_section: str = SETTING_SECTION,
                 output_logging_level: int = logging.NOTSET,
                 error_logging_level: int = logging.NOTSET
                 ):
        self.debug = False
        self.config = config
        self.config_section = config_section
        if self.config is None:
            # Add empty config so we don't always have to check for exceptions
            self.config = ConfigParser()
        if not self.config.has_section(self.config_section):
            # Add the section to the config so we don't always have to check for exceptions
            self.config.add_section(self.config_section)
        self.log = logging.getLogger(__name__)

        self.project_source = project_source or self.config.get(self.config_section,
                                                                CommandManager.SETTING_PROJECT_SOURCE,
                                                                fallback=None)
        if self.project_source is None:
            raise ValueError("project_source required as parameter or config setting")

        self.log.info("Connecting to {}".format(self.project_source))
        self.connect_user_id = connect_user_id or self.config.get(self.config_section,
                                                                  CommandManager.SETTING_CONNECT_USER_ID,
                                                                  fallback=None)
        if self.connect_user_id is None:
            raise ValueError("connect_user_id required as parameter or config setting")

        if connect_password is not None:
            self.connect_password = connect_password
        else:
            self.connect_password = self.config.get(self.config_section,
                                                    CommandManager.SETTING_CONNECT_PASSWORD,
                                                    fallback=None)
            if self.connect_password is None:
                keyring_section = self.config.get(self.config_section, 'keyring_section', fallback=self.project_source)
                try:
                    import keyring
                    self.connect_password = keyring.get_password(keyring_section, self.connect_user_id)
                except ImportError:
                    pass
                if self.connect_password is None:
                    raise ValueError("Admin password required in parameters, config or keyring({},{})".format(
                        keyring_section,
                        self.connect_user_id
                    ))
        self.cmdmgr_path = cmdmgr_path or self.config.get(self.config_section,
                                                          CommandManager.SETTING_CMDMGR,
                                                          fallback='cmdmgr')
        self.output_logging_level = output_logging_level
        self.error_logging_level = error_logging_level

    def __str__(self):
        msg = (f"CommandManager(project_source='{self.project_source}', "
               f"connect_user_id = '{self.connect_user_id}', "
               f"connect_password = '{self.connect_password[:2]}********' "
               f"cmdmgr_path = {self.cmdmgr_path}'"
               )
        return msg

    def should_run_via_cmd(self):
        return self.config.getboolean(self.config_section, 'run_via_cmd', fallback=False)

    def execute(self,
                script_str: str,
                return_output: bool = False,
                ):
        """
        Run a template through command manager

        Parameters
        ----------
        script_str:
            The script to run.
        return_output:
            Optional, default = False
            Should the output be parsed for return values from the script
            For example LIST PROJECTS; would return a list of projects.
            Each list entry is a dict with the attributes returned by the command.
        """
        with TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, 'script'), 'wb') as script_file:
                self.log.debug(script_str)
                script_file.write(script_str.encode('utf-8'))
                script_file.flush()
                output_file_name = os.path.join(temp_dir, 'output.log')
                cmd = []
                if sys.platform == 'win32' and self.should_run_via_cmd():
                    cmd.append('cmd')
                    cmd.append('/C')
                cmd.append(self.cmdmgr_path)
                cmd.append('-n')
                cmd.append(self.project_source)
                cmd.append('-u')
                cmd.append(self.connect_user_id)
                cmd.append('-p')
                cmd.append(self.connect_password)
                cmd.append('-f')
                cmd.append(script_file.name)
                cmd.append('-o')
                cmd.append(output_file_name)

                if self.debug:
                    self.log.debug("run_command CMD=")
                    self.log.debug("{}".format(cmd))
                    self.log.debug("run_command: Executing command manager")
                try:
                    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                    if return_output:
                        output = list()
                        try:
                            with open(output_file_name, 'rt') as output_file:
                                passed_header = False
                                results_done = False
                                first_header = None
                                nested_list = None
                                first_nested_header = None
                                row = dict()
                                nested_row = dict()
                                for line in output_file.readlines():
                                    line = line.rstrip()
                                    if self.output_logging_level != logging.NOTSET:
                                        self.log.log(self.output_logging_level,
                                                     "L:{}".format(line)
                                                     )
                                    if not passed_header:
                                        if 'Syntax checking has been completed' in line:
                                            passed_header = True
                                    elif 'No results returned' in line:
                                        results_done = True
                                    elif 'Successfully disconnected' in line:
                                        results_done = True
                                    elif line[:3] == '===':
                                        results_done = True
                                    elif not results_done:
                                        row_tuple = line.split('=')
                                        if len(row_tuple) == 2:
                                            header, value = row_tuple
                                            header = header.strip()
                                            value = value.strip()
                                            # Check if nested content
                                            if line[0] != ' ':
                                                if first_header is None:
                                                    first_header = header
                                                elif header == first_header:
                                                    output.append(row)
                                                    row = dict()
                                                row[header] = value
                                            else:  # Is nested
                                                if first_nested_header is None:
                                                    first_nested_header = header
                                                elif header == first_nested_header:
                                                    nested_list.append(nested_row)
                                                    nested_row = dict()
                                                nested_row[header] = value
                                        else:
                                            # Nested list
                                            nested_list = list()
                                            row[row_tuple[0]] = nested_list
                                            nested_row = dict()
                                if len(row) > 0:
                                    output.append(row)
                            return output
                        except FileNotFoundError:
                            self.log.error(f'{cmd} did not produce the expected output file')
                            raise
                except subprocess.CalledProcessError as e:
                    errors = f"Error code {e.returncode}\n"
                    errors += "From " + (' '.join(e.cmd)).replace(self.connect_password, '********') + '\n'
                    errors += script_str + '\n'
                    if e.output:
                        if self.error_logging_level != logging.NOTSET:
                            self.log.log(self.error_logging_level, "stdout:{}".format(e.output))
                        errors += e.output.decode('ascii')
                    if e.stderr:
                        if self.error_logging_level != logging.NOTSET:
                            self.log.log(self.error_logging_level, "stderr:{}".format(e.stderr))
                        errors += e.stderr.decode('ascii')
                    if 'You do not have' in errors and 'privilege' in errors:
                        errors = 'System privilege error'
                    try:
                        with open(output_file_name, 'rt') as output_file:
                            passed_header = False
                            for line in output_file.readlines():
                                if self.error_logging_level != logging.NOTSET:
                                    self.log.log(self.error_logging_level, "Error Out2:{}".format(line))
                                if not passed_header:
                                    if 'Syntax checking has been completed' in line:
                                        passed_header = True
                                else:
                                    if 'No results returned' in line:
                                        break
                                    else:
                                        errors += line
                    except FileNotFoundError as fnf:
                        errors += f'Command Manager did not produce the expected output file. Error code {e.returncode} is the only available information. {fnf}\n'
                    raise CommandManagerException(errors)

    def execute_with_substitutions(self,
                                   template,
                                   return_output: bool = False,
                                   **arguments):
        """
        Run a template through command manager
        """
        script_str = template.format(**arguments)
        return self.execute(script_str, return_output)

    def test_connection(self):
        """
        Check that a user can connect
        """

        return self.execute("DISCONNECT SOURCE;")

    def change_user_password(self, target_user: str, new_password: str):
        """
        Change a given users password.

        NOT GUARANTEED SAFE FOR ARBITRARY INPUT!
        Some simple escaping is performed, but it may not block all script injections.
        """
        if target_user.lower() == 'administrator':
            raise CommandManagerException('This tool cannot be used to change the Administrator password.')
        # Escape any double quotes in the password
        new_password = new_password.replace('"', '^"')
        # Escape any double quotes in the user_id
        target_user = target_user.replace('"', '^"')
        password_change_script = textwrap.dedent("""\
            ALTER USER "{user_id}"
            PASSWORD "{password}"
            CHANGEPWD FALSE
            ALLOWCHANGEPWD TRUE
            PASSWORDEXP IN 60 DAYS
            PASSWORDEXPFREQ 60 DAYS ENABLED;
        """)
        self.execute_with_substitutions(password_change_script,
                                        user_id=target_user,
                                        password=new_password)

    def trigger_event(self, event_name: str):
        script = "TRIGGER EVENT '{event_name}';"
        self.execute_with_substitutions(script, event_name=event_name)

    def purge_project_caches(self, project_name: str, cache_type: str = None):
        if cache_type is None:
            cache_type = 'ALL'
        script = "PURGE {cache_type} CACHING IN PROJECT '{project_name}';"
        self.execute_with_substitutions(script, project_name=project_name, cache_type=cache_type)

    def invalidate_project_dbconnection_caches(self, project_name: str, connection: str):
        script = 'INVALIDATE REPORT CACHES DBCONNECTION NAME "{connection}" IN PROJECT "{project_name}";'
        self.execute_with_substitutions(script, project_name=project_name, connection=connection)

    def invalidate_project_table_caches(self, project_name: str, table: str):
        script = 'INVALIDATE REPORT CACHES WHTABLE "{table}" IN PROJECT "{project_name}";'
        self.execute_with_substitutions(script, project_name=project_name, table=table)

    def find_running_jobs(self, user=None, project=None):
        script = 'LIST JOBS'
        if user:
            script += ' FOR USER "{}"'.format(user)
        if project:
            script += ' FROM PROJECT "{}"'.format(project)
        script += ';'
        return self.execute(script, return_output=True)


class CommandManagerException(Exception):
    pass
