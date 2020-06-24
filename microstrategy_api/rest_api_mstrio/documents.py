import requests


def document_cubes(connection, document_id, verbose=False):
    """
    Get the definition of a specific document, including attributes and metrics. This in-memory document definition provides information about all available objects without actually running any data query/document. The results can be used by other requests to help filter large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param document_id: Unique ID of the document you wish to extract information from.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check input types
    if not isinstance(document_id, str):
        print("Error: 'document_id' parameter is not a string")

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")
    if not hasattr(connection, 'project_id'):
        print("Error: connection object does not contain 'project_id'")

    headers = {'X-MSTR-AuthToken': connection.auth_token, 'X-MSTR-ProjectID': connection.project_id}
    response = requests.get(f'{connection.base_url}/documents/{document_id}/cubes',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def document_prompts(connection, document_id, verbose=False):
    """
    Get the definition of a specific document, including attributes and metrics. This in-memory document definition provides information about all available objects without actually running any data query/document. The results can be used by other requests to help filter large datasets and retrieve values dynamically, helping with performance and scalability.

    :param connection: MicroStrategy REST API connection object
    :param document_id: Unique ID of the document you wish to extract information from.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check input types
    if not isinstance(document_id, str):
        print("Error: 'document_id' parameter is not a string")

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")
    if not hasattr(connection, 'project_id'):
        print("Error: connection object does not contain 'project_id'")

    headers = {'X-MSTR-AuthToken': connection.auth_token, 'X-MSTR-ProjectID': connection.project_id}
    response = requests.get(f'{connection.base_url}/documents/{document_id}/prompts',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def document_instance(connection, document_id, offset, limit, verbose=False):
    """
    Get the results of a newly created document instance. This in-memory document instance can be used by other requests.

    :param connection: MicroStrategy REST API connection object
    :param document_id: Unique ID of the document you wish to extract information from.
    :param offset: Optional. Starting point within the collection of returned results. Default is 0.
    :param limit: Optional. Used to control data extract behavior on datasets which have a large number of rows.
    The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
    extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit setting
    (e.g. 10,000) may reduce the total time required to extract the entire dataset.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check input types
    if not isinstance(document_id, str):
        print("Error: 'document_id' parameter is not a string")
    if not isinstance(offset, int):
        print("Error: 'offset' parameter is not int")
    if not isinstance(limit, int):
        print("Error: 'limit' parameter is not int")

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")
    if not hasattr(connection, 'project_id'):
        print("Error: connection object does not contain 'project_id'")

    response = requests.post(url=connection.base_url + '/documents/' + document_id + '/instances/',
                             headers={'X-MSTR-AuthToken': connection.auth_token,
                                      'X-MSTR-ProjectID': connection.project_id},
                             cookies=connection.cookies,
                             params={'offset': offset,
                                     'limit': limit},
                             verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


def document_instance_id(connection, document_id, instance_id, offset, limit, verbose=False):
    """
    Get the results of a previously created document instance, using the in-memory document instance created by a POST /documents/{documentId}/instances request.

    :param connection: MicroStrategy REST API connection object
    :param document_id: Unique ID of the document you wish to extract information from.
    :param instance_id: Unique ID of the in-memory instance of a published document.
    :param offset: Optional. Starting point within the collection of returned results. Default is 0.
    :param limit: Optional. Used to control data extract behavior on datasets which have a large number of rows.
    The default is 1000. As an example, if the dataset has 50,000 rows, this function will incrementally
    extract all 50,000 rows in 1,000 row chunks. Depending on system resources, using a higher limit setting
    (e.g. 10,000) may reduce the total time required to extract the entire dataset.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check input types
    if not isinstance(document_id, str):
        print("Error: 'document_id' parameter is not a string")
    if not isinstance(offset, int):
        print("Error: 'offset' parameter is not int")
    if not isinstance(limit, int):
        print("Error: 'limit' parameter is not int")

    # check connection object
    if not hasattr(connection, 'auth_token'):
        print("Error: connection object does not contain 'auth_token'")
    if not hasattr(connection, 'base_url'):
        print("Error: connection object does not contain 'base_url'")
    if not hasattr(connection, 'cookies'):
        print("Error: connection object does not contain 'cookies'")
    if not hasattr(connection, 'project_id'):
        print("Error: connection object does not contain 'project_id'")

    response = requests.get(url=connection.base_url + '/documents/' + document_id + '/instances/' + instance_id,
                            headers={'X-MSTR-AuthToken': connection.auth_token,
                                     'X-MSTR-ProjectID': connection.project_id},
                            cookies=connection.cookies,
                            params={'offset': offset,
                                    'limit': limit},
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response
