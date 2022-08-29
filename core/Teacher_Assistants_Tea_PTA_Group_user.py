import aiohttp
import asyncio
from lib.proxy import tt_request
from db.operator_mysql import save_mysql
from conf.config import TEA_COOKIE


async def get_request(page, group_id, cookie_value, session):
    referer_value = 'https://pintia.cn/user-groups/' + group_id + '/members'
    if page == 0:
        url = 'https://pintia.cn/api/user-groups/' + group_id + '/members?filter=%7B%22scope%22%3A%22STUDENT_USER%22%7D&' \
                                                            'scope=STUDENT_USER&limit=30'
    else:
        url = 'https://pintia.cn/api/user-groups/' + group_id + '/members?filter=' \
              '%7B%22scope%22%3A%22STUDENT_USER%22%7D&scope=STUDENT_USER&page=' + str(page) + '&limit=30'
        referer_value = referer_value + '?page=' + str(page)

    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': referer_value,
    }

    return await tt_request(url, headers=headers, session=session)

async def get_group_user(group_id, cookie_value, session):
    group_user = []
    for page in range(100):
        obj = await get_request(page, group_id, cookie_value, session)
        if len(obj['members']) == 0:
            break
        user = []
        for i in obj['members']:
            del user[:]
            user.append(i['user']['id'])
            user.append(i['studentUser']['name'])
            group_user.append(user[:])
    # print(group_user)
    insert_group_user(group_user, group_id)


def insert_group_user(group_user, group_id):
    group_user_tuple = []
    for i in group_user:
        i.append(group_id)
        group_user_tuple.append(tuple(i))
    sql = 'insert ignore into pta_groups (user_pta_id, user_name, group_id) values (%s, %s, %s)'
    save_mysql(sql, group_user_tuple)
    print('用户组成员已存入数据库！')

async def run():
    groud_id = '1500768847425310720'
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_group_user(groud_id, TEA_COOKIE, session=session) for i in range(13)]
    await asyncio.gather(*scrape_tasks)
    await session.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())