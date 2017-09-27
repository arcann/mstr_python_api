import sys
import timeit

import logging

import time

from microstrategy_api.task_proc import TaskProc, Document
from microstrategy_api.task_proc.status import Status

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


def run_document(task_api_client, document_guid, prompt_answers_by_attr=None):
    log = logging.getLogger(__name__+'.run_document')
    log.setLevel(logging.DEBUG)

    doc = Document(task_api_client, guid=document_guid)
    prompts = doc.get_prompts()
    log.info("prompts:")
    log.info(prompts)

    prompt_answers = dict()
    if prompt_answers_by_attr is not None:
        for prompt in prompts:
            if prompt.attribute.guid in prompt_answers_by_attr:
                prompt_answers[prompt] = prompt_answers_by_attr[prompt.attribute.guid]
                log.debug("Prompt {} answer = {}".format(prompt, prompt_answers_by_attr[prompt.attribute.guid]))
            else:
                prompt_answers[prompt] = []
                log.debug("Prompt {} answer = None".format(prompt))

    max_wait_secs = 1
    start_time_precise = timeit.default_timer()
    message = doc.execute_async(
        element_prompt_answers=prompt_answers,
        refresh_cache=True,
        max_wait_secs=max_wait_secs
    )
    log.info('Status={} st = {}, request took {:.1f}'.format(message.status, message.st,
                                                             timeit.default_timer() - start_time_precise))

    while message.status != Status.Result:
        if message.status == Status.Prompt:
            raise ValueError("Prompts not answered")
        time.sleep(1)
        start_time_precise = timeit.default_timer()
        message.update_status(max_wait_ms=max_wait_secs * 800)
        log.info('Status={} st = {}, request took {:.1f}'.format(message.status, message.st,
                                                                 timeit.default_timer() - start_time_precise))
    log.info("Document Done")


if __name__ == '__main__':
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    user_name = 'Administrator'
    password = sys.argv[1]
    server = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'

    task_api_client = TaskProc(base_url=base_url,
                           server=server,
                           project_name=project_name,
                           username=user_name,
                           password=password)

    OU_GUID = '7039371C4B5CC07DC6682D9C0EC8F45C'

    run_document(
        task_api_client,
        # document_guid='BCB75A3D4E247616A91EF19F694BA7EF',  # Age Sex
        # document_guid='51EAB0564DBC634F79170E99D5659B81',  # SNU Results
        # document_guid='93FDBE81465497176A4A64B2D1668662',  # OU Results
        document_guid='9F973FDB44C642D8CE44B5BF4BEB7B3D',  # All Mech
        # prompt_answers_by_attr={OU_GUID: ['HfVjCurKxh2']},  # Kenya
        # prompt_answers_by_attr={OU_GUID: ['f5RoebaDLMx']},  # Zambia
        prompt_answers_by_attr={OU_GUID: ['FETQ6OmnsKB']},  # Uganda
    )

    log.info("Logging out")
    task_api_client.logout()
