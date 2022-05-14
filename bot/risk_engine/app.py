from venv import create
import pandas as pd
import boto3
import logging
import os


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_table() -> boto3.resource:
    hostname = os.environ["LOCALSTACK_HOSTNAME"] # get rid when image is on ECR
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=f"http://{hostname}:4566" # get rid when image is on ECR
    )
    table = dynamodb.Table('Positions')
    return table


def create_dataframe(table: boto3.resource) -> pd.DataFrame:
    response = table.scan()
    dataframe = pd.DataFrame(response['Items'])
    return dataframe


def run():
    table = get_table()
    dataframe = create_dataframe(table)
    logger.info(dataframe)


if __name__ == '__main__':
    run()