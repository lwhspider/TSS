import aiohttp
import asyncio
from lib.proxy import tt_request
from conf.config import TEA_COOKIE


async def get_request(page, cookie_value, session):
    if page == 0:
        url = 'https://pintia.cn/api/user-groups?limit=30&filter=%7B%22visible%22%3Atrue%7D'
        referer_value = 'https://pintia.cn/user-groups'
    else:
        url = 'https://pintia.cn/api/user-groups?page=' + str(page) + '&limit=30&filter=%7B%22visible%22%3Atrue%7D'
        referer_value = 'https://pintia.cn/user-groups?page=' + str(page)

    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': referer_value,
    }

    return await tt_request(url=url, headers=headers, session=session)


async def get_groups_list(cookie_value, session):
    groups_list = []
    for page in range(100):
        obj = await get_request(page, cookie_value, session=session)
        groups = []
        for i in obj['userGroups']:
            del groups[:]
            groups.append(i['id'])
            groups.append(i['name'])
            groups_list.append(groups[:])
        if len(obj['userGroups']) != 30:
            print("班级爬取结束")
            break
    return groups_list

async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_groups_list(TEA_COOKIE, session=session) for i in range(20)]
    set_list = await asyncio.gather(*scrape_tasks)
    print(set_list)
    await session.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())