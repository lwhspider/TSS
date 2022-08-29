import aiohttp
import asyncio
import datetime
from lib.proxy import tt_request
from conf.config import TEA_COOKIE, TEA_EMAIL
from db.operator_mysql import save_mysql, read_mysql
import core.Teacher_Assistants_Tea_PTA_Set_Score as SS


async def get_request(page, cookie_value, session):

    url = 'https://pintia.cn/api/problem-sets/admin?sort_by=%7B%22type%22%3A%22START_AT%22%2C%22asc%22%3Afalse%7D&page=' + str(page) + '&limit=15&filter=%7B%22ownerId%22%3A%220%22%2C%22stage%22%3A%7B%22stage%22%3A%22NORMAL%22%7D%7D'

    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
    }
    return await tt_request(url, headers=headers, session=session)

def change_At(updateAt):
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    utcTime = datetime.datetime.strptime(updateAt, UTC_FORMAT)
    localtime = utcTime + datetime.timedelta(hours=8)
    return str(localtime)


# 获取题集列表
async def get_set_list(user_pta_id, groups_set_list, cookie_value, session):
    groups_set_list = groups_set_list[:]
    set_ian = []
    set_list = []
    # 遍历用户每一页
    for page in range(1000000):
        try:
            obj = await get_request(page, cookie_value, session)
            # 提取每一页所有题集的 id 和 name
            if len(obj['problemSets']) == 0:
                print('已爬取所有存在的题集的信息!!!!')
                break
            b = False
            for o in obj['problemSets']:
                if len(groups_set_list) == 0:
                    b = True
                    break
                if o['id'] not in groups_set_list:
                    continue
                del groups_set_list[groups_set_list.index(o['id'])]
                del set_ian[:]
                Score, total = await SS.get_set_score(o['id'], cookie_value, session)
                createAt = change_At(o['createAt'])
                endAt = change_At(o['endAt'])
                set_ian.append(o['id'])
                set_ian.append(o['name'])
                set_ian.append(createAt)
                set_ian.append(endAt)
                set_ian.append(Score)
                set_ian.append(total)
                set_list.append(set_ian[:])
            if b:
                print('已爬取所有题集的信息!!!!')
                break
        except:
            print('已爬取所有题集的信息')
            break
    for se in set_list:
        print(se)
    insert_srt_content(set_list, user_pta_id)


def insert_srt_content(set_list, user_pta_id):
    set_list_t = []
    for i in set_list:
        i.append(user_pta_id)
        set_list_t.append(tuple(i))
    sql = 'insert ignore into questions_set (set_id, set_title, set_start_time, set_deadline, set_total_score,' \
          ' set_ques_number, set_creator) values(%s, %s, %s, %s, %s, %s, %s)'
    save_mysql(sql, set_list_t)
    print('用户组题集信息已存入数据库!')

async def run():
    user_id = TEA_EMAIL
    sql = 'select user_pta_id from user where user_email = %s'
    try:
        user_pta_id = read_mysql(sql, user_id)[0]
    except:
        user_pta_id = '974885479287754752'
    groups_set_list = ['1497051785460846592', '1497071691120119808']
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_set_list(user_pta_id, groups_set_list, TEA_COOKIE, session=session) for i in range(13)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())