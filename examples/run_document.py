import sys
from pprint import pformat, pprint

import logging

from task_proc import TaskProc, Document

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


def run_document(task_api_client, document_guid, prompt_answers_by_attr=None):
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
    if prompt_answers_by_attr is not None:
        for prompt in prompts:
            if prompt.attribute.guid in prompt_answers_by_attr:
                prompt_answers[prompt] = prompt_answers_by_attr[prompt.attribute.guid]
                log.debug("Prompt {} answer = {}".format(prompt, prompt_answers_by_attr[prompt.attribute.guid]))
            else:
                prompt_answers[prompt] = []
                log.debug("Prompt {} answer = None".format(prompt))

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

    OU_GUID = '7039371C4B5CC07DC6682D9C0EC8F45C'

    task_api_client = TaskProc(base_url=base_url,
                           server=server,
                           project_name=project_name,
                           username=user_name,
                           password=password)

    results = run_document(
        task_api_client,
        # document_guid='6AF9511C4AB4A76635DBEDB98E3859D8',
        document_guid='084536174A598B380CD33684232BB59C',
        prompt_answers_by_attr={OU_GUID: ['FETQ6OmnsKB']},
    )
    log.debug(pprint(results))

    log.info("Logging out")
    task_api_client.logout()
