from LoadEnviroment.LoadEnv import cas_login_method
from .globals import headers, cas_baseurl, pan_sso_service, username, password, get_new_driver
from datetime import datetime, timedelta
from .CasLoginByRequests import loginAndSetCookie
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

cookies_dict = {}


def wait_for_network_idle(driver, timeout=10, check_interval=0.5):
    WebDriverWait(driver, timeout, poll_frequency=check_interval).until(
        lambda d: d.execute_script(
            "return window.performance.getEntriesByType('resource').every(res => res.responseEnd > 0);"
        )
    )


def setCasCookie():
    global cookies_dict
    driver = get_new_driver()
    try:
        # 打开目标网站
        driver.get(cas_baseurl + pan_sso_service)

        # 定位用户名和密码输入框，并输入数据
        username_element = driver.find_element(By.ID, "un")
        password_element = driver.find_element(By.ID, "pd")
        time.sleep(2)
        username_element.send_keys(username)  # 替换为实际用户名
        time.sleep(2)
        password_element.send_keys(password)  # 替换为实际密码
        # 单击登录按钮
        login_button = driver.find_element(By.CLASS_NAME, "login_box_landing_btn")
        login_button.click()
        wait_for_network_idle(driver)  # 等待网络活动完成
        time.sleep(2)
        driver.get(cas_baseurl + pan_sso_service)
        # wait_for_network_idle(driver)  # 等待网络活动完成
        time.sleep(2.5)
        cookies = driver.get_cookies()
        # 查找并修改 tokenid Cookie，添加过期时间
        for cookie in cookies:
            if cookie['name'] == 'tokenid':
                # 设置过期时间为 20 分钟后
                expiry_time = datetime.now() + timedelta(minutes=20)
                cookie['expiry'] = int(expiry_time.timestamp())
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        time.sleep(3)
        driver.close()
        with open("./SITC-Cas.json", 'w') as file:
            json.dump(cookies, file, ensure_ascii=False)

        return headers, cookies_dict

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        # 关闭浏览器
        driver.quit()


def checkCookieExpired(cookies=None, white_list: list = []):
    if not cookies:
        return True

    for cookie in cookies:
        if cookie['name'] in white_list:
            continue
        expiry_time = cookie.get('expiry')
        # is_http_only = cookie.get('httpOnly', False)

        if expiry_time and expiry_time <= time.time():
            print(f"cookie '{cookie['name']}' has expired.")
            return True

    return False


def loadLocalCasCookie(check_expired=True):
    global cookies_dict, headers
    try:
        with open('./SITC-Cas.json', 'r') as file:
            cookies = json.load(file)
            if check_expired and checkCookieExpired(cookies) and cas_login_method == "selenium":
                return setCasCookie()
            elif check_expired and checkCookieExpired(cookies) and cas_login_method == "requests":
                return loginAndSetCookie()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return headers, cookies_dict
    except (FileNotFoundError, json.JSONDecodeError):
        if cas_login_method == "requests":
            return loginAndSetCookie()
        else:
            return setCasCookie()


def get_tokenid():
    global cookies_dict
    loadLocalCasCookie(True)
    tokenid_value = cookies_dict.get('tokenid')
    return tokenid_value
