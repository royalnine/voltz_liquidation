import time
import pandas as pd
import boto3
import logging
import os
from typing import Any

logger = logging.getLogger("risk_engine")
logging.basicConfig(level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_table() -> boto3.resource:
    hostname = os.environ["LOCALSTACK_HOSTNAME"] # get rid when image is on ECR
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=f"http://{hostname}:4566" # get rid when image is on ECR
    )
    table = dynamodb.Table('liquidation-bot-positions-table')
    return table


def get_queue() -> boto3.resource:
    hostname = os.environ["LOCALSTACK_HOSTNAME"] # get rid when image is on ECR
    sqs = boto3.resource(
        'sqs',
        endpoint_url=f"http://{hostname}:4566" # get rid when image is on ECR
    )
    queue = sqs.get_queue_by_name(
      QueueName='liquidation-bot-positions-queue',
      # QueueOwnerAWSAccountId='string' add this when image on ECR
    )
    return queue


def create_dataframe(table: boto3.resource) -> pd.DataFrame:
    response = table.scan()
    dataframe = pd.DataFrame(response['Items'])
    return dataframe


def poll_messages(queue: boto3.resource) -> Any:
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=1)
        if messages:
            yield messages[0]


def delete_message(message: Any, queue: boto3.resource):
    queue.delete_messages(
        Entries=[
            {
                'Id': message.message_id,
                'ReceiptHandle': message.receipt_handle
            },
        ]
    )
    logger.info(f"deleted message {message.message_id}")


def find_liquidatable_positions(table: boto3.resource) -> list:
    dataframe = create_dataframe(table)
    logger.info(dataframe)
    return []


def run():
    table = get_table()
    logger.info("DDB table obtained")
    queue = get_queue()
    logger.info("SQS obtained")

    for message in poll_messages(queue):
        logger.info(f"message = {message}")
        delete_message(message, queue)
        l_positions = find_liquidatable_positions(table)
        
        # work on l_positions 
        # TODO submit l_positions to lambdas to run liquidations


if __name__ == '__main__':
    logger.info("Starting and sleeping for 20 secs")
    time.sleep(20) # sleep for 5 secs in the beginning to allow account manager to create resources
    logger.info("Woke up and running")
    run()