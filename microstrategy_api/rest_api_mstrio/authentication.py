import requests


def sessions(connection, verbose=False):
    """
    Get the definition of a specific dossier, including attributes and metrics. This in-memory dossier definition provides information about all available objects without actually running any data query/dossier. The results can be used by other requests to help filter large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")

    headers = {'X-MSTR-AuthToken': connection.auth_token, 'X-MSTR-ProjectID': connection.project_id}
    response = requests.get(f'{connection.base_url}/sessions',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def session_privileges(connection, verbose=False):
    """
    Get the definition of a specific dossier, including attributes and metrics. This in-memory dossier definition provides information about all available objects without actually running any data query/dossier. The results can be used by other requests to help filter large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")

    headers = {'X-MSTR-AuthToken': connection.auth_token, 'X-MSTR-ProjectID': connection.project_id}
    response = requests.get(f'{connection.base_url}/sessions/privileges',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def session_privilege_info(connection, privilege_id: str, verbose=False):
    """
    Get the definition of a specific dossier, including attributes and metrics. This in-memory dossier definition provides information about all available objects without actually running any data query/dossier. The results can be used by other requests to help filter large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param privilege_id: ID of the privilege to check
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")

    headers = {'X-MSTR-AuthToken': connection.auth_token, 'X-MSTR-ProjectID': connection.project_id}
    response = requests.get(f'{connection.base_url}/sessions/privileges/{privilege_id}',
                            headers=headers,
                            # cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response
