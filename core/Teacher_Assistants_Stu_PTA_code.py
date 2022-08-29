import asyncio
import aiohttp
from conf.config import TEA_COOKIE
from lib.proxy import tt_request


async def get_request(set_id, submit_id, cookie_value, session):
    url = 'https://pintia.cn/api/submissions/' + submit_id + '?'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + set_id + '/submissions',
    }

    return await tt_request(url, headers=headers, session=session)


async def get_code(set_id, submit_id, cookie_value, session):
    obj = await get_request(set_id, submit_id, cookie_value, session)
    detail = 'programmingSubmissionDetail'
    if obj['submission']['submissionDetails'][0].get('programmingSubmissionDetail') == None:
        detail = 'codeCompletionSubmissionDetail'
    code = obj['submission']['submissionDetails'][0][detail]['program']
    print(code)
    return code


async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_code('1442680080946384896', '1449393639393927168', TEA_COOKIE, session=session) for i in range(20)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())