import aiohttp
import asyncio
from os.path import basename
from lib.common import get_logger
from lib.proxy import tt_request
from conf.config import STU_COOKIE

logger = get_logger(basename(__file__))


async def get_request(set_id, coookie_value, session):
    url = 'https://pintia.cn/api/problem-sets/' + set_id + '/exams'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': coookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + set_id,
    }
    return await tt_request(url=url, headers=headers, session=session)


async def get_request_question(set_id, exam_id, type_id, coookie_value, session):
    # 还差几种题目类型，但是感觉没必要加
    problem_type = ['', 'TRUE_OR_FALSE', 'MULTIPLE_CHOICE', 'MULTIPLE_CHOICE_MORE_THAN_ONE_ANSWER', 'FILL_IN_THE_BLANK',
                    'FILL_IN_THE_BLANK_FOR_PROGRAMMING', 'CODE_COMPLETION', 'PROGRAMMING']
    if type_id >= 6:
        url = 'https://pintia.cn/api/problem-sets/' + set_id + '/problem-list?exam_id=' + exam_id + '&problem_type=' + problem_type[type_id] + '&limit=100'
    else:
        url = 'https://pintia.cn/api/problem-sets/' + set_id + '/problems?exam_id=' + exam_id + '&problem_type=' + problem_type[type_id]
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': coookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + set_id + '/problems/type/' + str(type_id),
    }
    return await tt_request(url=url, headers=headers, session=session)


async def get_request_num(set_id, cookie_value, session):
    url = 'https://pintia.cn/api/problem-sets/' + set_id + '/exam-problem-status?'
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': 'https://pintia.cn/problem-sets/' + set_id,
    }
    return await tt_request(url=url, headers=headers, session=session)


# 获取完成的题目的列表
async def get_exam_id(set_list, cookie_value, session):
    exam_list = []
    que_list = []
    try:
        # 遍历题目id和名称
        for set in set_list:
            # 获取题集exam_id
            obj = await get_request(set[0], cookie_value, session=session)
            # 记录题集得分、完成提数等信息
            data = []
            del data[:]
            try:
                data.append(set[0])
                data.append(set[1])
                data.append(obj['exam']['score'])
            except KeyError:
                print('未填写 ', set[1])
                continue
            # 获取题目的对错信息
            obj_num = await get_request_num(set[0], cookie_value,session)
            cou = 0
            right_que = []
            for num in obj_num.get('problemStatus', []):
                # 记录正确题目的名称
                if num['problemSubmissionStatus'] == 'PROBLEM_ACCEPTED':
                    right_que.append(num['id'])
                    cou += 1
            data.append(cou)
            # 获取函数题和编程题的title
            for type_id in range(6, 8):
                obj_que = await get_request_question(set[0], obj['exam']['id'], type_id, cookie_value, session)
                que_data = []
                for que in obj_que.get('problemSetProblems', []):
                    del que_data[:]
                    if que['id'] in right_que:
                        que_data.append(set[0])
                        que_data.append(que['id'])
                        que_data.append((que['title']))
                        que_list.append(que_data[:])
            exam_list.append(data[:])
        return exam_list, que_list
    except Exception as e:
        logger.error(f'get_exam_id  error：{e}')
        return [], []

async def run():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_exam_id([['1507035666164760576', '题目类型'], ['1181729963034562560', '19级《程序设计基础》第3章（顺序）练习']], STU_COOKIE, session=session) for i in range(20)]
    set_list = await asyncio.gather(*scrape_tasks)
    print(set_list)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())