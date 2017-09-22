import sys
from pprint import pformat

from microstrategy_api.task_proc import TaskProc
import logging

from task_proc import ObjectSubType

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'PEPFAR'
    password = '2017Q1PublicQ2'
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
    contents = task_api_client.get_folder_object(
        '\Public Objects\Reports\POART\I-frames\OVC Visuals Dedup_Iframe',
        type_restriction={ObjectSubType.DocumentDefinition, ObjectSubType.ReportWritingDocument},
    )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    task_api_client.logout()
