import asyncio
from aiohttp import ClientSession


def read_wallets():
    with open("wallets.txt", "r") as file:
        return [wallet.strip().lower() for wallet in file.read().split("\n")]


def parse_sui_balance(balances: list):
    for balance in balances:
        try:
            if balance["coinType"] == "0x2::sui::SUI":
                return round(int(balance["totalBalance"]) / 10 ** 9, 2)
        except Exception:
            return 0
    return 0


async def get_balances(session: ClientSession, address: str):
    json_data = {
        'jsonrpc': '2.0',
        'id': '13',
        'method': 'suix_getAllBalances',
        'params': [
            address,
        ],
    }
    async with session.post("https://explorer-rpc.mainnet.sui.io/", json=json_data) as res:
        try:
            r = await res.json()
            return r["result"]
        except Exception:
            return []


async def get_transactions(session: ClientSession, address: str):
    json_data = {
        'jsonrpc': '2.0',
        'id': '17',
        'method': 'suix_queryTransactionBlocks',
        'params': [
            {
                'filter': {
                    'FromAddress': address,
                },
                'options': {
                    'showEffects': True,
                    'showInput': True,
                },
            },
            None,
            100,
            True,
        ],
    }
    async with session.post("https://explorer-rpc.mainnet.sui.io/", json=json_data) as res:
        try:
            r = await res.json()
            return r["result"]["data"]
        except Exception:
            return []


async def handle_wallet(session: ClientSession, address: str):
    balances, transactions = await asyncio.gather(
        get_balances(session, address),
        get_transactions(session, address)
    )
    return address, balances, transactions

async def run_all(addresses: list):
    async with ClientSession() as session:
        tasks = [handle_wallet(session, address) for address in addresses]
        results = await asyncio.gather(*tasks)
        return results


def main():
    wallets = read_wallets()
    asyncio_result = asyncio.run(run_all(addresses=wallets))
    
    result = []

    for address, balances, transactions in asyncio_result:
        parsed_balance = parse_sui_balance(balances)
        num_transactions = len(transactions)
        result.append(f"{address};{parsed_balance};{num_transactions}")

    with open("result.txt", "w") as file:
        file.write("address;SUI balance;txs\n")
        for entry in result:
            file.write(f"{entry}\n")

if __name__ == "__main__":
    print("Начата обработка...")
    main()
    print("Результат записан в файл 'result.txt'")
