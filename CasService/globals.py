from selenium.webdriver.chrome.service import Service
from LoadEnviroment.LoadEnv import cas_baseurl, pan_sso_service, cas_cookie_path, username, password, chromedriver_path, pan_baseurl
from selenium import webdriver
from selenium_stealth import stealth


def get_new_driver():
    """创建并返回一个新的 WebDriver 实例"""
    try:
        # 创建WebDriver实例
        service = Service(executable_path=chromedriver_path)
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("--window-size=1920x1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(options=options, service=service)

        stealth(driver,
                languages=["zh-CN", "cn"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        return driver

    except Exception as e:
        print(f"无法启动 WebDriver: {e}")
        return None


headers = {
    # "Accept": "*/*",
    "Accept-Encoding": "gzip,deflate,zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Host": "cas.shitac.net",
    "Origin": "https://cas.shitac.net",
    "Referer": "https://cas.shitac.net/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
}

# 向外暴露的内容
__all__ = [
    'cas_baseurl',
    'pan_baseurl',
    'pan_sso_service',
    'cas_cookie_path',
    'headers',
    'get_new_driver',
    "username",
    "password"
]
