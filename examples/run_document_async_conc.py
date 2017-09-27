import logging
import random
import time

import sys
from datetime import datetime

from microstrategy_api.task_proc import TaskProc, MstrClientException, Report, Document
from microstrategy_api.task_proc import ObjectSubType, ObjectType
from microstrategy_api.task_proc.executable_base import ExecutableBase
from microstrategy_api.task_proc.status import Status


class ScheduleEntry(object):
    def __init__(self,
                 folder_object: TaskProc.FolderObject,
                 executable_object: ExecutableBase,
                 prompts=None,
                 ou_name=None,
                 ):
        self.folder_object = folder_object
        self.executable_object = executable_object
        self.prompts = prompts
        self.ou_name = ou_name
        self.message = None
        self.start_time = None
        self.end_time = None
        self.done = False

    def __str__(self):

        if self.ou_name:
            result = "{self.folder_object} for {self.ou_name}".format(self=self)
        else:
            if self.prompts:
                result = "{self.folder_object} with {self.prompts}".format(self=self)
            else:
                result = "{self.folder_object}".format(self=self)
        if self.message:
            result += " Status={}".format(self.message)
        if self.start_time:
            result += " start_time={}".format(self.start_time)
        if self.end_time:
            result += " end_time={}".format(self.end_time)
        if self.start_time and self.end_time:
            result += " duration={}".format(self.end_time - self.start_time)
        return result


