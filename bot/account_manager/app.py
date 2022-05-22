import requests
import boto3
import logging
import schedule
import time
import os
from http import HTTPStatus
from dotenv import load_dotenv
from position_serialiser import Position


load_dotenv()


logger = logging.getLogger("account_manager")
logging.basicConfig(level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)


URL = 'https://api.thegraph.com/subgraphs/name/voltzprotocol/v1-2'


BASE_QUERY = """{{
    positions(first: {count}, skip: {offset}) {{
        id
        tickLower {{
          value
        }}
        tickUpper {{
          value
        }}
        margin
        owner {{
          id
        }}
        marginUpdates{{
          id
          marginDelta
        }}
        liquidations{{
          id
        }}
        amm{{
          id
          marginEngine{{
            id
          }}
        }}
      }}
    }}"""


def get_position_dataclass(position: dict) -> Position:
  return Position(
    id=position['id'],
    tickLower=position['tickLower'],
    tickUpper=position['tickUpper'],
    margin=position['margin'],
    owner=position['owner']['id'],
    liquidations=position['liquidations'],
    marginEngine=position['amm']['marginEngine']['id'],
  ) 


def fetch_and_write_positions(url: str, table: boto3.resource): ## TODO retrieve newly created or updated ids
  """
  Fetch positions -> write to dynamodb
  """
  count: int = 1000
  offset: int = 0
  while True:
    positions = fetch_positions(url, count, offset)
    if not positions:
      break
    write_positions(positions, table)
    offset += count


def fetch_positions(url: str, count: int, offset: int) -> dict:
  """
  Method to fetch voltz positions from the graph api
  """
  resp = requests.post(url, json={'query': BASE_QUERY.format(count=count, offset=offset)})

  if resp.status_code == HTTPStatus.OK:
    positions = resp.json()['data']['positions'] 
    logger.info(f"fetched {count} positions with {offset} offset")
  else:
    raise RuntimeError(status_code=resp.status_code)

  return positions


def write_positions(positions: dict, table: boto3.resource):
  """
  Method to write positions to dynamodb
  """
  try:
    with table.batch_writer() as batch:
      for position in positions:
        pos = get_position_dataclass(position)
        batch.put_item(pos.to_dict())
    logger.info("wrote positions to db")
  except Exception as e:
    logger.exception(e)


def get_or_create_table() -> boto3.resource:
  """
  Method to get or create dynamodb table
  """
  hostname = os.environ["LOCALSTACK_HOSTNAME"] # get rid when image is on ECR
  dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=f"http://{hostname}:4566" # get rid when image is on ECR
  )
  table = dynamodb.Table('liquidation-bot-positions-table')
  try:
    table.table_status
    logger.info("table 'liquidation-bot-positions-table' already exists")
  except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    dynamodb.create_table(
      AttributeDefinitions=[
        {
            'AttributeName': 'id',
            'AttributeType': 'S'
        },
    ],
    TableName='liquidation-bot-positions-table',
    KeySchema=[
        {
            'AttributeName': 'id',
            'KeyType': 'HASH'
        },
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 123,
        'WriteCapacityUnits': 123
    },)
    logger.info("created 'liquidation-bot-positions-table' table")
  return table


def get_or_create_queue() -> boto3.resource:
  hostname = os.environ["LOCALSTACK_HOSTNAME"] # get rid when image is on ECR
  sqs = boto3.resource(
    'sqs',
    endpoint_url=f"http://{hostname}:4566" # get rid when image is on ECR
  )
  try:
    queue = sqs.get_queue_by_name(
      QueueName='liquidation-bot-positions-queue',
      # QueueOwnerAWSAccountId='string' add this when image on ECR
    )
  except sqs.meta.client.exceptions.QueueDoesNotExist:
    queue = sqs.create_queue(
      QueueName='liquidation-bot-positions-queue',
    )
  return queue


def run(table: boto3.resource, queue: boto3.resource):
  """
  Driver
  """
  
  fetch_and_write_positions(URL, table)
  queue.send_message(MessageBody='fetch_complete')


if __name__ == '__main__':
  logger.info("Starting account manager")
  table = get_or_create_table()
  logger.info("DDB table obtained")
  queue = get_or_create_queue()
  logger.info("SQS obtained")

  run(table=table, queue=queue)
  
  schedule.every(90).seconds.do(run, table=table, queue=queue)
  
  while True:
    schedule.run_pending()
    time.sleep(1)