import json
from CasService import *
from CasService.CasLogin import get_new_driver

with open(cas_cookie_path) as f:
    driver = get_new_driver()
    # 打开网站
    driver.get('https://pan.shitac.net')

    for cookie in json.loads(f.read()):
        cookie.pop("sameSite", None)
        cookie.pop("httpOnly", None)
        driver.add_cookie(cookie)

    # 刷新页面以便新cookie生效
    driver.refresh()
    input("回车退出")
    driver.quit()
