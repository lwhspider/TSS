from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from conf.config import CHROME_PATH, DRIVER_PATH
import requests
import time
import numpy
import cv2

'''
建议网速好一点执行此程序，否则可能会get不到资源导致程序终端或者get到的题目和答案为空
question_list_url   题目列表链接（只能是编程题的链接，其他题型同理判断一下即可我这里没写）
file_name   要保存的文件名，我使用的markdown格式
access_interval     根据网速自定义设置，访问每到题的时间间隔s，访问太快总会被提示，不过我写了出现提示继续访问的逻辑；
'''


def share_browser():

    '''
    功能：生成无头浏览器
    :return: browser
    '''

    # 创建Options对象
    chrome_options = Options()

    # 这两个参数是用来设置无界面的
    chrome_options.add_argument('headless')
    chrome_options.add_argument('disable‐gpu')

    # 将本机的Chrome路径传入Options的binary_location中
    chrome_options.binary_location = CHROME_PATH
    # 将chromedriver的路径传入，或者将该文件放到与脚本同一目录下，并传入Option对象
    browser = webdriver.Chrome(DRIVER_PATH, options=chrome_options)
    return browser


def pta_login(browser, account_number, password):
    '''
    功能：登陆并破解滑动登陆
    :param browser:无头浏览器
    :param account_number: 账号
    :param password: 密码
    :return:
    '''
    # 隐式等待：没找到元素在这个时间内继续找，超出时间抛出异常
    browser.implicitly_wait(5)
    # 打开登陆页面
    browser.get('https://pintia.cn/auth/login')
    # 获取账号密码的输入框
    zh = browser.find_element_by_xpath('//*[@id="username"]')
    mm = browser.find_element_by_xpath('//*[@id="password"]')

    # 在PTA的账号密码：
    for i in account_number:
        time.sleep(0.01)
        zh.send_keys(i)
    for i in password:
        time.sleep(0.01)
        mm.send_keys(i)

    time.sleep(1)
    # 找到登录按钮并点击两下
    browser.find_element_by_xpath('//*[@id="sparkling-daydream"]/div[2]/div/div[2]/form/div[2]/button').click()
    browser.find_element_by_xpath('//*[@id="sparkling-daydream"]/div[2]/div/div[2]/form/div[2]/button').click()

    # 破解滑动验证
    for i in range(10):
        # 等待一会，时间间隔可根据网速调整，验证码加载完成
        time.sleep(1)

        print('当前url:' + browser.current_url)
        # 如果当前url没变说明验证未通过，循环5（可修改）次重新验证
        if (browser.current_url != 'https://pintia.cn/auth/login'):
            break
        print('破解第:' + str(i) + '次')

        for wait_number in range(5):
            # bg背景图片
            bg_img_src = browser.find_element_by_xpath(
                '/html/body/div[@style="display: block;"]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/img[1]').get_attribute(
                'src')
            # front可拖动图片
            front_img_src = browser.find_element_by_xpath(
                '/html/body/div[@style="display: block;"]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/img[2]').get_attribute(
                'src')
            try:
                # 保存图片，图片用二进制生成
                with open("bg.jpg", mode="wb") as f:
                    f.write(requests.get(bg_img_src).content)
                with open("front.jpg", mode="wb") as f:
                    f.write(requests.get(front_img_src).content)
            except:
                print("等待加载图片第", wait_number, "次！")
                time.sleep(1)


        # 将图片加载至内存
        bg = cv2.imread("bg.jpg")
        front = cv2.imread("front.jpg")

        # 将背景图片转化为灰度图片，将三原色降维
        bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        # 将可滑动图片转化为灰度图片，将三原色降维
        front = cv2.cvtColor(front, cv2.COLOR_BGR2GRAY)
        front = front[front.any(1)]
        # 用cv算法匹配精度最高的xy值
        result = cv2.matchTemplate(bg, front, cv2.TM_CCOEFF_NORMED)
        # numpy解析xy，注意xy与实际为相反，x=y,y=x
        x, y = numpy.unravel_index(numpy.argmax(result), result.shape)
        # 找到可拖动区域
        div = browser.find_element_by_xpath(
            '/html/body/div[@style="display: block;"]/div[2]/div/div/div[2]/div/div[2]/div[2]')
        # 拖动滑块，以实际相反的y值代替x
        ActionChains(browser).drag_and_drop_by_offset(div, xoffset=y // 0.946, yoffset=0).perform()

# 废弃
# 返回我的题集的cookie
def get_pta_Historical_Problem_set_cookies(browser, set_all=False):
    # 点击我的题集
    browser.find_element_by_xpath('//*[@id="sparkling-daydream"]/div[2]/div[1]/div/div[1]/div/div[1]/a[2]').click()
    if set_all :
        # 点击所有题集
        browser.find_element_by_xpath('//*[@id="sparkling-daydream"]/div[2]/div[1]/div/div[1]/div/div[3]/select[2]/option[2]').click()
    print('当前的url：', browser.current_url)
    value = ''
    for line in browser.get_cookies():
        str = line['name'] + '=' + line['value']
        value = value + str + ';'

    return value


# 获取的pta首页的cookie
def get_pta_cookies(account_number, password):
    '''
    功能：返回cookie的值
    :param account_number: 账号
    :param password: 密码
    :return: cookie_value
    '''

    browser = share_browser()
    # 登陆
    pta_login(browser, account_number, password)
    print('登陆成功')
    cookie_list = browser.get_cookies()
    value = ''
    for line in cookie_list:
        if line['name'] == 'PTASession':
            str = line['name'] + '=' + line['value']
            value = value + str + ';'
            break
    return value


if __name__ == '__main__':
    # 浏览器和驱动器的路径
    browser = share_browser()
    account_number = '1210376319@qq.com'
    password = 'lwh835524'
    # 登陆
    # pta_login(browser, account_number, password)
    print(get_pta_cookies(account_number, password))
    # print('登陆成功')
    # cookie_value = get_pta_Historical_Problem_set_cookies(browser)
    # print(get_pta_cookies(account_number, password))
