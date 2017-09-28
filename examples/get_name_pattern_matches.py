from pprint import pformat

import keyring

from microstrategy_api.task_proc.task_proc import TaskProc
from microstrategy_api.task_proc.object_type import ObjectSubType
import logging


base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'PEPFAR'
    password = keyring.get_password('Development', user_name)
    server = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'

    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
        username=user_name,
        password=password
    )

    log.info("Calling get_folder_contents")
    contents = task_api_client.get_matching_objects_list(
        path_list=['\Public Objects\Reports\POART\I-frames\*global*[r]'],
        # path_list=['\Public Objects\Reports\POART\I-frames\[r]'],
        type_restriction={ObjectSubType.DocumentDefinition, ObjectSubType.ReportWritingDocument},
    )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    task_api_client.logout()