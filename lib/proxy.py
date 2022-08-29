import asyncio
import aiohttp
from os.path import basename
from fake_useragent import UserAgent
from lib.common import get_logger, semaphore

logger = get_logger(basename(__file__))
ua = UserAgent()


async def tt_request(url, session, method='get', headers=None, params={}, data={}, res='json', number = 100):
    try:
        if not headers:
            headers = {}
            headers['user-agent'] = ua.random
        else:
            headers['user-agent'] = ua.random

        async with semaphore:
            try:
                logger.info('scraping %s', url)
                for i in range(100):
                    print(f'次数：{i}')
                    try:
                        if method == 'get':
                            async with session.get(url=url, headers=headers, params=params, ssl=False) as response:
                                if response.status >= 500:
                                    logger.error('Stop!')
                                    return
                                elif response.status == 200:
                                    if res == 'json':
                                        return await response.json()
                                    elif res == 'text':
                                        text = await response.text()
                                        return text[:5]
                                    else:
                                        return response

                                elif response.status == 404 and i > 3:
                                    # 重新获取cookie
                                    return -1

                                else:
                                    await asyncio.sleep(0.5)
                                    logger.error(f'url: {url}, status: {response.status}')
                        elif method == 'post':
                            async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                                if response.status >= 500:
                                    logger.error('Stop!')
                                    return
                                elif response.status == 200:
                                    if res == 'json':
                                        return await response.json()
                                    elif res == 'text':
                                        return await response.text()
                                    else:
                                        return response
                                else:
                                    await asyncio.sleep(0.5)
                                    logger.error(f'url: {url}, status: {response.status}')
                    except asyncio.TimeoutError:
                        logger.info(f'Timeout url:{url}')
                else:
                    logger.info(f'{url} 超过次数限制')
                    return {}
            except Exception as e:
                logger.error(f'error occurred while scraping {url}, {e}')
                return {}
    except Exception as e:
        logger.error(e)
        return {}

async def test():
    timeout = aiohttp.ClientTimeout(total=5)
    session = aiohttp.ClientSession(timeout=timeout)
    scrape_tasks = [tt_request(url='https://www.baidu.com', res='text', session=session) for i in range(10)]
    res_list = await asyncio.gather(*scrape_tasks)
    print(res_list)
    await session.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(test())