import sys

from task_proc import TaskProc


def main():
    base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'
    user_name = 'Administrator'
    server = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'

    task_api_client = TaskProc(base_url=base_url,
                           server=server,
                           project_name=project_name,
                           username=user_name,
                           password=sys.argv[1])

    print(task_api_client.session)


if __name__ == '__main__':
    main()

