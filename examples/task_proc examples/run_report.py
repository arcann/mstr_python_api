import sys
from pprint import pformat

import logging

import keyring

from microstrategy_api.task_proc.report import Report
from microstrategy_api.task_proc.task_proc import TaskProc

base_url = 'https://my_hostname/MicroStrategy/asp/TaskProc.aspx?'


def run_report(task_api_client, report_id, prompt_answers_by_seq=None):
    log = logging.getLogger(__name__+'.run_report')
    log.setLevel(logging.DEBUG)

    rpt = Report(task_api_client, guid=report_id)
    prompts = rpt.get_prompts()
    log.info("prompts:")
    log.info(prompts)
    attributes = rpt.get_attributes()
    log.info("attributes:")
    log.info(pformat(attributes))

    prompt_answers = dict()
    if prompt_answers_by_seq is not None:
        for prompt_number, prompt_answer in prompt_answers_by_seq.items():
            prompt_answers[prompts[prompt_number]] = prompt_answer

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
    user_name = 'Administrator'
    password = keyring.get_password('Development', user_name)
    server = 'my_server'
    project_name = 'my_project'

    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
        username=user_name,
        password=password,
    )

    run_report(task_api_client,
               report_id='4B0C2CA3453DAFB26B113E9171A4FBDE',
               #prompt_answers_by_seq={0: 'PqlFzhuPcF1'}  # Nigeria
    )

    log.info("Logging out")
    task_api_client.logout()
