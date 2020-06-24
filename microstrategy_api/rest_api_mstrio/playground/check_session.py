from pprint import pprint

import keyring
from mstrio import microstrategy

from microstrategy_api.rest_api_mstrio.authentication import *

USERNAME = "system_user"
PASSWORD = keyring.get_password('Development', USERNAME)
PROJECT_NAME = "PEPFAR"
BASE_URL = "https://dev.pepfar-panorama.org/MicroStrategyLibrary/api"

# https://dev.pepfar-panorama.org/MicroStrategyLibrary/api-docs/index.html#/


def main():
    conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME, password=PASSWORD, project_name=PROJECT_NAME)
    conn.connect()
    print(f'Connected to {conn.project_name} ID {conn.project_id}')

    print('Session')
    results = sessions(conn)  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Session Privs')
    results = session_privileges(conn)
    pprint(results.json())

    conn.close()


if __name__ == '__main__':
    main()
