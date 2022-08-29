import datetime
import time
import os
import sys
import asyncio
import aiohttp
from db.operator_mysql import save_mysql,read_mysql

Source_path = os.path.dirname(os.path.dirname(__file__))
# 添加路径，便于导包
sys.path.append(Source_path)

import pymysql
import sys
import core.Teacher_Assistants_PTA_LoginToCookie as LTC
import core.Teacher_Assistants_Stu_PTA_Set_Content as SC
import core.Teacher_Assistants_Stu_PTA_id as SID
import core.Teacher_Assistants_Stu_PTA_Exams as PE
import core.Teacher_Assistants_Judge_TOS as TOS

import core.Teacher_Assistants_Tea_PTA_id as TID
import core.Teacher_Assistants_Tea_PTA_Groups as TG
import core.Teacher_Assistants_Tea_PTA_Group_Set as TGS
import core.Teacher_Assistants_Tea_PTA_Groups_Set_Content as GSC
import core.Teacher_Assistants_Tea_PTA_Submit_List as TSL
import core.Teacher_Assistants_Tea_PTA_Group_user as TGu


def get_list():
    if len(sys.argv) == 1:
        # 从数据库取出每一个用户的基本信息
        sql = 'select user_email, user_pta_id, user_pta_account, user_pta_password, user_pta_cookie, user_status from user'
        return read_mysql(sql, mothed='all')
    return [[sys.argv[1], None, sys.argv[2], sys.argv[3], None, None]]

def update_user(key, value, user_email):
    sql = 'update user set ' + key + ' = %s where user_email = %s'
    save_mysql(sql, (value, user_email))
    print('用户pta的', key, '已更新!')


def insert_set_data(user_pta_id, exam_list):
    # 还没设置为遇到相同的数据就替换
    sql = 'replace  into performance (set_id, set_name, score, completed_number, user_pta_id ) values (%s, %s, %s, %s, %s)'
    exam_list_t = []
    for i in exam_list:
        i.append(user_pta_id)
        exam_list_t.append(tuple(i))
    save_mysql(sql, exam_list_t)
    print('题集信息存入数据库!')


def insert_que_data(user_pta_id, que_list):
    sql = 'insert ignore into completed_topic (set_id, ques_id, ques_title, user_id) values (%s, %s, %s, %s)'
    que_list_t = []
    for i in que_list:
        i.append(user_pta_id)
        que_list_t.append(tuple(i))
    save_mysql(sql, que_list_t)
    print('完成的题目存入数据库!')


async def spider_stu( user_pta_id, user_pta_cookie, active, session):
    # 4、生成学生活跃题集id和name的列表
    set_list = await SC.get_set_list(user_pta_cookie, active, session)
    # 5、学生完成题目列表
    exam_list, que_list = await PE.get_exam_id(set_list, user_pta_cookie, session=session)
    if len(exam_list) != 0:
        insert_set_data(user_pta_id, exam_list)
    if len(que_list) != 0:
        insert_que_data(user_pta_id, que_list)


# 将用户组列表添加到数据库
def insert_groups(user_id, groups_list):
    # 还没设置为遇到相同的数据就替换
    sql = 'replace  into teacher_groups (group_id, group_name, user_pta_id) values (%s, %s, %s)'
    exam_list_t = []
    for i in groups_list:
        i.append(user_id)
        exam_list_t.append(tuple(i))
    save_mysql(sql, exam_list_t)
    print('老师用户组存入数据库!')

