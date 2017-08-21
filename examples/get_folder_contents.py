import sys
from pprint import pformat

from microstrategy_api.task_proc import TaskProc, MstrClientException
import logging

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'Administrator'
    project_source = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR Q3'

    mstr_client = TaskProc(base_url=base_url,
                           project_source=project_source,
                           project_name=project_name,
                           username=user_name,
                           password=sys.argv[1])

    log.info("Calling get_folder_contents")
    # contents = mstr_client.get_folder_contents(system_folder=TaskProc.SystemFolders.Reports)
    # contents = mstr_client.get_folder_contents(folder_id='2451540649316E411E227B9F552968CF')
    #contents = mstr_client.get_report(report_id='2451540649316E411E227B9F552968CF')
    # contents = mstr_client.get_folder_contents_by_name(r"Public Objects/Reports/POART/I-frames")
    # contents = mstr_client.get_folder_contents_by_name(r"Public Objects\Templates")
    # contents = mstr_client.get_folder_contents_by_name(r"Public Objects\Reports\POART\Datasets\OVC",
    #                                                    type_restriction=set([2048, 768, 769, 774, 776, 14081]),
    #                                                    )
    contents = mstr_client.get_folder_recursive_contents(name=r"Public Objects",
                                                         type_restriction={2048, 768, 769, 774, 776, 14081},
                                                         )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    mstr_client.logout()
