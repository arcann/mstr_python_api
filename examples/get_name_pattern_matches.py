from pprint import pformat

import keyring

from microstrategy_api.task_proc.task_proc import TaskProc
from microstrategy_api.task_proc.object_type import ObjectSubType
import logging


base_url = 'https://my_hostname/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'system_user'
    password = keyring.get_password('Development', user_name)
    server = 'WIN-EQNJ5RHQVEV'
    project_name = 'my_project'

    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
        username=user_name,
        password=password
    )

    log.info("Calling get_folder_contents")
    contents = task_api_client.get_matching_objects_list(
        path_list=['\Public Objects\Reports\Spotlight\[r]'],
        type_restriction={ObjectSubType.DocumentDefinition, ObjectSubType.ReportWritingDocument},
    )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    task_api_client.logout()
