import requests
import boto3
import logging
import schedule
import time
import os
from http import HTTPStatus


logger = logging.getLogger(__name__)
# logger.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)


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
      }}
    }}"""


def fetch_and_write_positions(url: str, table: boto3.resource):
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
        batch.put_item(position)
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
  table = dynamodb.Table('Positions')
  try:
    table.table_status
    logger.info("table 'Positions' already exists")
  except dynamodb.meta.client.exceptions.ResourceNotFoundException:
    dynamodb.create_table(
      AttributeDefinitions=[
        {
            'AttributeName': 'id',
            'AttributeType': 'S'
        },
    ],
    TableName='Positions',
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
    logger.info("created 'Positions' table")
  return table


def run_client():
  table = get_or_create_table()
  fetch_and_write_positions(URL, table)


if __name__ == '__main__':
  logger.info("Starting account manager")
  schedule.every(2).minutes.do(run_client)
  
  while True:
    schedule.run_pending()
    time.sleep(1)
