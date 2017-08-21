import sys
from pprint import pformat

from microstrategy_api.task_proc import TaskProc, MstrClientException, Report
import logging

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


def psnu_download(mstr_client):
    log = logging.getLogger(__name__+'.psnu_download')
    log.setLevel(logging.DEBUG)

    rpt = Report(mstr_client, report_id='4B0C2CA3453DAFB26B113E9171A4FBDE')
    prompts = rpt.get_prompts()
    log.info("prompts:")
    log.info(prompts)
    attributes = rpt.get_attributes()
    log.info("attributes:")
    log.info(pformat(attributes))

    # prompt_answers = {prompts[0]: 'HfVjCurKxh2'}  # Kenya
    prompt_answers = {prompts[0]: 'PqlFzhuPcF1'}  # Nigeria
    rpt.execute(element_prompt_answers=prompt_answers)
    values = rpt.get_values()
    log.info('Rows={}'.format(len(values)))
    for row_number, row in enumerate(values):
        if row_number < 10:
            log.debug("Row #{}".format(row_number))
            for cell in row:
                log.info(' {} = {}'.format(cell.header, cell.value))
    # Must execute a report before viewing the headers or metrics
    log.debug("headers:")
    log.debug(pformat(rpt.get_headers()))
    log.debug("metrics:")
    log.debug(pformat(rpt.get_metrics()))
    log.info("Report Done")


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    user_name = 'PEPFAR'
    project_source = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR Q3'

    mstr_client = TaskProc(base_url=base_url,
                           project_source=project_source,
                           project_name=project_name,
                           username=user_name,
                           password=sys.argv[1])

    psnu_download(mstr_client)

    log.info("Logging out")
    mstr_client.logout()
