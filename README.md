1) npm run deploy:localhost
2) npm run createTestIrs:localhost
3) npx hardhat --network localhost mintTestTokens --beneficiaries 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 --amount 900
4) npx hardhat --network localhost mintLiquidity
 ensure tickspacing is correct for ticks
 ensure margin is enough
 approve test token spendature


1) Deploy liquidator bot contract
2) Take address and put into /scripts



LOCALSTACK_HOSTNAME=localhost /home/pochanga/.pyenv/versions/3.9.5/envs/account_manager/bin/python /home/pochanga/money-hack/liquidation_bot/bot/account_manager/app.py

LOCALSTACK_HOSTNAME=localhost /home/pochanga/.pyenv/versions/voltz-bot/envs/risk_engine/bin/python /home/pochanga/money-hack/liquidation_bot/bot/risk_engine/app.py