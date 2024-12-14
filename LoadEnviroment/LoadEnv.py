import json
import os

cas_baseurl = ""
pan_sso_service = ""
username = ""
password = ""
cas_cookie_path = ""
pan_baseurl = ""
mysql_host = ""
mysql_port = ""
mysql_username = ""
mysql_password = ""
jwt_secret_key = ""
server_env = "development",
pan_host = "",
wechat_webhook_service = "",
wechat_webhook_service_token = "",
wechat_send_group = "",
chromedriver_path = None


# 读取 .env.json 文件
def load_env_json(filepath):
    global cas_baseurl, pan_host, pan_sso_service, username, password, cas_cookie_path, pan_baseurl, \
        mysql_host, mysql_port, mysql_username, mysql_password, \
        jwt_secret_key, server_env, \
        wechat_webhook_service, wechat_webhook_service_token, wechat_send_group, \
        chromedriver_path
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # 将内容加载到环境变量中
        cas_baseurl = data['cas_baseurl']
        pan_sso_service = data['pan_sso_service']
        username = data['username']
        password = data['password']
        cas_cookie_path = data['cas_cookie_path']
        pan_baseurl = data['pan_baseurl']
        mysql_host = data['mysql_host']
        mysql_port = data['mysql_port']
        mysql_username = data['mysql_username']
        mysql_password = data['mysql_password']
        jwt_secret_key = data['jwt_secret_key']
        server_env = data['server_env']
        pan_host = data['pan_host']
        wechat_webhook_service = data['wechat_webhook_service']
        wechat_webhook_service_token = data['wechat_webhook_service_token'],
        wechat_send_group = data['wechat_send_group']
        chromedriver_path = data['chromedriver_path'] if data['use_customize_chromedriver'] is True else None


# 默认加载 .env.json 文件（可选）
_default_env_path = os.path.join(os.getcwd(), '.env.json')
print(_default_env_path)
if os.path.exists(_default_env_path):
    print("Successfully loaded .env.json")
    load_env_json(_default_env_path)

# 向外暴露的内容
__all__ = [
    "cas_baseurl",
    "pan_sso_service",
    'username',
    'password',
    "jwt_secret_key",
    'cas_cookie_path',
    'server_env',
    'mysql_host',
    'mysql_port',
    'mysql_username',
    'mysql_password',
    'pan_host',
    'wechat_webhook_service',
    'wechat_webhook_service_token',
    'chromedriver_path'
]
