import sys
from pprint import pformat, pprint

import logging

from task_proc import TaskProc, Document

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


def run_document(task_api_client, document_guid, prompt_answers_by_seq=None):
    log = logging.getLogger(__name__+'.run_document')
    log.setLevel(logging.DEBUG)

    doc = Document(task_api_client, guid=document_guid)
    prompts = doc.get_prompts()
    log.info("prompts:")
    log.info(prompts)

    doc = Document(task_api_client, guid=document_guid)
    prompts = doc.get_prompts()
    log.info("prompts:")
    log.info(prompts)

    prompt_answers = dict()
    if prompt_answers_by_seq is not None:
        for prompt_number, prompt_answer in prompt_answers_by_seq.items():
            prompt_answers[prompts[prompt_number]] = prompt_answer

    results = doc.execute(element_prompt_answers=prompt_answers)

    log.info("Document Done")
    return results


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

    results = run_document(
        task_api_client,
        document_guid='6AF9511C4AB4A76635DBEDB98E3859D8',
        prompt_answers_by_seq={0: ['FETQ6OmnsKB']},
    )
    log.debug(pprint(results))

    log.info("Logging out")
    task_api_client.logout()
