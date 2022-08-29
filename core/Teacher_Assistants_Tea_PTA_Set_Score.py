import aiohttp
import asyncio
from lib.proxy import tt_request
from conf.config import TEA_COOKIE

async def get_request(Set_Id, cookie_value, session):

    url = 'https://pintia.cn/api/problem-sets/' + str(Set_Id) + '/problem-summaries'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + str(Set_Id) + '/manage',
    }

    return await tt_request(url, headers=headers, session=session)

# 获取题集列表
async def get_set_score(Set_Id, cookie_value, session):
    obj = await get_request(Set_Id, cookie_value, session)
    Score = 0.0
    total = 0
    for i in list(obj['summaries'].keys()):
        Score += obj['summaries'][i]['totalScore']
        total += obj['summaries'][i]['total']
    # print(Score, ' ', total)
    return Score, total

async def run():
    Set_Id = '1497051785460846592'
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_set_score(Set_Id, TEA_COOKIE, session=session) for i in range(20)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())