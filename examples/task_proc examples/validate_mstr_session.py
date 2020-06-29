import logging

import keyring

from microstrategy_api.task_proc.exceptions import MstrClientException
from microstrategy_api.task_proc.privilege_types import PrivilegeTypes
from microstrategy_api.task_proc.task_proc import TaskProc

def validate_session(session_state):
    """
    Authenticate callers using a MicroStrategy session cookie. Note: The session value needed is not usually
    stored as a session cookie or passed to code outside of /MicroStrategy. Javascript code must be used to
    generate a cookie value that this function can use.
    """
    log = logging.getLogger(__name__ + '.validate_session')
    authorized = False
    if session_state is None:
        log.error('session state is None')
    else:
        try:
            log.debug('microstrategy_task_url = {}'.format(base_url))
            task_api_client = TaskProc(base_url=base_url, session_state=session_state)
            task_api_client.trace = True
            privs = task_api_client.check_user_privileges(privilege_types={PrivilegeTypes.CreateAppObj})
            log.debug('Session good. privs={p}'.format(p=privs))
            if privs[PrivilegeTypes.CreateAppObj]:
                log.info("Has required priv")
            else:
                log.info("DOES NOT HAVE REQUIRED PRIV")
            authorized = True
        except MstrClientException as e:
            log.debug('Session not valid for {} {}'.format(session_state, e))
    return authorized


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'my_user'
    password = keyring.get_password('Development', user_name)
    server = 'my_server'
    project_name = 'my_project'

    session_state = None
    logout_session = False
    task_api_client = None

    # For testing purposes make a valid session
    if session_state is None:
        task_api_client = TaskProc(
            base_url=base_url,
            server=server,
            project_name=project_name,
            username=user_name,
            password=password,
        )
        session_state = task_api_client.session
        logout_session = True

    log.info("validate_session")
    validate_session(session_state)

    if logout_session and task_api_client is not None:
        log.info("Logging out")
        task_api_client.logout()


    log.info("Testing ANON session")
    # For testing purposes make a valid ANON session
    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
    )
    session_state = task_api_client.session
    logout_session = True

    log.info("validate_session for ANON")
    validate_session(session_state)

    if logout_session and task_api_client is not None:
        log.info("Logging out")
        task_api_client.logout()

