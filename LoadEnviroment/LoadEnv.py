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

# 读取 .env.json 文件
def load_env_json(filepath):
    global cas_baseurl, pan_sso_service, username, password, cas_cookie_path, pan_baseurl, mysql_host, mysql_port, mysql_username, mysql_password, jwt_secret_key
    with open(filepath, 'r') as f:
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
]
