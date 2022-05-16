import time
import pandas as pd
import boto3
import logging
import os
from typing import Any
from web3 import Web3
import json


"""
Account #0: 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
"""


logger = logging.getLogger("risk_engine")
logging.basicConfig(level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


ABI = '../../bot_contracts/build/contracts/LiquidationBot.json'
BOT_CONTRACT = '0x1fA02b2d6A771842690194Cf62D91bdd92BfE28d' # TODO deploy on kovan
NAME_TO_PROVIDER_URL = {
    "localhost": "http://127.0.0.1:8545",
    "kovan": "https://kovan.infura.io/v3/4155eba497904a7eb58ffda08dd5a28a", # make env variable
}

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


def find_liquidatable_positions(w3: Web3, table: boto3.resource) -> pd.DataFrame:
    dataframe = create_dataframe(table)
    dataframe['LiquidationMargin'] = dataframe.apply(lambda row: get_liquidation_margin(w3, dataframe['owner'], dataframe['tickLower'], dataframe['tickUpper']))
    breakpoint()
    # filter
    # return filtered_dataframe
    # return


def get_liquidation_reward(w3: Web3) -> int:
    with open(ABI) as f:
        data = json.load(f)

    bot_contract = w3.eth.contract(BOT_CONTRACT, abi=data['abi'])

    get_liquidation_reward_function = bot_contract.get_function_by_signature('getLiquidationReward()')
    reward = get_liquidation_reward_function().call()
    return reward


def get_liquidation_margin(w3: Web3, owner: dict, tick_lower: int, tick_upper: int) -> int:
    with open(ABI) as f:
        data = json.load(f)

    bot_contract = w3.eth.contract(BOT_CONTRACT, abi=data['abi'])
    get_positions_margin_requirement = bot_contract.get_function_by_signature('getPositionMarginRequirement(address,int24,int24,bool)')
    owner = w3.toChecksumAddress(owner['id'])
    margin = get_positions_margin_requirement(owner, tick_lower, tick_upper, True).call()
    return margin


def get_web3_provider(name: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(NAME_TO_PROVIDER_URL[name]))
    return w3


def run():
    w3 = get_web3_provider("kovan") ## TODO Change to infura
    table = get_table()
    logger.info("DDB table obtained")
    queue = get_queue()
    logger.info("SQS obtained")

    for message in poll_messages(queue):
        logger.info(f"message = {message}")
        # delete_message(message, queue)
        l_positions = find_liquidatable_positions(w3, table)
        
        # work on l_positions 
        # TODO submit l_positions to lambdas to run liquidations


if __name__ == '__main__':
    
    logger.info("Starting and sleeping for 20 secs")
    time.sleep(20) # sleep for 20 secs in the beginning to allow account manager to create resources
    logger.info("Woke up and running")
    run()
    # get_liquidation_margin(w3, '0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266', 0, 3000)
