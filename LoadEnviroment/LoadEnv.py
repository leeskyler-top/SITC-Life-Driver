import json
import os

cas_baseurl = ""
pan_sso_service = ""
des_trans_mode = "js2py"
username = ""
password = ""
cas_cookie_path = ""
pan_baseurl = ""
mysql_host = "127.0.0.1"
mysql_port = 3306
mysql_username = "root"
mysql_password = ""
mysql_use_ssl = False
mysql_ssl_ca = ""
mysql_ssl_cert = ""
mysql_ssl_key = ""
mysql_ssl_verify_cert = ""
redis_host = "127.0.0.1"
redis_port = 6379
redis_username = "default"
redis_password = ""
redis_use_ssl = False
redis_ssl_ca = ""
redis_ssl_cert = ""
redis_ssl_key = ""
redis_db = 0
jwt_secret_key = ""
server_env = "development",
pan_host = "",
wechat_webhook_service = "",
chromedriver_path = None
cas_login_method = "requests",
refresh_token_exp_sec = 1800
access_token_exp_sec = 180
save_histories = False
save_histories_days = 7
save_histories_count = None
rar_path = ""
upload_folder = ""
backend_aes_key = ""
hmac_secret_key = ""
cloudflare_worker_baseurl = ""
cloudflare_worker_secret = ""
ms_tenant_id = ""
ms_client_id = ""
ms_client_secret = ""
ms_client_secret_type = "secret"
storage = "local"
server_aes_rsa_private_key = ""


# 读取 .env.json 文件
def load_env_json(filepath):
    global cas_baseurl, pan_host, pan_sso_service, username, password, cas_cookie_path, pan_baseurl, \
        mysql_host, mysql_port, mysql_username, mysql_password, \
        mysql_use_ssl, mysql_ssl_ca, mysql_ssl_cert, mysql_ssl_key, mysql_ssl_verify_cert, \
        redis_host, redis_port, redis_username, redis_password, redis_use_ssl, redis_ssl_ca, redis_ssl_cert, redis_ssl_key, redis_db, \
        jwt_secret_key, server_env, \
        wechat_webhook_service, \
        chromedriver_path, cas_login_method, des_trans_mode, \
        refresh_token_exp_sec, access_token_exp_sec, rar_path, \
        save_histories, save_histories_days, save_histories_count, upload_folder, \
        hmac_secret_key, ms_tenant_id, ms_client_id, ms_client_secret, ms_client_secret_type, storage, \
        cloudflare_worker_baseurl, cloudflare_worker_secret, backend_aes_key, \
        server_aes_rsa_private_key

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # 将内容加载到环境变量中
        cas_baseurl = data['cas_baseurl']
        cas_login_method = data['cas_login_method']
        des_trans_mode = data['des_trans_mode']
        pan_sso_service = data['pan_sso_service']
        username = data['username']
        password = data['password']
        cas_cookie_path = data['cas_cookie_path']
        pan_baseurl = data['pan_baseurl']
        mysql_host = data['mysql_host']
        mysql_port = data['mysql_port']
        mysql_username = data['mysql_username']
        mysql_password = data['mysql_password']
        mysql_use_ssl = data['mysql_use_ssl']
        mysql_ssl_ca = data['mysql_ssl_ca']
        mysql_ssl_cert = data['mysql_ssl_cert']
        mysql_ssl_key = data['mysql_ssl_key']
        mysql_ssl_verify_cert = data['mysql_ssl_verify_cert']
        redis_host = data['redis_host']
        redis_port = data['redis_port']
        redis_username = data['redis_username']
        redis_password = data['redis_password']
        redis_use_ssl = data['redis_use_ssl']
        redis_ssl_ca = data['redis_ssl_ca']
        redis_ssl_cert = data['redis_ssl_cert']
        redis_ssl_key = data['redis_ssl_key']
        redis_db = data['redis_db']
        jwt_secret_key = data['jwt_secret_key']
        server_env = data['server_env']
        pan_host = data['pan_host']
        wechat_webhook_service = data['wechat_webhook_service']
        chromedriver_path = data['chromedriver_path'] if data['use_customize_chromedriver'] is True and data[
            'cas_login_method'] == "selenium" else None
        refresh_token_exp_sec = data['refresh_token_exp_sec']
        access_token_exp_sec = data['access_token_exp_sec']
        save_histories = data['save_histories']
        save_histories_days = data['save_histories_days']
        save_histories_count = data['save_histories_count']
        rar_path = data['rar_path']
        upload_folder = data['upload_folder']
        hmac_secret_key = data['hmac_secret_key']
        backend_aes_key = bytes.fromhex(data['backend_aes_key'])
        assert len(backend_aes_key) == 32, "密钥必须是32字节"
        cloudflare_worker_secret = data['cloudflare_worker_secret']
        cloudflare_worker_baseurl = data['cloudflare_worker_baseurl']
        ms_tenant_id = data['ms_tenant_id']
        ms_client_id = data['ms_client_id']
        ms_client_secret_type = data['ms_client_secret_type']
        ms_client_secret = data['ms_client_secret']
        storage = data['storage']
        server_aes_rsa_private_key = data['server_aes_rsa_private_key']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)


# 默认加载 .env.json 文件（可选）
_default_env_path = os.path.join(os.getcwd(), '.env.json')
print(_default_env_path)
if os.path.exists(_default_env_path):
    print("Successfully loaded .env.json")
    load_env_json(_default_env_path)
