import json
import os
import signal
import sys
from datetime import datetime
from typing import List

from botocore.exceptions import ClientError
from warrant import Cognito
from canotic.config import BASE_FOLDER, COGNITO_USERPOOL_ID, COGNITO_CLIENT_ID, COGNITO_REGION
from canotic.client import Client
import click


def _signal_handler(s, f):
    sys.exit(1)


def save_api_key(api_key: str):
    api_key_file = os.path.expanduser(f'{BASE_FOLDER}/apikey')
    if not os.path.exists(os.path.dirname(api_key_file)):
        os.makedirs(os.path.dirname(api_key_file))
    with open(api_key_file, 'w') as f:
        f.write(api_key)


@click.group()
def cli():
    pass


def load_api_key() -> str:
    api_key_file = os.path.expanduser(f'{BASE_FOLDER}/apikey')
    with open(api_key_file) as f:
        api_key = f.readline()
    return api_key


@cli.group()
@click.pass_context
def client(ctx):
    """
    Canotic API operations
    """
    api_key = ''
    try:
        api_key = load_api_key()
    except Exception as e:
        pass
    if len(api_key) == 0:
        print('User needs to login or set api key')
        exit()
    ctx.obj = {}
    ctx.obj['client'] = Client(api_key=api_key)


@client.command(name='create_jobs')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('--callback_url', '-c', help='Callback URL for post when jobs finish')
@click.option('--inputs', '-i', help='Json list with inputs')
@click.option('--inputs_file', '-if', help='URL pointing to JSON file')
@click.pass_context
def create_jobs(ctx, app_id: str, callback_url: str, inputs: str, inputs_file: str):
    """
    Submit jobs
    """
    client = ctx.obj['client']
    print("Submitting jobs")
    json_inputs = None
    if inputs is not None:
        try:
            json_inputs = json.loads(inputs)
        except:
            print("Couldn't read json inputs")
            exit()
    print(client.create_jobs(app_id, callback_url, json_inputs, inputs_file))


@client.command(name='fetch_job')
@click.option('--job_id', '-j', help='Job id', required=True)
@click.pass_context
def fetch_job(ctx, job_id: str):
    """
    Get Job given job id
    """
    client = ctx.obj['client']
    print(f'Fetching job {job_id}')
    print(client.fetch_job(job_id))


@client.command(name='get_job_response')
@click.option('--job_id', '-j', help='Job id', required=True)
@click.pass_context
def get_job_response(ctx, job_id: str):
    """
    Get Job response given job id
    """
    client = ctx.obj['client']
    print(f'Getting job response {job_id}')
    print(client.get_job_response(job_id))


@client.command(name='cancel_job')
@click.option('--job_id', '-j', help='Job id', required=True)
@click.pass_context
def cancel_job(ctx, job_id: str):
    """
    Cancel a job given job id. Only for jobs in SCHEDULED, IN_PROGRESS or SUSPENDED state.
    """
    client = ctx.obj['client']
    print(f'Cancelling job {job_id}')
    print(client.cancel_job(job_id))


@client.command(name='list_jobs')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('--page', '-p', help='Page number', type=int)
@click.option('--size', '-s', help='Size of page', type=int)
@click.option('--sort_by', '-sort', help='Job field to sort by', type=str, default='id', show_default=True)
@click.option('--order_by', '-order', help='Sort direction (asc or desc)',
              type=click.Choice(['asc', 'desc']), default='asc', show_default=True)
@click.option('--created_start_date', '-c0', help='Created start date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--created_end_date', '-c1', help='Created end date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--completed_start_date', '-e0', help='Completed start date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--completed_end_date', '-e1', help='Completed end date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--status_in', '-s_in', help='Status of jobs', multiple=True, type=click.Choice(
    ['SCHEDULED', 'IN_PROGRESS', 'FAILED', 'SUSPENDED', 'CANCELED', 'EXPIRED', 'COMPLETED']))
@click.pass_context
def list_jobs(ctx, app_id: str, page: int, size: int, sort_by: str, order_by: str, created_start_date: datetime,
              created_end_date: datetime, completed_start_date: datetime, completed_end_date: datetime,
              status_in: List[str] = None):
    """
    Get a paginated list of jobs (without response) given an application id
    """
    client = ctx.obj['client']
    print(f'Fetching jobs per application {app_id}')
    if len(status_in) == 0:
        status_in = None
    print(client.list_jobs(app_id, page, size, sort_by, order_by, created_start_date, created_end_date,
                           completed_start_date,
                           completed_end_date, status_in))


@client.command(name='download_jobs')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('--created_start_date', '-c0', help='Created start date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--created_end_date', '-c1', help='Created end date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--completed_start_date', '-e0', help='Completed start date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--completed_end_date', '-e1', help='Completed end date',
              type=click.DateTime(formats=['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']))
@click.option('--status_in', '-s_in', help='Status of jobs', multiple=True, type=click.Choice(
    ['SCHEDULED', 'IN_PROGRESS', 'FAILED', 'SUSPENDED', 'CANCELED', 'EXPIRED', 'COMPLETED']))
