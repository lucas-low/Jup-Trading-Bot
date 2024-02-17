from jupiter import JupiterExchange
import asyncio
import datetime as dt

async def main():
    print(dt.datetime.now())

    amount_buys = 0
    dexchange = JupiterExchange()

    # Wait until a specific time to start trading
    while dt.datetime.now() < dt.datetime(2024, 1, 31, 14, 58, 30):
        remaining_time = (dt.datetime(2024, 1, 31, 14, 58, 30) - dt.datetime.now()).total_seconds()
        print(dt.datetime.now(), remaining_time)
        await asyncio.sleep(1)  # Sleep to prevent spamming

    while True:
        try:
            dex_quote = await dexchange.get_quote_buy()  # Ensure this is awaited
            if dex_quote is None:
                print("Dex quote did not meet min slippage price")
                continue

            print(f"Simulating swap with quote: {dex_quote}")
            simulated_result = await dexchange.swap(dex_quote)
            print(f"Swap simulation result: {simulated_result}")
            
            amount_buys += 1
            if amount_buys >= 10:
                print("Exiting after 10 buys")
                await asyncio.sleep(10)
                exit()
        except Exception as e:  # Catch all exceptions to prevent crash
            print(f"An error occurred: {e}")
            await asyncio.sleep(0.25)  # Throttle requests to prevent rate limiting

asyncio.run(main())
