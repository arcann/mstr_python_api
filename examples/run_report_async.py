import sys
from pprint import pformat

import time
import timeit

from microstrategy_api.task_proc import TaskProc, MstrClientException, Report
import logging

from task_proc.status import Status

base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'


def run_report(task_api_client, report_id, prompt_answers_by_attr=None):
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
    if prompt_answers_by_attr is not None:
        for prompt in prompts:
            if prompt.attribute.guid in prompt_answers_by_attr:
                prompt_answers[prompt] = prompt_answers_by_attr[prompt.attribute.guid]
                log.info("Prompt {} answer = {}".format(prompt, prompt_answers_by_attr[prompt.attribute.guid]))
            else:
                prompt_answers[prompt] = []
                log.info("Prompt {} answer = None".format(prompt))

    max_wait_secs = 1
    start_time_precise = timeit.default_timer()
    message = rpt.execute_async(
        element_prompt_answers=prompt_answers,
        refresh_cache=True,
        max_wait_secs=max_wait_secs,
    )
    log.info('Status={} st = {}, request took {:.1f}'.format(message.status, message.st,
                                                             timeit.default_timer() - start_time_precise))
    while message.status != Status.Result:
        if message.status == Status.Prompt:
            raise ValueError("Prompts not answered")
        time.sleep(1)
        start_time_precise = timeit.default_timer()
        message.update_status(max_wait_ms=max_wait_secs * 900)
        log.info('Status={} st = {}, request took {:.1f}'.format(message.status, message.st,
                                                                 timeit.default_timer() - start_time_precise))
    log.info("Report Finished")

    # log.info("Getting data")
    # rpt.execute(arguments={'msgID': message.guid})
    #
    # # Must execute a report before viewing the headers or metrics
    # log.debug("headers:")
    # log.debug(pformat(rpt.get_headers()))
    # log.debug("metrics:")
    # log.debug(pformat(rpt.get_metrics()))
    #
    # values = rpt.get_values()
    # log.info('Rows={}'.format(len(values)))
    # for row_number, row in enumerate(values):
    #     if row_number < 10:
    #         log.debug("Row #{}".format(row_number))
    #         for cell in row:
    #             log.info(' {} = {}'.format(cell.header, cell.value))
    #
    # log.info("Report Done")


if __name__ == '__main__':
    org_units = {
        "Angola":                           "XOivy2uDpMF",
        "Asia Regional Program":            "iD2i0aynOGm",
        "Botswana":                         "l1KFEXKI4Dg",
        "Burma":                            "wChmwjpXOw2",
        "Burundi":                          "Qh4XMQJhbk8",
        "Cambodia":                         "XWZK2nop7pM",
        "Cameroon":                         "bQQJe0cC1eD",
        "Caribbean Region":                 "nBo9Y4yZubB",
        "Central America Region":           "vSu0nPMbq7b",
        "Central Asia Region":              "t25400wXrNB",
        "Cote dIvoire":                     "ds0ADyc9UCU",
        "Democratic Republic of the Congo": "ANN4YCOufcP",
        "Dominican Republic":               "NzelIFhEv3C",
        "Ethiopia":                         "IH1kchw86uA",
        "Ghana":                            "y3zhsvdXlhN",
        "Guyana":                           "PeOHqAwdtez",
        "Haiti":                            "JTypsdEUNPw",
        "India":                            "skj3e4YSiJY",
        "Indonesia":                        "W73PRZcjFIU",
        "Kenya":                            "HfVjCurKxh2",
        "Lesotho":                          "qllxzIjjurr",
        "Malawi":                           "lZsCb6y0KDX",
        "Mozambique":                       "h11OyvlPxpJ",
        "Namibia":                          "FFVkaV9Zk1S",
        "Nigeria":                          "PqlFzhuPcF1",
        "Papua New Guinea":                 "cl7jVQOW3Ks",
        "Rwanda":                           "XtxUYCsDWrR",
        "South Africa":                     "cDGPF739ZZr",
        "South Sudan":                      "WLG0z5NxQs8",
        "Swaziland":                        "V0qMZH29CtN",
        "Tanzania":                         "mdXu6iCbn2G",
        "Uganda":                           "FETQ6OmnsKB",
        "Ukraine":                          "ligZVIYs2rL",
        "Vietnam":                          "YM6xn5QxNpY",
        "Zambia":                           "f5RoebaDLMx",
        "Zimbabwe":                         "a71G4Gtcttv"
    }
    
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

    OU_GUID = '7039371C4B5CC07DC6682D9C0EC8F45C'    
    run_report(task_api_client,
               report_id='6D62CD7A470CC4B697C2209303F318E8',  # All Mech
               # prompt_answers_by_attr={OU_GUID: [org_units['Kenya']}
               # prompt_answers_by_attr={OU_GUID: ['f5RoebaDLMx']},  # Zambia
               # prompt_answers_by_attr={OU_GUID: ['FETQ6OmnsKB']},  # Uganda
               prompt_answers_by_attr={OU_GUID: ['PqlFzhuPcF1']},  # Nigeria
    )

    # for org_unit_name, org_unit_guid in org_units.items():
    #     log.info("Running {}  {}".format(org_unit_name, org_unit_guid))
    #     run_report(task_api_client,
    #                report_id='6D62CD7A470CC4B697C2209303F318E8',  # All Mech
    #                prompt_answers_by_attr={OU_GUID: [org_unit_guid]},
    #     )

    log.info("Logging out")
    task_api_client.logout()
