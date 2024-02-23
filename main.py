from jupiter import JupiterExchange
import asyncio
import datetime as dt

async def main():

    print(dt.datetime.now())

    amount_buys = 0
    dexchange = JupiterExchange()
    while dt.datetime.now() < dt.datetime(2024, 1, 31, 14, 58, 30):
        print(dt.datetime.now(), (dt.datetime(2024, 1, 31, 14, 58, 30) - dt.datetime.now()).total_seconds())
        await asyncio.sleep(1)

    while True:
        try:
            dex_quote = dexchange.get_quote_buy()
            if dex_quote is None:
                print(f"dex quote did not meet min slippage price")
                continue

            print(f"Simulating swap with quote: {dex_quote}")

            simulated_result = await dexchange.swap(dex_quote)
            print(f"Swap simulation result: {simulated_result}")
            # uncomment this to actually swap
            #asyncio.create_task(dexchange.swap(dex_quote))
            amount_buys += 1
            # use this to spam network across multiple blocks
            if amount_buys >= 10:
                print("exiting")
                await asyncio.sleep(10)
                exit()
        except KeyError as e:
            print(e)
            import traceback
            print(traceback.format_exc())
        await asyncio.sleep(0.25)

asyncio.run(main())