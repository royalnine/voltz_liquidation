from brownie import LiquidationBot, accounts, Contract

def main():
    liquidation_bot = LiquidationBot.deploy({'from': accounts[0], 'gas_price': 9463996})
    liquidation_bot.setMarginEngineAddress('0x15e3484EB4Ae66B9186699DB76024cBC363c1f2B', {'gas_price': 8330283})
    
    liquidation_reward = liquidation_bot.getLiquidationReward()

    print(f"before liquidation_reward = {liquidation_reward}")

    # margin_requirement = liquidation_bot.getPositionMarginRequirement('0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266', -1000, 1000, True, {'gas_price': 4945713})

    # print(f"before margin_requirement = {margin_requirement}")

    # margin_engine = Contract('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    # margin_engine.setLiquidatorReward(20000)

    # liquidation_reward = liquidation_bot.getLiquidationReward()

    # print(f"after liquidation_reward = {liquidation_reward}")
