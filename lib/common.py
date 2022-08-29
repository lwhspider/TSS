import os
import logging
import asyncio
from conf.config import CONCURRENCY
from datetime import datetime

semaphore = asyncio.Semaphore(CONCURRENCY)

def get_logger(file_name):
    logger = logging.getLogger()
    log_level = logging.INFO
    logger.setLevel(log_level)
    logger_name = f'..{os.sep}log{os.sep}{datetime.now().strftime("%Y-%m-%d")}_{file_name[:-3]}.log'
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s | %(lineno)d | %(message)s')
    fh = logging.FileHandler(logger_name)  # 创建一个handler，用于写入日志文件
    ch = logging.StreamHandler()  # 创建一个handler,用于输出到控制台
    fh.setLevel(log_level)
    ch.setLevel(log_level)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger