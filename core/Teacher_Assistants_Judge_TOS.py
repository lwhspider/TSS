import asyncio
import aiohttp
from conf.config import STU_COOKIE, TEA_COOKIE
from lib.proxy import tt_request

async def get_request(cookie_value, session):
    url = 'https://pintia.cn/api/user-groups?limit=3&filter=%7B%22visible%22%3Atrue%7D'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
    }
    return await tt_request(url, headers=headers, session=session)

async def get_status(cookie_value, session):
    if await get_request(cookie_value, session) != -1:
        status = 1
    else:
        status = 0
    print(status)
    return status


async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_status(STU_COOKIE, session=session) for i in range(10)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())