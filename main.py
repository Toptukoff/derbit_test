import asyncio
import websockets
import json
import ssl
import asyncpg

# Отключаем проверку сертификата
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class DeribitRequest:
    def __init__(self, index_name):
        self.message = {
            'jsonrpc': '2.0',
            'method': 'public/get_index_price',
            'params': {
                'index_name': index_name
            }
        }

    def to_json(self):
        return json.dumps(self.message)

btc_request = DeribitRequest('btc_usd').to_json()
eth_request = DeribitRequest('eth_usd').to_json()

async def call_api(message):
    try:
        async with websockets.connect(
            'wss://test.deribit.com/ws/api/v2',
            ssl=ssl_context
        ) as websocket:
            await websocket.send(message)
            response = await websocket.recv()
            data = json.loads(response)
            return data
    except (websockets.exceptions.WebSocketException, asyncio.TimeoutError) as e:
        print(f"Ошибка при получении данных: {e}")
        return None


async def safe_db(data, ticker):
    if data and 'result' in data:
        try:
            conn = await asyncpg.connect(
                user='deribit',
                password='deribit',
                database='deribit',
                host='localhost',
                port='5433'
            )
            index_price = data['result']['index_price']
            timestamp = data['usIn']

            await conn.execute('''
                INSERT INTO deribit (ticker, index_price, timestamp)
                VALUES($1, $2, $3)
            ''', ticker, index_price, timestamp)
            await conn.close()
        except Exception as e:
            print(f"Ошибка при сохранении в БД: {e}")
    else:
        print("Некорректные данные:", data)


async def main():
    while True:
        btc_response, eth_response = await asyncio.gather(call_api(btc_request), call_api(eth_request))
        await asyncio.gather(
            safe_db(btc_response, 'btc_usd'),
            safe_db(eth_response, 'eth_usd')
        )
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
