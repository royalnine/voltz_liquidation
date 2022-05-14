from brownie import LiquidationBot, accounts, Contract

def main():
    liquidation_bot = LiquidationBot.deploy({'from': accounts[0], 'gas_price': 9463996})
    liquidation_bot.setMarginEngineAddress('0x75537828f2ce51be7289709686A69CbFDbB714F1', {'gas_price': 7295711})
    
    liquidation_reward = liquidation_bot.getLiquidationReward()

    print(f"before liquidation_reward = {liquidation_reward}")

    # margin_engine = Contract('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    # margin_engine.setLiquidatorReward(20000)

    # liquidation_reward = liquidation_bot.getLiquidationReward()

    # print(f"after liquidation_reward = {liquidation_reward}")
