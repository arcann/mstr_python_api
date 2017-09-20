import sys
from pprint import pformat

from microstrategy_api.task_proc import TaskProc
import logging

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'Administrator'
    server = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'

    task_api_client = TaskProc(base_url=base_url,
                           server=server,
                           project_name=project_name,
                           username=user_name,
                           password=sys.argv[1])

    log.info("Calling get_folder_contents")
    # contents = task_api_client.get_folder_contents(system_folder=TaskProc.SystemFolders.Reports)
    # contents = task_api_client.get_folder_contents(folder_id='2451540649316E411E227B9F552968CF')
    # contents = task_api_client.get_report(report_id='2451540649316E411E227B9F552968CF')
    contents = task_api_client.get_folder_contents(
            r"\Public Objects\Reports",
            flatten_structure=True,
            recursive=False,
        ##['\Shared Reports\Testing\Cube for Disaggs Analysis'		   type=ObjectType.ReportDefinition subtype=ObjectSubType.ReportCube guid=2B1BFD654DFC986F52EBC28EDE5C2DB3]
    )
    # contents = task_api_client.get_folder_contents_by_name(r"Public Objects\Templates")
    # contents = task_api_client.get_folder_contents_by_name(r"Public Objects\Reports\POART\Datasets\OVC",
    #                                                    type_restriction=set([2048, 768, 769, 774, 776, 14081]),
    #                                                    )
    # contents = task_api_client.get_folder_contents_by_guid("F414193240E1D8AEE80EF8BFE72A6929")
    # contents = task_api_client.get_folder_contents(name=r"\Public Objects\Reports\Testing",
    #                                            #type_restriction={ObjectSubType.ReportCube},
    #                                            flatten_structure=True,
    #                                            recursive=True,
    #                                            )
    log.info("\n" + pformat(contents))

    log.info("Logging out")
    task_api_client.logout()
