import sys
import asyncio
import aiohttp
from lib.proxy import tt_request
from conf.config import STU_COOKIE
from db.operator_mysql import save_mysql, read_mysql


async def get_request(set_id, que_id, cookie_value, session):
    url = 'https://pintia.cn/api/problem-sets/' + set_id + '/problems/' + que_id
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + set_id + '/problems/' + que_id,
    }

    return await tt_request(url=url, headers=headers, session=session)


def from_database_cookie(user_id):
    sql = 'select user_pta_cookie from user where user_pta_id = %s'
    return read_mysql(sql, user_id)[0]


# 添加收藏题目
def insert_que(que_tuple):
    sql = 'insert into bookmarked_submission_records (ques_id, user_id, ques_content, ques_code) values(%s, %s, %s, %s)'
    save_mysql(sql, que_tuple)
    print('已收藏题目!')


async def get_ques_content(user_id, set_id, que_id, session):
    try:
        cookie_value = from_database_cookie(user_id)
    except TypeError:
        # 返回0表示改用户未绑定pta
        return 0, 0
    obj = await get_request(set_id, que_id, cookie_value, session)
    ques_title = obj['problemSetProblem']['title']
    ques_content = obj['problemSetProblem']['content']
    return ques_title, ques_content


async def crawl_one(user_id, set_id, que_id, session):
    cookie_value = from_database_cookie(user_id)
    # cookie_value = STU_COOKIE
    obj =await get_request(set_id, que_id, cookie_value, session)
    que_content = obj['problemSetProblem']['content']

    detail = 'programmingSubmissionDetail'
    if obj['problemSetProblem']['lastSubmissionDetail'].get(detail) == None:
        detail = 'codeCompletionSubmissionDetail'

    que_code = obj['problemSetProblem']['lastSubmissionDetail'][detail]['program']
    que_tuple = (set_id, user_id, que_content, que_code)
    print(que_tuple)
    insert_que(que_tuple)

async def run():
    user_id = sys.argv[1]
    set_id = sys.argv[2]
    que_id = sys.argv[3]
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [crawl_one(user_id, set_id, que_id, session=session)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

async def test():
    user_id = '1182519575940190208'
    set_id = '1181135511882584064'
    que_id = '1181136291268153344'
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [crawl_one(user_id, set_id, que_id, session=session) for i in range(10)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    # 传入用户和题目信息信息
    if len(sys.argv) > 1:
        asyncio.get_event_loop().run_until_complete(run())
    else:
        asyncio.get_event_loop().run_until_complete(test())
        exit('请传入正确的参数')