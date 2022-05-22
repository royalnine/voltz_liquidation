# voltz liquidation bot

We are using dynamodb to store positions fetched from the graph API and SQS to communicate between account manager and risk engine 

## Prerequisite

Set up .env file `./risk_engine` dirs with the following vars

```
LOCALSTACK_HOSTNAME=localhost -- only needed for running code without docker`
ACCOUNT=YOUR_ACCOUNT_ADDRESS
PK=YOUR_PRIVATE_KEY
MARGIN_ENGINE=MARGIN_ENGINE_ADDRESS_FOR_CORRESPONDING_POOL
BOT_CONTRACT=ADDRESS_OF_BOT_CONTRACT from ../bot_contracts
KOVAN_INFURA_KEY=INFURA_PROJECT_ID
```

## Running the bot

```
docker-compose build
docker-compose up
```

This will spin up local dynamodb, local sqs, account manager and risk engine.