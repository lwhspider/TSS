import time
import asyncio
import aiohttp
import datetime
from conf.config import STU_COOKIE, TEA_COOKIE
from lib.proxy import tt_request
from db.operator_mysql import save_mysql
import core.Teacher_Assistants_Stu_PTA_code as Scode
import core.Teacher_Assistants_Stu_PTA_Item_Content as SIC


async def get_request(set_id , page, cookie_value, before, session):
    if page == 0:
        url = 'https://pintia.cn/api/problem-sets/' + str(set_id) + '/submissions?show_all=true&limit=50&filter=%7B%7D'
        referer_value ='https://pintia.cn/problem-sets/' + str(set_id) + '/submissions'
    else:
        url = 'https://pintia.cn/api/problem-sets/' + str(set_id) + '/submissions?show_all=true&before=' + before + '&limit=50&filter=%7B%7D'
        referer_value = 'https://pintia.cn/problem-sets/' + str(set_id) + '/submissions?' + before


    headers = {
        'accept': 'application/json;charset=UTF-8',
        'accept-language': 'zh-CN',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie_value,
        'referer': referer_value,
    }

    return await tt_request(url=url, headers=headers, session=session)


async def get_submit_list(set_id, cookie_value, session, last_time=datetime.datetime.strptime('2000-03-20T07:10:23Z', "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=8)):
    '''

    :param set_id: 题集id
    :param cookie_value:
    :param last_time: 上一次最晚的提交记录
    :return:
    '''

    submit_list = []
    ri_list = []
    before = '0'    # 上一页的最后一次提交记录
    for page in range(10000):
        try:
            obj = await get_request(set_id, page, cookie_value, before, session)
            count_submit = len(obj['submissions'])

            # 提交记录的信息，用于异常判断
            recorded_information = []

            for i in obj['submissions']:
                utc = i['submitAt']
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
                utcTime = datetime.datetime.strptime(utc, UTC_FORMAT)
                localtime_date = utcTime + datetime.timedelta(hours=8)

                # 爬取提交记录最早时间
                if localtime_date <= last_time:
                    count_submit = 1
                    break
                localtime = str(localtime_date)

                # 未提交成功的记录去除掉
                if i.get('problemSetProblem') == None:
                    continue
                if i['status'] == 'ACCEPTED':
                    status = 1
                else:
                    status = 0
                submit = (i['id'], i['user']['user']['id'], i['problemSetProblem']['id'], localtime, status, set_id)
                submit_list.append(submit[:])

                del recorded_information[:]
                recorded_information.append(i['user']['user']['id']),
                recorded_information.append(i['problemSetProblem']['id'])
                recorded_information.append(status)
                recorded_information.append(i['score'])
                recorded_information.append(localtime_date)
                recorded_information.append(i['id'])
                recorded_information.append(i['problemSetProblem']['label'])
                recorded_information.append(i['user']['studentUser']['name'])
                ri_list.append(recorded_information[:])

            if count_submit != 50:
                print("提交记录爬取结束!")
                break
            before = obj['submissions'][49]['id']
            time.sleep(1)
        except:
            print("网址无效，提交记录爬取结束!")
            break

    # 保存到数据库
    insert_submit_list(submit_list)
    return ri_list


def insert_submit_list(submit_list):
    sql = 'insert ignore into submit_record (record_id, user_pta_id, ques_id, submit_time, submit_state, set_id) values' \
          ' (%s, %s, %s, %s, %s, %s)'
    save_mysql(sql, submit_list)
    print("提交记录已经存入数据库!")

async def get_stu_abnormal(ri_list):
    stu_ques = {}
    for i in ri_list:
        # 将答题错误的状态设为-1, 分数设为0
        status = 1
        score = i[3]
        if i[2] == 0:
            status = -1
            score = 0.0

        # 判断该学生存不存在
        if stu_ques.get(i[0]) == None:
            stu_ques[i[0]] = {i[1]: [status, score, i[4], i[5], i[4], i[6], i[7]], 'last_ques_id': i[1]}

        else:
            # 判断该学生是否记录了该题的id
            if stu_ques[i[0]].get(i[1]) == None:
                stu_ques[i[0]][i[1]] = [status, score, i[4], i[5], i[4], i[6], i[7]]
            # 同一道题，将题目的信息更新为最早一次的正确的信息
            elif i[2] == 1 and stu_ques[i[0]][i[1]][0] >= 0:
                stu_ques[i[0]][i[1]] = [status, score, i[4], i[5], i[4], i[6], i[7]]
            # 将题目信息改为状态为正确的信息
            elif i[2] == 1 and stu_ques[i[0]][i[1]][0] < 0:
                stu_ques[i[0]][i[1]] = [status, score, i[4], i[5], i[4], i[6], i[7]]
            # 如果一直不正确，则叠加错误的次数：
            elif i[2] == 0 and stu_ques[i[0]][i[1]][0] < 0:
                stu_ques[i[0]][i[1]][0] -= 1
                stu_ques[i[0]][i[1]][4] = i[4]
            # 如果之前有错误，则记录题目的最早提交时间
            elif i[2] == 0 and stu_ques[i[0]][i[1]][0] >= 0:
                stu_ques[i[0]][i[1]][4] = i[4]

            # 上一个提交记录与现在的提交记录进行比较，判断出作弊则将这道题的status == 0
            if stu_ques[i[0]][stu_ques[i[0]]['last_ques_id']][0] == 1 and i[1] != stu_ques[i[0]]['last_ques_id'] and (stu_ques[i[0]][stu_ques[i[0]]['last_ques_id']][2] - i[4]) < datetime.timedelta(minutes=2) and stu_ques[i[0]][stu_ques[i[0]]['last_ques_id']][1] >= 15:
                stu_ques[i[0]][stu_ques[i[0]]['last_ques_id']][0] = 0

            # 将上一个提交记录的信息改为当前题目
            stu_ques[i[0]]['last_ques_id'] = i[1]
    stu_abnormal = []
    for s in stu_ques:
        for q in stu_ques[s]:
            if q == 'last_ques_id':
                continue
            if stu_ques[s][q][0] == 0 or stu_ques[s][q][0] < -9:
                stu_abnormal.append([s, q, stu_ques[s][q][3], str(stu_ques[s][q][4]), str(stu_ques[s][q][2]), stu_ques[s][q][0], stu_ques[s][q][5], stu_ques[s][q][6]])
    return stu_abnormal


async def insert_abnormal_record(set_id, stu_abnormal, cookie_value, session):
    now_date = str(datetime.datetime.now().strftime('%Y-%m-%d'))
    abnormal_list = []
    for abnormal in stu_abnormal:
        # 通过提交记录id爬取学生的代码
        code = Scode.get_code(set_id, abnormal[2], cookie_value, session)

        # 通过pta_id获取学生的cookie，再通过学生的题目id获取题目内容
        try:
            ques_title, ques_content = await SIC.get_ques_content(abnormal[0], set_id, abnormal[2], session)
        except:
            ques_title = 0
        if ques_title == 0:
            ques_title = abnormal[6]
            ques_content = '用户未绑定不能获取题目内容!'
        abnormal_list.append((abnormal[0], abnormal[1], abnormal[2], abnormal[3], abnormal[4], abnormal[5],abnormal[7],
                              ques_title, ques_content, code, set_id, now_date))

    sql = 'insert ignore into abnormal_records (user_pta_id, ques_id, submit_id, start_time, end_time, submit_number,' \
          ' user_name ,ques_title, ques_content, ques_code, set_id, abnormal_date) values (%s, %s, %s, %s, %s, %s, %s' \
          ', %s, %s, %s, %s, %s)'
    save_mysql(sql, abnormal_list)
    print('异常记录存入成功')

async def run():
    set_id = '1503179517895417856'
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [get_submit_list(set_id, TEA_COOKIE, session=session) for i in range(1)]
    await asyncio.gather(*scrape_tasks)
    await session.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())
    # stu_abnormal = get_stu_abnormal(ri_list)
    # insert_abnormal_record('1503179517895417856', stu_abnormal, cookie_value)