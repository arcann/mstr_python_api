import requests


def object_info(connection, object_id, object_type, verbose=False):
    """
    Get information for a specific object in a specific project;
    if you do not specify a project ID, you get information for the object in all projects.
    You identify the object with the object ID and object type. You obtain the authorization token needed to
    execute the request using POST /auth/login; you obtain the project ID using GET /projects. You pass the
    authorization token and the project ID in the request header. You specify the object ID in the path of
    the request. You specify the object type as a query parameter; possible values for object type are
    provided in EnumDSSXMLObjectTypes.

    :param connection: MicroStrategy REST API connection object
    :param object_id: Unique ID of the document you wish to extract information from.
    :param verbose: Verbosity of request response; defaults to False
    :return: Complete HTTP response object
    """

    # check input types
    if not isinstance(object_id, str):
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

    headers = {'X-MSTR-AuthToken': connection.auth_token,
               'X-MSTR-ProjectID': connection.project_id,
               }
    params = {
        'type': object_type,
    }
    response = requests.get(f'{connection.base_url}/objects/{object_id}',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify,
                            params=params,
                            )
    if verbose:
        print(response.url)
    return response


def object_recommendations(connection, document_id, verbose=False):
    """
    Get recommendations for a specific object in a specific project.

    Currently, only objects with type 55 (documents/dossiers) are supported.

    Recommendations are based on an algorithm that uses affinity and popularity. You obtain the authorization token needed to execute the request
    using POST /auth/login and the project ID using GET /projects; you pass the authorization token and the project ID in the request header. You
    identify the object you are getting recommendations for with the object ID; you specify the object ID in the path of the request. You can
    refine the results that are returned using the offset and limit query parameters.

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
    response = requests.get(f'{connection.base_url}/objects/{document_id}/recommendations',
                            headers=headers,
                            cookies=connection.cookies,
                            verify=connection.ssl_verify)
    if verbose:
        print(response.url)
    return response


