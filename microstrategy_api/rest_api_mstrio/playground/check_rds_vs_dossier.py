from pprint import pprint

import keyring
from mstrio import microstrategy
from microstrategy_api.rest_api_mstrio.documents import document_cubes, document_prompts
from microstrategy_api.rest_api_mstrio.dossiers import dossier
from microstrategy_api.rest_api_mstrio.objects import object_info, object_recommendations

USERNAME = "system_user"
PASSWORD = keyring.get_password('Development', USERNAME)
PROJECT_NAME = "PEPFAR"
BASE_URL = "https://dev.pepfar-panorama.org/MicroStrategyLibrary/api"

# https://dev.pepfar-panorama.org/MicroStrategyLibrary/api-docs/index.html#/


def main():
    conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME, password=PASSWORD, project_name=PROJECT_NAME)
    conn.connect()
    print(f'Connected to {conn.project_name} ID {conn.project_id}')

    # project_list = projects(conn)
    # pprint(project_list.json())

    # results = report(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE')  # Age Sex Disaggregates Global_Iframe
    # pprint(results.json())  # b'{"code":"ERR001","iServerCode":-2147217147,"message":"(The object with the given identifier is not an object of the expected type.)","ticketId":"941a569c4bea4e469a9fc69b0155820b"}'
    #
    # results = report(conn, '965160184912B1497ACBDBA8274FEAB1')  # Clinical Cascade: All OU Dossier
    # pprint(results.json())

    print('=' * 80)
    print("Cubes")
    print('=' * 80)
    print('Age Sex Disaggregates Global_Iframe')
    results = document_cubes(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE')  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Clinical Cascade: All OU Dossier')
    results = document_cubes(conn, '965160184912B1497ACBDBA8274FEAB1')  # Clinical Cascade: All OU Dossier
    pprint(results.json())

    print('=' * 80)
    print("Prompts")
    print('=' * 80)
    print('Age Sex Disaggregates Global_Iframe')
    results = document_prompts(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE')  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Clinical Cascade: All OU Dossier')
    results = document_prompts(conn, '965160184912B1497ACBDBA8274FEAB1')  # Clinical Cascade: All OU Dossier
    pprint(results.json())

    print('=' * 80)
    print("Dossier structure")
    print('=' * 80)
    print('Age Sex Disaggregates Global_Iframe')
    results = dossier(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE')  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Clinical Cascade: All OU Dossier')
    results = dossier(conn, '965160184912B1497ACBDBA8274FEAB1')  # Clinical Cascade: All OU Dossier
    pprint(results.json())

    print('=' * 80)
    print("Object info")
    print('=' * 80)
    print('Age Sex Disaggregates Global_Iframe')
    results = object_info(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE', 55)  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Clinical Cascade: All OU Dossier')
    results = object_info(conn, '965160184912B1497ACBDBA8274FEAB1', 55)  # Clinical Cascade: All OU Dossier
    pprint(results.json())

    print('=' * 80)
    print("Object recommendations")
    print('=' * 80)
    print('Age Sex Disaggregates Global_Iframe')
    results = object_recommendations(conn, '3069CDF24535B4AA9FB1BE8FDFF9EDDE')  # Age Sex Disaggregates Global_Iframe
    pprint(results.json())

    print('-' * 80)
    print('Clinical Cascade: All OU Dossier')
    results = object_recommendations(conn, '965160184912B1497ACBDBA8274FEAB1')  # Clinical Cascade: All OU Dossier
    pprint(results.json())

    conn.close()


if __name__ == '__main__':
    main()
