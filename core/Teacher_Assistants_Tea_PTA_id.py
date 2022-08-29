import aiohttp
import asyncio
from lib.proxy import tt_request
from conf.config import TEA_COOKIE, TEA_EMAIL
from db.operator_mysql import save_mysql


def save_data(data):
    sql = 'update user set user_status = %s, user_pta_cookie = %s, user_unit = %s, user_pta_id = %s, user_pta_is_correct = %s where user_email = %s'
    save_mysql(sql,data)
    print("老师的基本已存进数据库!")



async def get_PTA_id(user_email, cookie_value, session):
    url = 'https://pintia.cn/api/users/profile'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/home/account',
    }
    obj = await tt_request(url=url, headers=headers, session=session)
    # print(obj)
    school_name = obj['organization']['name']
    user_Id = obj['bindings']['WECHAT']['userId']
    data = [1, cookie_value, school_name, user_Id, 1, user_email]
    save_data(data)
    return user_Id

async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    user_email = TEA_EMAIL
    scrape_tasks = [get_PTA_id(user_email, TEA_COOKIE, session=session) for i in range(20)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())