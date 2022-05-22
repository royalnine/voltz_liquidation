from web3 import Web3
import json 
import os
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(f"https://kovan.infura.io/v3/{os.environ['WEB3_INFURA_PROJECT_ID']}"))

with open("../build/contracts/LiquidationBot.json") as f:
    data = json.load(f)

abi = data['abi']
bytecode = data['bytecode']
owner = os.environ["ACCOUNT"]
private_key = os.environ["PK"]
margin_engine = w3.toChecksumAddress('0x14d8bc8F4833c01623a158A16Cd3df31Ec46A45D')

def get_nonce(owner):
    return w3.eth.get_transaction_count(owner)

liq = w3.eth.contract(abi=abi, bytecode=bytecode)

transaction = {
    'gas': 9463996,
    'nonce': get_nonce(owner),
    'from': owner
}

deployment = liq.constructor(margin_engine).buildTransaction(transaction)
signed_transaction = w3.eth.account.sign_transaction(deployment, private_key)
result = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(result)

print(tx_receipt['contractAddress'])