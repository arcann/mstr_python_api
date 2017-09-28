import keyring

from microstrategy_api.task_proc.task_proc import TaskProc


def main():
    base_url = 'https://devtest.pepfar-panorama.org/MicroStrategy/asp/TaskProc.aspx?'
    user_name = 'Administrator'
    server = 'WIN-NTHRJ60PG84'
    project_name = 'PEPFAR'
    password = keyring.get_password('Development', user_name)

    task_api_client = TaskProc(
        base_url=base_url,
        server=server,
        project_name=project_name,
        username=user_name,
        password=password,
    )

    print(task_api_client.session)


if __name__ == '__main__':
    main()

