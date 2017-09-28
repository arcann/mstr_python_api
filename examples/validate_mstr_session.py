import logging

import keyring

from microstrategy_api.task_proc.exceptions import MstrClientException
from microstrategy_api.task_proc.task_proc import TaskProc

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


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
            privs = task_api_client.check_user_privileges()
            authorized = True
        except MstrClientException as e:
            log.debug('Session not valid for {} {}'.format(session_state, e))
    return authorized


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'PEPFAR'
    password = keyring.get_password('Development', user_name)
    project_source = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'

    session_state = None
    # session_state = '0.00000001d7575431f2e9639c7ad0f291eb844fa008a24a181923ffb4e454a48175cd557a8cda5d6267d45a54ddf02d776b315e7f8ddf28ebbd15007f2195f0316d578f138e525494cde73105f67526fe496cb3b89eeefeb7e388ca71641aaf1c19a4f148cd7064a4ed5a4949c2ef18c11c84f774e5df964b13109c330c2a66d521385a2b769aa84731b14e02d68cb570.1033.0.1.America/New*_York.pidn2*_1*_prun*_1.000000010f301c1bdc227fa2b7ebae5edd60faf5a68ffe339071ca3a21e5701eefb7a7c80cd580875fc12b4670578583e31f613a.0.1.1.PEPFAR.111159B147906A00F31BCFB0573D473C.0-1033.1.1_-0.1.0_-1033.1.1_10.1.0.*0.0'
    logout_session = False
    task_api_client = None

    # For testing purposes make a valid session
    if session_state is None:
        task_api_client = TaskProc(
            base_url=base_url,
            project_source=project_source,
            project_name=project_name,
            username=user_name,
            password=password,
        )
        session_state = task_api_client.session
        logout_session = True

    log.info("validation_session")
    validate_session(session_state)

    if logout_session and task_api_client is not None:
        log.info("Logging out")
        task_api_client.logout()
