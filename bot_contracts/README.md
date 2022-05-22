# deploying the contract

## Prerequisite

Set up .env file with the following env vars in `./scripts` dir with:

```
ACCOUNT=YOUR_ACCOUNT_ADDRESS
PK=YOUR_PRIVATE_KEY
WEB3_INFURA_PROJECT_ID=PROJECT_ID_FROM_INFURA
```

## Deploying the contract

```
pip install web3
pip install python-dotenv
python ./scripts/deploy_liquidation_bot.py
```
 
remember the output contract address, this will be needed to run the bot
