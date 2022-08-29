import pymysql
from conf.config import MYSQL_DATABASE, MYSQL_PORT, MYSQL_USER, MYSQK_HOST, MYSQL_PASSWORD


def save_mysql(sql, data):
    conn = pymysql.connect(host=MYSQK_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
                               charset='gbk')
    cur = conn.cursor()
    if isinstance(data, tuple):
        cur.execute(sql, data)
    elif isinstance(data, list):
        cur.exeuctemany()
    conn.commit()
    conn.commit()
    cur.close()
    conn.close()

def read_mysql(sql, data=None, mothed='one'):
    conn = pymysql.connect(host=MYSQK_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
                               charset='gbk')
    cur = conn.cursor()
    cur.execute(sql, data)
    if mothed == 'all':
        return cur.fetchall()
    return cur.fetchone()