class RunConcurrent(object):
    OU_GUID = '7039371C4B5CC07DC6682D9C0EC8F45C'
    OU_DICT = {
        # "Angola":                           "XOivy2uDpMF",
        # "Asia Regional Program":            "iD2i0aynOGm",
        # "Botswana":                         "l1KFEXKI4Dg",
        # "Burma":                            "wChmwjpXOw2",
        # "Burundi":                          "Qh4XMQJhbk8",
        # "Cambodia":                         "XWZK2nop7pM",
        "Cameroon":                         "bQQJe0cC1eD",
        # "Caribbean Region":                 "nBo9Y4yZubB",
        # "Central America Region":           "vSu0nPMbq7b",
        # "Central Asia Region":              "t25400wXrNB",
        "Cote dIvoire":                     "ds0ADyc9UCU",
        "Democratic Republic of the Congo": "ANN4YCOufcP",
        # "Dominican Republic":               "NzelIFhEv3C",
        "Ethiopia":                         "IH1kchw86uA",
        # "Ghana":                            "y3zhsvdXlhN",
        # "Guyana":                           "PeOHqAwdtez",
        # "Haiti":                            "JTypsdEUNPw",
        # "India":                            "skj3e4YSiJY",
        # "Indonesia":                        "W73PRZcjFIU",
        # "Kenya":                            "HfVjCurKxh2",
        # "Lesotho":                          "qllxzIjjurr",
        # "Malawi":                           "lZsCb6y0KDX",
        # "Mozambique":                       "h11OyvlPxpJ",
        "Namibia":                          "FFVkaV9Zk1S",
        "Nigeria":                          "PqlFzhuPcF1",
        # "Papua New Guinea":                 "cl7jVQOW3Ks",
        "Rwanda":                           "XtxUYCsDWrR",
        # "South Africa":                     "cDGPF739ZZr",
        # "South Sudan":                      "WLG0z5NxQs8",
        # "Swaziland":                        "V0qMZH29CtN",
        "Tanzania":                         "mdXu6iCbn2G",
        "Uganda":                           "FETQ6OmnsKB",
        # "Ukraine":                          "ligZVIYs2rL",
        # "Vietnam":                          "YM6xn5QxNpY",
        "Zambia":                           "f5RoebaDLMx",
        "Zimbabwe":                         "a71G4Gtcttv"
    }

    def __init__(self,
                 max_concurrent: int = 5
                 ):
        logging.basicConfig()
        log = logging.getLogger(__name__)
        log.setLevel(logging.WARNING)
        log.root.setLevel(logging.WARNING)
        self.log = log
        self.max_concurrent = max_concurrent
        self.cmd = None
        self.project = None
        self.task_client = None
        self._schedule_entries = list()

    def add_to_schedule(self, schedule_entry):
        self._schedule_entries.append(schedule_entry)

    def get_executable_object(self, folder_obj: TaskProc.FolderObject):
        # If document
        if folder_obj.object_subtype == ObjectSubType.ReportWritingDocument:
            # Document
            return Document(self.task_client, guid=folder_obj.guid, name=folder_obj.full_name())
        elif folder_obj.object_subtype == ObjectSubType.ReportCube:
            # Cube
            return Report(self.task_client, guid=folder_obj.guid, name=folder_obj.full_name())
        else:
            # Dataset
            return Report(self.task_client, guid=folder_obj.guid, name=folder_obj.full_name())

    def _wait(self):
        jobs_are_running = True
        while jobs_are_running:
            time.sleep(15)
            jobs = self.cmd.find_running_jobs(project=self.project)
            if len(jobs) == 0:
                jobs_are_running = False
            else:
                self.log.debug("{} jobs are still active".format(len(jobs)))

    def execute_entry(self, schedule_entry: ScheduleEntry):
        self.log.debug("Executing {}".format(schedule_entry))
        schedule_entry.start_time = datetime.now()
        schedule_entry.message = schedule_entry.executable_object.execute_async(
            element_prompt_answers=schedule_entry.prompts,
            # refresh_cache=True,
            max_wait_secs=1,
        )

    def execute_schedule(self):
        self.log.debug("Starting cache updates")
        done = False
        running_cnt = 0
        error_jobs = []
        while not done:
            pending_cnt = 0

            #if folder_obj.object_subtype == ObjectSubType.ReportCube:

            for schedule_entry in self._schedule_entries:
                # Check if we need to start or check on running job
                if schedule_entry.message is None:
                    pending_cnt += 1
                    if running_cnt < self.max_concurrent:
                        running_cnt += 1
                        self.execute_entry(schedule_entry)
                elif schedule_entry.message.status not in {Status.Result, Status.Prompt}:
                    pending_cnt += 1
                    self.log.debug("Checking on {} which was {}".format(schedule_entry, schedule_entry.message))
                    schedule_entry.message.update_status(max_wait_ms=250)

                if not schedule_entry.done and schedule_entry.message is not None:
                    # Check for status on running jobs
                    if schedule_entry.message.status == Status.Result:
                        schedule_entry.done = True
                        schedule_entry.executable_object.execute(arguments={'messageID': schedule_entry.message.guid})
                        schedule_entry.end_time = datetime.now()
                        self.log.debug("Job {} completed".format(schedule_entry))
                        running_cnt -= 1
                        pending_cnt -= 1
                    elif schedule_entry.message.status == Status.Prompt:
                        schedule_entry.done = True
                        self.log.error("{} has un-resolved prompts".format(schedule_entry))
                        error_jobs.append(schedule_entry)
                        pending_cnt -= 1
                        running_cnt -= 1
                    elif schedule_entry.message.status == Status.ErrMsg:
                        schedule_entry.done = True
                        schedule_entry.end_time = datetime.now()
                        self.log.error("{} has an error".format(schedule_entry))
                        error_jobs.append(schedule_entry)
                        pending_cnt -= 1
                        running_cnt -= 1
            time.sleep(0.1)

            if pending_cnt == 0:
                done = True
            else:
                self.log.debug("{} pending jobs, {} running jobs".format(pending_cnt, running_cnt))

        # self.log.info("-" * 80)
        # self.log.info("Job Summary")
        # self.log.info("-" * 80)
        # for schedule_entry in self._schedule_entries:
        #     print("{s.ou_name},{s.start_time},{s.end_time},{duration}".format(s=schedule_entry, duration=schedule_entry.end_time-schedule_entry.start_time))
        #
        # self.log.info("-" * 80)
        # self.log.info("-" * 80)
        #
        # if error_jobs:
        #     self.log.error("-" * 80)
        #     self.log.error("-" * 80)
        #     self.log.error("Summary of all jobs with errors")
        #     for schedule_entry in error_jobs:
        #         self.log.error("Error in job {}".format(schedule_entry))
        #     self.log.error("-" * 80)

    def run(self, jobs_to_create=50):
        project = "PEPFAR"
        user_name = 'Administrator'
        password = sys.argv[1]
        self.project = project

        self.task_client = TaskProc(base_url='https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?',
                                    server='WIN-NTHRJ60PG84',
                                    project_name=project,
                                    username=user_name,
                                    password=password,
                                    concurrent_max=self.max_concurrent * 2,
                                    )
        # self.task_client = TaskProc(base_url='https://pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?',
        #                             server='WIN-SA6VMUGPKSI',
        #                             project_name=project,
        #                             username=user_name,
        #                             password=password,
        #                             concurrent_max=self.max_concurrent * 2,
        #                             )

        folder_objs = contents = self.task_client.get_folder_contents(
            r"\Public Objects\Reports\POART\I-frames",
            flatten_structure=True,
            recursive=False,
            type_restriction={ObjectSubType.ReportWritingDocument}
        )
        test_reports = [
            'Additional Disaggregates_Iframe',
            'Age Sex Disaggregates_Iframe',
            'CHIPS-Testing Volume and Yield by Modality Dedup_Iframe',
            'Coverage Indicator Results_OU-SNU_Iframe',
            'Mech by SNU Analysis_Iframe',
            'OVC Visuals Non Dedup_Iframe',
            'PMTCT Visuals Dedup_Iframe',
            'SNU Level Analysis_Iframe',
            'TB/HIV Screening to Treatment Visuals Dedup_Iframe',
            'Treatment Continuum and Net New Visuals Dedup_Iframe',
            'VMMC Dedup_Iframe'
        ]

        for conc in range(15, 71, 5):
            self.max_concurrent = conc
            jobs_to_create = conc * 3
            for folder_obj in folder_objs:
                if folder_obj.object_subtype != ObjectSubType.Folder and folder_obj.name in test_reports:
                    executable_object = self.get_executable_object(folder_obj)

                    ou_prompt = None
                    prompts = executable_object.get_prompts()
                    for prompt in prompts:
                        if prompt.attribute.guid == self.OU_GUID:
                            ou_prompt = prompt

                    self._schedule_entries = list()
                    #self.log.info("Scheduling jobs")
                    for _ in range(jobs_to_create):
                        ou_name = random.choice(list(self.OU_DICT.keys()))
                        ou_uid = self.OU_DICT[ou_name]
                        self.add_to_schedule(
                            ScheduleEntry(folder_obj, executable_object, prompts={ou_prompt: ou_uid}, ou_name=ou_name)
                        )

                    #self.log.info("Running jobs")
                    test_start = datetime.now()
                    self.execute_schedule()
                    test_end = datetime.now()

                    total_time = 0
                    max_time = None
                    for schedule_entry in self._schedule_entries:
                        duration = schedule_entry.end_time - schedule_entry.start_time
                        if max_time is None:
                            max_time = duration
                        elif duration > max_time:
                            max_time = duration
                        total_time += (duration.seconds + duration.microseconds/1E6)
                    print("{name},{concurrent},{avg_time},{max_time},{test_duration}".format(
                        name=folder_obj.name,
                        concurrent=self.max_concurrent,
                        avg_time=1.0 * total_time / len(self._schedule_entries),
                        max_time=max_time,
                        test_duration=test_end - test_start,
                    ))

        #self.log.info("Done")


if __name__ == '__main__':
    print("name,concurrent,avg_time,max_time,test_duration")
    RunConcurrent(max_concurrent=55).run()
