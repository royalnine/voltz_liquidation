from brownie import network, Contract

def main():
    contract = Contract.from_explorer("0x15e3484EB4Ae66B9186699DB76024cBC363c1f2B")
    print("received contract")