async def spider_tea(user_email, user_pta_id, user_pta_cookie, active, session):
    # 1、获取老师用户组list
    groups_list = await TG.get_groups_list(user_pta_cookie, session)
    # 将用户组保存到数据库
    insert_groups(user_pta_id, groups_list)

    # 2、爬取老师创建班级所绑定的用户组所对应的题集id和name
    sql = 'select groups_id from classes where class_owner = %s'
    groups_tuple = read_mysql(sql, user_email, mothed='all')
    for groups_id in groups_tuple:
        await TGS.get_groups_set_list(groups_id[0], user_pta_cookie, session)
        time.sleep(0.5)
        await TGu.get_group_user(groups_id[0], user_pta_cookie, session)
        time.sleep(0.5)

    time.sleep(3)
    # 3、爬取创建班级所绑定用户组所对应的题集信息
    sql = 'select set_id from class_set a join classes b on a.groups_id = b.groups_id where class_owner = %s group by set_id'
    grous_set_tuple = read_mysql(sql, user_email, mothed='all')
    grous_set_id_list = []
    for grous_set_id in grous_set_tuple:
        grous_set_id_list.append(grous_set_id[0])
    await GSC.get_set_list(user_pta_id, grous_set_id_list[:], user_pta_cookie, session)

    # 4、获取老师活跃题集的内容并保存
    # set_list = TSC.get_set_list(user_pta_id, user_pta_cookie)

    # 5、获取老师活跃题集的提交记录并保存到数据库，然后再分析出异常记录，获取信息并保存到数据库
    # active = False
    for set_id in grous_set_id_list:
        # 如果是第一次爬取，则保存题集的所有提交记录
        if not active:
            ri_list = await TSL.get_submit_list(set_id, user_pta_cookie, session=session)
        # 如果不是第一次，则爬取每日的提交记录
        else:
            # 获取前一天的时间
            last_oneday = datetime.datetime.now() - datetime.timedelta(days=1)
            ri_list = await TSL.get_submit_list(set_id, user_pta_cookie, last_time=last_oneday, session=session)
        # 分析出异常信息的列表
        stu_abnormal = await TSL.get_stu_abnormal(ri_list)
        # 将异常的数据存进数据库
        await TSL.insert_abnormal_record(set_id, stu_abnormal, user_pta_cookie, session=session)
        time.sleep(0.5)


async def get_user_info(user, session):
    user_pta_id = user[1]
    user_pta_cookie = user[4]
    user_pta_status = user[5]

    first_spider = False
    active = True
    if user_pta_id == None:
        first_spider = True
    # 如果没有绑定过账号，则不爬取
    if user[2] == None:
        return

    # 判断是不是第一次爬取
    if first_spider:
        active = False
        try:
            # 1、获取cookie的值
            user_pta_cookie = LTC.get_pta_cookies(user[2], user[3])
        except:
            # 将用户pta账号密码不正确存入数据库
            update_user('user_pta_is_correct', 0, user[0])
            if len(sys.argv) == 1:
                return
            else:
                # 如果是在绑定时密码出错，则返回-1
                exit('pta账号密码不正确！')

        # 2、判断用户是老师还是学生
        user_pta_status = await TOS.get_status(user_pta_cookie, session=session)

        # 3、将用户的基本信息存进数据库
        if user_pta_status == 0:
            user_pta_id = await SID.get_PTA_id(user[0], user_pta_cookie, session=session)
        else:
            user_pta_id = await TID.get_PTA_id(user[0], user_pta_cookie, session=session)

    # 不是第一次爬
    else:
            # 响应一个页面，判断cookie有没有失效
        if await SC.get_request(0, user_pta_cookie, active, session= session) == -1:
            print('cookie失效')
            try:
                # 1、获取cookie的值
                user_pta_cookie = LTC.get_pta_cookies(user[2], user[3])
                # 2、更新用户pta的cookie
                update_user('user_pta_cookie', user_pta_cookie, user[0])
            except:
                # 将用户pta账号密码不正确存入数据库
                update_user('user_pta_is_correct', 0, user[0])
                if len(sys.argv) == 1:
                    return
                else:
                    # 如果是在绑定时密码出错，则返回-1
                    exit('pta账号密码不正确！')

    if user_pta_status == 0:
        await spider_stu(user_pta_id, user_pta_cookie, active, session)
    elif user_pta_status == 1:
        await spider_tea(user[0], user_pta_id, user_pta_cookie, active, session)



async def run():
    user_list = get_list()
    print(user_list)

    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)

    scrape_tasks = [get_user_info(user=user, session=session) for user in user_list]
    await asyncio.gather(*scrape_tasks)

    await session.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())