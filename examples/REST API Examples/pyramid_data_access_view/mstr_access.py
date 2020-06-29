import logging
from json import JSONDecodeError

from pyramid.request import Request
from pyramid.authentication import extract_http_basic_credentials

from microstrategy_api.mstr_rest_api_facade import MstrRestApiFacade
from simple_view import SimpleView

log = logging.getLogger(__name__)


@SimpleView(path='/mstr_data_access', renderer='string')
def mstr_data_access(request: Request):
    log.debug(f'query = {request.query_string}')
    log.debug(f'headers = {dict(request.headers)}')
    log.debug(f'body = {request.body}')

    credentials = extract_http_basic_credentials(request)
    if credentials is None:
        return "Error: HTTP Basic Authentication is required"
    username = credentials.username
    password = credentials.password

    try:
        json_request = request.json_body
        project_name = json_request['project']
        log.debug(f'project_name = {project_name}')
        mstr_path = json_request['path']
        log.debug(f'mstr_path = {mstr_path}')
        mstr_rest_api_url = request.registry.settings['microstrategy_rest_api_url']
        mstr_rest_api_version = request.registry.settings['microstrategy_rest_api_version']
        rest_api = MstrRestApiFacade(mstr_rest_api_url, username, password, api_version=mstr_rest_api_version)
        login_resuls = rest_api.login()
        if login_resuls['mstr_auth_token'] is None:
            return f"Error: Login failed: {login_resuls['error_message']}"
        else:
            log.debug(f"mstr_auth_token = {login_resuls['mstr_auth_token']}")
        csv_rslt = rest_api.run_report_csv(
            project_name=project_name,
            report_path=mstr_path,
        )
        rest_api.logout()
        return csv_rslt
    except JSONDecodeError as e:
        return f"Error: body of request must be JSON formatted. {e}"
    except KeyError as e:
        return f"Error: Request body json missing {e}"


@SimpleView(path='/mstr_data_definition', renderer='string')
def mstr_data_definition(request: Request):
    log.debug(f'query = {request.query_string}')
    log.debug(f'headers = {dict(request.headers)}')
    log.debug(f'body = {request.body}')

    credentials = extract_http_basic_credentials(request)
    if credentials is None:
        return "Error: HTTP Basic Authentication is required"
    username = credentials.username
    password = credentials.password

    try:
        json_request = request.json_body
        project_name = json_request['project']
        log.debug(f'project_name = {project_name}')
        mstr_path = json_request['path']
        log.debug(f'mstr_path = {mstr_path}')
        mstr_rest_api_url = request.registry.settings['microstrategy_rest_api_url']
        mstr_rest_api_version = request.registry.settings['microstrategy_rest_api_version']
        rest_api = MstrRestApiFacade(mstr_rest_api_url, username, password, api_version=mstr_rest_api_version)
        login_resuls = rest_api.login()
        if login_resuls['mstr_auth_token'] is None:
            return f"Error: Login failed: {login_resuls['error_message']}"
        else:
            log.debug(f"mstr_auth_token = {login_resuls['mstr_auth_token']}")
        csv_rslt = rest_api.get_report_definition_csv(
            project_name=project_name,
            report_path=mstr_path,
        )

        rest_api.logout()
        return csv_rslt
    except JSONDecodeError as e:
        return f"Error: body of request must be JSON formatted. {e}"
    except KeyError as e:
        return f"Error: Request body json missing {e}"
