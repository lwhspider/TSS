import sys
import aiohttp
import asyncio
from lib.proxy import tt_request
from conf.config import TEA_COOKIE
from db.operator_mysql import save_mysql, read_mysql
import core.Teacher_Assistants_Tea_PTA_Groups_Set_Content as GSC


def insert_groups_set(groups_id, groups_set_list):
    # 还没设置为遇到相同的数据就替换
    sql = 'insert ignore into class_set (set_id, set_name, groups_id) values (%s, %s, %s)'
    groups_set_list_t = []
    for i in groups_set_list:
        i.append(groups_id)
        groups_set_list_t.append(tuple(i))
    save_mysql(sql, groups_set_list_t)
    print('用户组的题集存入数据库!')

async def get_request(page, class_id, cookie_value, session):
    if page:
        url = 'https://pintia.cn/api/user-groups/' + str(class_id) + '/permissions?limit=100'
        referer_value = 'https://pintia.cn/user-groups/' + str(class_id) + '/permissions'
    else:
        url = 'https://pintia.cn/api/user-groups/' + str(class_id) + '/permissions?page=' + str(page) + '&limit=100'
        referer_value = 'https://pintia.cn/user-groups/' + str(class_id) + '/permissions?page=' + str(page)

    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': referer_value,
    }

    return await tt_request(url=url, headers=headers, session=session)



async def get_groups_set_list(class_id, cookie_value, session):
    groups_set_list = []
    groups_set_id_list = []
    for page in range(10):
        obj = await get_request(page, class_id, cookie_value, session)
        groups_set = []
        b = False
        # 如果第一个题集id == 前一页第一个题集id 则结束爬取, 防止存在最后一页的题集数等于100的情况
        if page > 0 and len(obj['permissions']) > 0 and before_id == obj['permissions'][0]['problemSet']['id']:
            b = True
        if len(obj['permissions']) > 0:
            before_id = obj['permissions'][0]['problemSet']['id']
        for i in obj['permissions']:
            if b:
                break
            del groups_set[:]
            groups_set_id_list.append(i['problemSet']['id'])
            groups_set.append(i['problemSet']['id'])
            groups_set.append(i['problemSet']['name'])
            groups_set_list.append(groups_set[:])
        if len(obj['permissions']) != 100 or b:
            print(("用户组题目集列表爬取结束!"))
            break
    # 存入数据库
    insert_groups_set(class_id, groups_set_list)
    # print(groups_set_id_list)
    return groups_set_id_list



async def one_crawl(user_pta_id, groups_id, session):
    '''
        单独获取老师用户组的题集
    :return:

    '''
    sql = 'select user_pta_cookie from user where user_pta_id = %s'
    # 从数据库获取cookie
    cookie_value = read_mysql(sql, user_pta_id)[0]
    # 获取用户组的题集
    groups_set_id_list = await get_groups_set_list(groups_id, cookie_value[0], session)
    # 将用户组的题集信息存入数据库
    await GSC.get_set_list(user_pta_id, groups_set_id_list, cookie_value[0])


async def run():
    user_pta_id = sys.argv[1]
    groups_id = sys.argv[2]
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [one_crawl(user_pta_id, groups_id, session=session)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

async def test():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_groups_set_list('1515197281077719040', TEA_COOKIE, session=session) for i in range(20)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    # 传入user_id和班级对应的用户组id
    if len(sys.argv) > 1:
        asyncio.get_event_loop().run_until_complete(run())
    else:
        asyncio.get_event_loop().run_until_complete(test())
        exit('请传入参数!!!!!')
