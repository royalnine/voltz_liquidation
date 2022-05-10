import aiohttp
import asyncio
from typing import Coroutine, List
from dataclasses import dataclass
from typing import List, Optional, Dict
from decimal import Decimal
from dataclasses_json import dataclass_json


BASE_QUERY = '''{
      positions(first: 100) {
        id
        tickLower {
          value
        }
        tickUpper {
          value
        }
        margin
        owner {
          id
        }
      }
    }'''


class VoltzQuery(str):
    pass


class GraphClient:

    
    def __init__(self, url: str):
        self.url = url

    async def fetch_positions(self, query: VoltzQuery):
        async with aiohttp.ClientSession() as session:
            coro = self.get_coro(session, query)
            resp = await coro
            data = await resp.json()

        breakpoint()    
        return resp
            
    def get_coro(self, session: aiohttp.ClientSession, query: VoltzQuery) -> Coroutine:
        coro = session.post(self.url, json={'query': query})
        return coro


async def run():
    client = GraphClient('https://api.thegraph.com/subgraphs/name/voltzprotocol/voltz-kovan')
    response = await client.fetch_positions(BASE_QUERY)
    
asyncio.run(run())