import aiohttp
import asyncio
from lib.proxy import tt_request
from conf.config import STU_COOKIE, STU_EMAIL
from db.operator_mysql import save_mysql

def save_data(data):
    sql = 'update user set user_status = %s, user_pta_cookie = %s, user_student_id = %s, user_unit = %s, user_true_name = %s, user_pta_id = %s, user_pta_is_correct = %s where user_email = %s'
    save_mysql(sql,data)
    print("学生的学号，真实姓名，单位等基本已存进数据库!")



async def get_PTA_id(user_email, cookie_value, session):
    url = 'https://pintia.cn/api/student-users/bindings'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/home/bindings',
    }
    obj = await tt_request(url=url, headers=headers, session=session)
    studentNumber = obj['studentUsers'][0]['studentNumber']
    school_name = obj['studentUsers'][0]['organization']['name']
    user_name = obj['studentUsers'][0]['name']
    user_Id = obj['studentUsers'][0]['userId']
    data = [0, cookie_value, studentNumber, school_name, user_name, user_Id, 1, user_email]
    print(data)
    save_data(data)
    return user_Id


async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    user_email = STU_EMAIL
    scrape_tasks = [get_PTA_id(user_email, STU_COOKIE, session=session) for i in range(10)]
    await asyncio.gather(*scrape_tasks)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())