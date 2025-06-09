import os
import ssl
import subprocess
import urllib.parse
import urllib3
import json
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

from LoadEnviroment.LoadEnv import cas_cookie_path, server_env
from .globals import username, password, pan_sso_service, cas_baseurl, pan_baseurl, des_trans_mode
from CasService import headers
from CasService.DES import get_des_key
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta

local_headers = headers

# 忽略 InsecureRequestWarning 警告
warnings.simplefilter('ignore', InsecureRequestWarning)


class CustomHttpAdapter(HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_new_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
    ctx.check_hostname = False
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    session.headers.update(local_headers)
    return session


def get_csrf_token_and_execution(service):
    session = get_new_session()
    req = session.get(cas_baseurl, params={"service": service},
                      verify=False)
    soup = BeautifulSoup(req.text, 'html.parser')

    # 查找 input 元素，获取 id 为 'lt' 的 value 属性
    csrf_tag = soup.find('input', {'id': 'lt'})
    if csrf_tag:
        csrf_token = csrf_tag.get('value')
    else:
        csrf_token = None
        print("Input element with id 'lt' not found.")
    exec_tag = soup.find('input', {'name': 'execution'})
    if exec_tag:
        execution = exec_tag.get('value')
    else:
        execution = None
        print("Input element with name 'execution' not found.")

    return csrf_token, execution, session


def try_redirect(session, location):
    if location is None:
        return session, None
    if location and location.startswith('/#/sso'):
        location = "https://cas.shitac.net" + location
    res = session.get(location, verify=False, allow_redirects=False)
    location = res.headers.get('Location')
    if server_env == 'development':
        print(f"Redirect Location: {location}")
    return session, location


def get_sso_ticket(session):
    # access https://pan.shitac.net/sso
    session, location = try_redirect(session, pan_sso_service)
    # access cas service to auth https://pan.shitac.net/sso
    session, location = try_redirect(session, location)
    # get pan.shitac.net SSO Ticket
    session, location = try_redirect(session, location)
    ticket_id = location.split('=')[-1]
    return session, ticket_id


def save_cookies_as_json(tokenid: str, expires_sec: int):
    # 准备 cookies 数据格式
    cookies_list = []
    token_json = {
        "domain": "pan.shitac.net",
        "httpOnly": False, "name":
            "tokenid", "path": "/",
        "sameSite": "Lax",
        "secure": False,
        "value": tokenid,
        "expiry": 0
    }
    expiry_time = datetime.now() + timedelta(seconds=expires_sec - 200)
    token_json['expiry'] = int(expiry_time.timestamp())
    default_json = {
        "domain": "pan.shitac.net",
        "httpOnly": False,
        "name": "lastVisitedOrigin",
        "path": "/",
        "sameSite": "Lax",
        "secure": False,
        "value": "https%3A%2F%2Fpan.shitac.net"
    }
    cookies_list.append(token_json)
    cookies_list.append(default_json)
    try:
        with open(cas_cookie_path, 'w') as file:
            json.dump(cookies_list, file, ensure_ascii=False)
    except Exception as e:
        print("cannot save tokenid cookie.")
        print(e)

    print(f"Cookies have been saved to '{cas_cookie_path}'")


def get_token_id(ticket_id: str):
    data = {
        "thirdpartyid": "as-shitac",
        "params": {"ticket": ""},
        "deviceinfo": {"ostype": 6}
    }
    data['params']['ticket'] = ticket_id
    req = requests.post(pan_baseurl + "/auth1", verify=False, params={"method": "getbythirdparty"}, json=data)
    return req.json(), req.status_code


def cas_login(username: str, password: str, service: str):
    csrf_token, execution, session = get_csrf_token_and_execution(service)
    if des_trans_mode == "nodejs":
        path = os.path.join(os.getcwd(), "CasService", "des.js").replace("\\", "/")
        cmd = [
            'node',
            '-e',
            f"require('{path}').strEnc('{username.strip()}{password.strip()}{csrf_token}', '1', '2', '3')"
        ]
        rsa = subprocess.run(cmd, capture_output=True, text=True, shell=False).stdout.strip()
    else:
        rsa = get_des_key(username.strip(), password.strip(), csrf_token)
    # 使用 session 进行后续的请求
    data = {
        'rsa': rsa,
        'ul': len(username),
        'pl': len(password),
        'lt': csrf_token,
        "execution": execution,
        "_eventId": "submit"
    }
    # 发送 POST 请求，cookies 会自动包含在请求头中
    local_headers['Referer'] = cas_baseurl + "?service=" + urllib.parse.quote(service, safe='')
    local_headers['Content-Type'] = "application/x-www-form-urlencoded"
    res = session.post("https://cas.shitac.net/tpass/login", params={"service": service},
                       data=data, verify=False, headers=local_headers, allow_redirects=False)
    # 获取 Location 头（如果存在）
    location = res.headers.get('Location')
    if location is not None and location.endswith("h5?act=tpass/guide"):
        # (Try to go to CAS Guide, but no ticket.)
        session, location = try_redirect(session, location)
        # (CAS Guide Login)
        session, location = try_redirect(session, location)
        # act=tpass/guide&ticket=ST-*****-******-tpass (Using CAS Guide SSO Ticket)
        session, location = try_redirect(session, location)
        # https://cas.shitac.net/tp_tpass/h5?act=tpass/guide
        session, location = try_redirect(session, location)
        res = session.get("https://cas.shitac.net/tpass/login", params={"service": service},
                          verify=False, headers=local_headers, allow_redirects=False)
        location = res.headers.get('Location')
        session, location = try_redirect(session, location)
        session, location = try_redirect(session, location)
    elif res.status_code == 200:
        res = session.get("https://cas.shitac.net/tpass/login", params={"service": service},
                          verify=False, headers=local_headers, allow_redirects=False)
        location = res.headers.get('Location')
        session, location = try_redirect(session, location)
        session, location = try_redirect(session, location)

    session, location = try_redirect(session, location)
    session, location = try_redirect(session, location)
    return session


def loginAndSetCookie():
    session = cas_login(username, password, pan_sso_service)
    session, ticket_id = get_sso_ticket(session)
    req, code = get_token_id(ticket_id)
    if code == 200:
        save_cookies_as_json(req['tokenid'], req['expires'])
    else:
        print("get cas sso tokenid failed")
