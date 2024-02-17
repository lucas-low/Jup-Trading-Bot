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
import sys

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
def read_keypair_from_file(keypath='./key'):
    try:
        with open(keypath, 'r') as key_file:
            address = key_file.readline().strip()
            exported_secret = key_file.readline().strip()

            if not address or not exported_secret:
                raise ValueError("Key file is incomplete. It must contain a public address and an exported secret key.")

            # print(f"Address: {address}")
            # print(f"Exported Secret (Base58): {exported_secret}")

            exported_bytes = base58.b58decode(exported_secret)
            keypair = Keypair.from_bytes(exported_bytes)

            # Sanity check
            if str(keypair.pubkey()) != address:
                raise ValueError(f"Public key does not match the address in the key file. {keypair.pubkey()} != {address}")

            return keypair

    except FileNotFoundError:
        raise FileNotFoundError(f"The key file at {keypath} was not found.")
    except ValueError as e:
        raise ValueError(f"Error reading keypair: {e}")

# Use the function to read the keypair
try:
    keypair = read_keypair_from_file()
    # Proceed with using `keypair` for further operations...
except Exception as error:
    print(f"An error occurred while reading the keypair: {error}")
    sys.exit(1)

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

    def get_quote_buy(self):
        try:
            start_dt = dt.datetime.now()
            amt = int(self.amount_to_buy_usdc * (10 ** USDC_DECIMALS))
            r = requests.get(f"{BASE_URL}/quote?inputMint={USDC_ADDRESS}&outputMint={JUP_ADDRESS}&amount={amt}&slippageBps={self.slippage}&swapMode=ExactIn")
            print(f"[{dt.datetime.now()}] Took {(dt.datetime.now() - start_dt).total_seconds():.2f} seconds for BUY quote")
            r.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code.
            data = r.json()
            if 'error' in data:
                print(f"[{dt.datetime.now()}] {data}")
                return None
            return data
        except requests.HTTPError as http_err:
            print(f"[{dt.datetime.now()}] HTTP error occurred: {http_err}")
            return None
        except Exception as err:
            print(f"[{dt.datetime.now()}] Other error occurred: {err}")
            return None

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
            r.raise_for_status()
            return r.json()['swapTransaction']
        except requests.HTTPError as http_err:
            print(f"[{dt.datetime.now()}] HTTP error occurred: {http_err}")
            return None
        except KeyError:
            print(f"error getting swap tx {r.json()}")
            return None

    async def swap(self, quote, use_shared_accounts=True):
        swap_tx = self.get_swap_tx(quote, use_shared_accounts=use_shared_accounts)
        if swap_tx is None:
            return False
        raw_tx = solders.transaction.VersionedTransaction.from_bytes(base64.b64decode(swap_tx))
        signature = keypair.sign_message(solders.message.to_bytes_versioned(raw_tx.message))
        signed_tx = solders.transaction.VersionedTransaction.populate(raw_tx.message, [signature])

        try:
            txid = await self.solana_client.send_transaction(
                signed_tx,
                opts=TxOpts(skip_confirmation=False, skip_preflight=False, max_retries=3),
            )
            print(f"Transaction ID: {json.loads(txid.to_json())['result']}")
            return True
        except UnconfirmedTxError as e:
            print(f"Transaction could not be confirmed: {e}")
            return False
        except SolanaRpcException as e:
            print(f"RPC exception occurred: {e}")
            return False

    #     # Simulated method
    # def get_quote_buy(self):
    #     # ... [other simulation setup code] ...
    #     # Instead of making an actual request, return a simulated response
    #     return {
    #         'inAmount': '500000',  # Simulated amount in USDC (5 USDC)
    #         'outAmount': '1500000',  # Simulated amount out in JUP (15 JUP)
    #         'otherAmountThreshold': '1400000',  # Simulated slippage threshold amount
    #     }

    # # Simulated method
    # async def swap(self, quote, use_shared_accounts=True):
    #     # Log the action instead of executing it
    #     print(f"Simulated swap with quote: {quote}")
    #     # Return a simulated transaction ID or result
    #     return "SimulatedTxId1234"