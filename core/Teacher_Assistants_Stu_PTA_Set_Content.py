import datetime
import asyncio
import aiohttp
from conf.config import STU_COOKIE
from lib.proxy import tt_request


async def get_request(page, cookie_value, active, session):
    data = {}
    if active:
        now_datetime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:00.000Z')
        url = 'https://pintia.cn/api/problem-sets?'
        if page == 0:
            data = {
                'filter': '{"problemSetCategoryId":"0","endAtAfter":"' + now_datetime + '"}',
                'limit': 30,
                'order_by': 'END_AT',
                'asc': 'true'
            }
            referer_value = 'https://pintia.cn/problem-sets?tab=1&filter=active'
        else:
            data = {
                'filter': '{"problemSetCategoryId":"0","endAtAfter":"' + now_datetime + '"}',
                'page': str(page),
                'limit': 30,
                'order_by': 'END_AT',
                'asc': 'true'
            }
            referer_value = 'https://pintia.cn/problem-sets?tab=1&filter=active&page=' + str(page)
    else:
        if page == 0:
            url = 'https://pintia.cn/api/problem-sets?filter=%7B%22problemSetCategoryId%22%3A%220%22%7D&limit=30&order_by=END_AT&asc=true'
            referer_value = 'https://pintia.cn/problem-sets?tab=1&filter=all'
        else:
            url = 'https://pintia.cn/api/problem-sets?filter=%7B%22problemSetCategoryId%22%3A%220%22%7D&page=' + str(page) + '&limit=30&order_by=END_AT&asc=true'
            referer_value = 'https://pintia.cn/problem-sets?tab=1&filter=all&page=' + str(page)

    headers = {
        'accept': ' application/json;charset=UTF-8',
        'accept-language': ' zh-CN',
        'content-type': ' application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': referer_value,
    }

    return await tt_request(url=url, headers=headers, params=data, session=session)

# 提取有用数据并将一个题目的信息作为一个字典
def get_item_dict(content):
    c = content['problemSetProblem']
    item_dict = {
        'id': c['id'],
        'label': c['label'],
        'score': c['score'],
        'title': c['title'],
        'content': c['content']
    }
    return item_dict


# 获取题集列表
async def get_set_list(cookie_value, active, session):
    set_list = []
    # 遍历用户每一页
    for page in range(10000000):
        # 将 json 数据转换为 python数据
        obj = await get_request(page, cookie_value, active, session=session)
        set_ian = []
        # 提取每一页所有题集的 id 和 name
        for o in obj['problemSets']:
            del set_ian[:]
            set_ian.append(o['id'])
            set_ian.append(o['name'])
            set_list.append(set_ian[:])
        if len(obj['problemSets']) != 30 or len(set_ian) == 0:
            print('已爬取所有题集id和name')
            break
    return set_list

async def run():
    # 测试get_set_list
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_set_list(STU_COOKIE, False, session=session)]
    set_list = await asyncio.gather(*scrape_tasks)
    print(set_list)
    await session.close()

async def test():
    # 测试判断cookie失效
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_request(0, STU_COOKIE, False, session=session) for i in range(10)]
    set_list = await asyncio.gather(*scrape_tasks)
    print(set_list)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(test())