@click.pass_context
def download_jobs(ctx, app_id: str, created_start_date: datetime,
                  created_end_date: datetime, completed_start_date: datetime, completed_end_date: datetime,
                  status_in: List[str] = None):
    """
    Trigger processing of job responses that is sent to customer email once is finished.
    """
    client = ctx.obj['client']
    print(f'Triggering job responses processing per application {app_id}')
    if len(status_in) == 0:
        status_in = None
    print(client.download_jobs(app_id, created_start_date, created_end_date, completed_start_date, completed_end_date,
                               status_in))


@client.command(name='create_ground_truth')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('--input_json', '-i', help='Input json of ground truth', required=True)
@click.option('--label', '-l', help='Label (or output) json of ground truth', required=True)
@click.option('--tag', '-t', help='Tag ground truth data')
@click.pass_context
def create_ground_truth(ctx, app_id: str, input_json: dict = None, label: dict = None, tag: str = None):
    """
    Submit fresh ground truth data
    """
    client = ctx.obj['client']
    print("Submitting fresh ground truth data")
    print(client.create_ground_truth(app_id, input_json, label, tag))


@client.command(name='update_ground_truth')
@click.option('--ground_truth_data_id', '-g', help='Ground truth data id', required=True)
@click.option('--input_json', '-i', help='Input json of ground truth')
@click.option('--label', '-l', help='Label (or output) json of ground truth')
@click.option('--tag', '-t', help='Tag ground truth data')
@click.pass_context
def update_ground_truth(ctx, ground_truth_data_id: str, input_json: dict = None, label: dict = None, tag: str = None):
    """
    Update (patch) ground truth data
    """
    client = ctx.obj['client']
    print(f"Updating ground truth data {ground_truth_data_id}")
    print(client.update_ground_truth(ground_truth_data_id, input_json, label, tag))


@client.command(name='list_ground_truth_data')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('--page', '-p', help='Page number', type=int)
@click.option('--size', '-s', help='Size of page', type=int)
@click.pass_context
def list_ground_truth_data(ctx, app_id: str, page: int, size: int):
    """
    List all ground truth data for an application
    """
    client = ctx.obj['client']
    print(f"Fetching ground truth data per application {app_id}")
    print(client.list_ground_truth_data(app_id, page, size))


@client.command(name='get_ground_truth_data')
@click.option('--ground_truth_data_id', '-g', help='Ground truth data id', required=True)
@click.pass_context
def get_ground_truth_data(ctx, ground_truth_data_id: str):
    """
    Fetch single ground truth data object
    """
    client = ctx.obj['client']
    print(f"Fetching ground truth data {ground_truth_data_id}")
    print(client.get_ground_truth_data(ground_truth_data_id))


@client.command(name='delete_ground_truth_data')
@click.option('--ground_truth_data_id', '-g', help='Ground truth data id', required=True)
@click.pass_context
def delete_ground_truth_data(ctx, ground_truth_data_id: str):
    """
    Mark ground truth data as deleted
    """
    client = ctx.obj['client']
    print(f"Deleting ground truth data {ground_truth_data_id}")
    print(client.delete_ground_truth_data(ground_truth_data_id))


@client.command(name='delete_ground_truth_data')
@click.option('--app_id', '-a', help='Application id', required=True)
@click.option('-job_id', '-j', help='Job id', required=True)
@click.pass_context
def create_ground_truth_from_job(ctx, app_id: str, job_id: str):
    client = ctx.obj['client']
    print(f"Converting job {job_id} to ground truth data")
    print(client.create_ground_truth_from_job(app_id, job_id))


@cli.command()
@click.option('--api-key', help='Your Canotic API KEY', required=True)
def config(api_key):
    """
    Set api key.
    """
    save_api_key(api_key)


@cli.command()
@click.option('--username', '-u', help='Canotic Username', required=True)
@click.option('--password', prompt=True, hide_input=True)
def login(username, password):
    """
    Use username and password to get Canotic api key.
    """
    user = Cognito(access_key='AKIAIOSFODNN7EXAMPLE', secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                   user_pool_id=COGNITO_USERPOOL_ID, client_id=COGNITO_CLIENT_ID,
                   user_pool_region=COGNITO_REGION, username=username)
    try:
        user.authenticate(password)
    except ClientError as e:
        if e.response['Error']['Code'] == 'UserNotFoundException' or e.response['Error'][
            'Code'] == 'NotAuthorizedException':
            print("Incorrect username or password")
            return
        else:
            print(f"Unexpected error: {e}")
            return

    client = Client(auth_token=user.access_token)
    api_keys = client.get_apikeys()
    if len(api_keys) > 0:
        save_api_key(api_keys[0])
        print(f'Api key {api_keys[0]} was set')
    else:
        print(f'User {username} doesn\'t have any api keys')


@cli.command()
def logout():
    """
    Remove stored api key
    """
    save_api_key('')
    print('Stored api key was removed')


def main():
    signal.signal(signal.SIGINT, _signal_handler)
    sys.exit(cli())


if __name__ == '__main__':
    main()
