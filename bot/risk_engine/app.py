import time
import pandas as pd
import boto3
import logging
import os
from typing import Any
from web3 import Web3
import json
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv

logger = logging.getLogger("risk_engine")
logging.basicConfig(level=logging.INFO)


load_dotenv()


ABI = './LiquidationBot.json'
NAME_TO_PROVIDER_URL = {
    "localhost": "http://127.0.0.1:8545",
    "kovan": f"https://kovan.infura.io/v3/{os.environ['KOVAN_INFURA_KEY']}", # make env variable
}


BOT_CONTRACT = os.environ['BOT_CONTRACT'] # TODO deploy on kovan
MARGIN_ENGINE = os.environ['MARGIN_ENGINE']
ACCOUNT = os.environ['ACCOUNT']
PK = os.environ['PK']


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
    response = table.scan(FilterExpression=Attr("marginEngine").eq(MARGIN_ENGINE))
    logger.info(f"read {len(response['Items'])} items off ddb")
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


def get_position_margin_req(w3: Web3, owner: dict, tick_lower: int, tick_upper: int) -> int:
    with open(ABI) as f:
        data = json.load(f)
    owner = w3.toChecksumAddress(owner)
    bot_contract = w3.eth.contract(w3.toChecksumAddress(BOT_CONTRACT), abi=data['abi'])
    get_positions_margin_requirement = bot_contract.get_function_by_signature('getPositionMarginRequirement(address,int24,int24)')
    margin = get_positions_margin_requirement(owner, tick_lower, tick_upper).call()
    return margin


def _get_nonce(w3: Web3, owner: str):
    return w3.eth.get_transaction_count(owner)


def get_liquidation_margin(row, *, w3: Web3):
    owner, tick_lower, tick_upper, margin = row['owner'], row['tickLower'], row['tickUpper'], row['margin']

    liquidation_margin = get_position_margin_req(w3, owner, int(tick_lower), int(tick_upper))
    
    if liquidation_margin:
        margin_health = int(margin)/liquidation_margin
    else:
        margin_health = 100

    row['liquidationMargin'] = liquidation_margin
    row['marginHealth'] = margin_health

    return row


def find_liquidatable_positions(table: boto3.resource, w3: Web3) -> pd.DataFrame:
    logger.info("looking for positions to liquidate")
    positions = create_dataframe(table)
    logger.info("calculating liquidation margin")
    positions_with_liquidation_margin = positions.apply(get_liquidation_margin, axis=1, w3=w3)
    positions_filtered_by_margin_delta = positions_with_liquidation_margin[positions_with_liquidation_margin['marginHealth'] < 1]
    logger.info(f"found {len(positions_filtered_by_margin_delta)} liquidatable positions")
    return positions_filtered_by_margin_delta


def liquidate_position(row, *, w3: Web3) -> bytes:

    owner, tick_lower, tick_upper = row['owner'], row['tickLower'], row['tickUpper']
    with open(ABI) as f:
        data = json.load(f)

    abi = data['abi']

    bot_owner = w3.toChecksumAddress(ACCOUNT)
    owner = w3.toChecksumAddress(owner)
    logger.info(f"liquidating {owner} position")
    transaction = {
        'gas': 10000000,
        'nonce': _get_nonce(w3, bot_owner),
        'from': bot_owner
    }
    try:
        bot_contract = w3.eth.contract(w3.toChecksumAddress(BOT_CONTRACT), abi=abi)
        liquidate_position_function = bot_contract.get_function_by_signature('liquidatePosition(address,int24,int24)')
        built_transaction = liquidate_position_function(owner, int(tick_lower), int(tick_upper)).buildTransaction(transaction)
        signed_transaction = w3.eth.account.sign_transaction(built_transaction, PK)
        tx_handle = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        return tx_handle
    except:
        logger.info(f"error liquidating owner {owner}")
        return None


def liquidate(positions_to_liquidate, w3):
    positions_to_liquidate.apply(liquidate_position, axis=1, w3=w3)


def get_web3_provider(name: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(NAME_TO_PROVIDER_URL[name]))
    return w3


def run():
    w3 = get_web3_provider("kovan") 
    table = get_table()
    logger.info("DDB table obtained")
    queue = get_queue()
    logger.info("SQS obtained")

    for message in poll_messages(queue):
        logger.info(f"message = {message}")
        delete_message(message, queue)
        positions_to_liquidate = find_liquidatable_positions(table, w3)
        liquidate(positions_to_liquidate, w3)


if __name__ == '__main__':
    
    logger.info("Starting and sleeping for 20 secs")
    time.sleep(20) # sleep for 20 secs in the beginning to allow account manager to create resources
    logger.info("Woke up and running")
    run()
