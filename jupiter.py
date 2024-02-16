import requests
import solders
import base64
from solders.keypair import Keypair
import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.exceptions import SolanaRpcException
from solana.rpc.core import UnconfirmedTxError
import json
from decimal import Decimal
import datetime as dt

RPC_FILE = './rpc'
with open(RPC_FILE, 'r') as f: 
    rpc_url = f.readline().strip()

BASE_URL = "https://quote-api.jup.ag/v6"
JUP_ADDRESS = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"
JUP_DECIMALS = 6
#JUP_ADDRESS = "So11111111111111111111111111111111111111112"
#JUP_DECIMALS = 9
PRICE_THRESHOLD = Decimal('0.8')
PRICE_THRESHOLD_LOWER = Decimal('0.3')
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDC_DECIMALS = 6

PUBKEY = 'INSERT YOUR PUBLIC WALLET ADDRESS HERE'

# this should match the priv key of your pub key - export it from phantom
KEYPATH = './key'
with open(KEYPATH, 'r') as f: 
    address = f.readline().strip()
    exported_secret = f.readline().strip()

exported_bytes=base58.b58decode(exported_secret)
kp = Keypair.from_bytes(exported_bytes)

# sanity check
assert str(kp.pubkey()) == address, f"{kp.pubkey()} != {address}"
class JupiterExchange:
    def __init__(self):
        self.amount_to_buy_usdc = Decimal(input('enter amount to buy in usdc:\t').strip())
        print(f"{PRICE_THRESHOLD=} {PRICE_THRESHOLD_LOWER=}")
        print(f"{JUP_ADDRESS=}")
        print(f"{JUP_DECIMALS=}")
        print(f"{self.amount_to_buy_usdc=}")
        x = input("looks legit? press y if so:\t")
        if x.strip() != "y":
            exit()
        self.solana_client = AsyncClient(rpc_url)
        self.slippage = 3000

        # Simulated method
    def get_quote_buy(self):
        # ... [other simulation setup code] ...
        # Instead of making an actual request, return a simulated response
        return {
            'inAmount': '500000',  # Simulated amount in USDC (5 USDC)
            'outAmount': '1500000',  # Simulated amount out in JUP (15 JUP)
            'otherAmountThreshold': '1400000',  # Simulated slippage threshold amount
        }

    # Simulated method
    async def swap(self, quote, use_shared_accounts=True):
        # Log the action instead of executing it
        print(f"Simulated swap with quote: {quote}")
        # Return a simulated transaction ID or result
        return "SimulatedTxId1234"

    def get_quote_buy(self):
        try:
            start_dt = dt.datetime.now()
            amt = int(self.amount_to_buy_usdc * (10 ** USDC_DECIMALS))
            r = requests.get(f"{BASE_URL}/quote?inputMint={USDC_ADDRESS}&outputMint={JUP_ADDRESS}&amount={amt}&slippageBps={self.slippage}&swapMode=ExactIn")
            #print(json.dumps(r.json(), indent=4))
            print(f"[{dt.datetime.now()}] Took {(dt.datetime.now() - start_dt).total_seconds():.2f} for BUY quote")
            data = r.json()
            if 'error' in data:
                print(f"[{dt.datetime.now()}] {data}")
            else:
                amount_in_human = Decimal(data['inAmount']) / (10 ** USDC_DECIMALS)
                amount_out_human = Decimal(data['outAmount']) / (10 ** JUP_DECIMALS)
                amount_out_slippage_thresh_human = Decimal(data['otherAmountThreshold']) / (10 ** JUP_DECIMALS)
                price = amount_in_human / amount_out_human
                price_min =  amount_in_human / amount_out_slippage_thresh_human
                print(f"[{dt.datetime.now()}] Got quote: {price} ({price_min} w/ {self.slippage} bps slippage)")
                if price_min < PRICE_THRESHOLD and price > PRICE_THRESHOLD_LOWER:
                    print('yes')
                    return data
                else:
                    print(f'no - {PRICE_THRESHOLD=}')
                    self.slippage -= 500
                    if self.slippage <= 100:
                        self.slippage = 100
                    return None
        except:
            print(f"[{dt.datetime.now()}] ERROR {r.text}")
            raise

    def get_swap_tx(self, quote, use_shared_accounts):
        r = requests.post(
            f"{BASE_URL}/swap", json={
                'userPublicKey': PUBKEY,
                'wrapAndUnwrapSol': True,
                'useSharedAccounts': use_shared_accounts,
                'quoteResponse': quote,
                'prioritizationFeeLamports': 50_000_000 # 0.05 SOL
            }
        )
        try:
            return r.json()['swapTransaction']
        except KeyError:
            print(f"error getting swap tx {r.json()}")
            raise

    async def swap(self, quote, use_shared_accounts=True):
        swap_tx = self.get_swap_tx(quote, use_shared_accounts=use_shared_accounts)
        if swap_tx is None:
            return False
        raw_tx = solders.transaction.VersionedTransaction.from_bytes(base64.b64decode(swap_tx))
        signature = kp.sign_message(solders.message.to_bytes_versioned(raw_tx.message))
        signed_tx = solders.transaction.VersionedTransaction.populate(raw_tx.message, [signature])

        try:
            txid = await self.solana_client.send_transaction(
                signed_tx,
                opts=TxOpts(skip_confirmation=True, skip_preflight=True, max_retries=3),
            )
            print(json.loads(txid.to_json())['result'])
            return True
        except UnconfirmedTxError:
            return False
        except SolanaRpcException:
            return False
        return False
