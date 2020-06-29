from pprint import pformat

import keyring

from microstrategy_api.task_proc.task_proc import TaskProc
import logging

base_url = 'https://my_hostname/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'my_username'
    # user_name = 'Administrator'
    password = keyring.get_password('Development', user_name)
    assert password
    server = 'my_server'
    project_name = 'my_project'

    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
        username=user_name,
        password=password
    )
    print("User Info=", task_api_client.get_user_info())

    log.info("Calling get_folder_contents")
    contents = task_api_client.get_folder_contents(
        name=r"\Public Objects\Reports\Testing",
        # type_restriction={ObjectSubType.ReportCube},
        flatten_structure=True,
        recursive=True,
        )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    task_api_client.logout()
