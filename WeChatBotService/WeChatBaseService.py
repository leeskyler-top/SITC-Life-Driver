from .globals import wechat_webhook_service, wechat_webhook_service_token
import requests

headers = {
    'Content-Type': 'application/json',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

def reqApi(name, method, params={}, headers=headers, data=None, json={}, files=None):
    params['token'] = wechat_webhook_service_token
    if method == "GET":
        req = requests.get(wechat_webhook_service + name, params=params, verify=False, headers=headers)
        return req, req.status_code
    elif method == "POST":
        req = requests.post(wechat_webhook_service + name, data=data, json=json, params=params, files=files, headers=headers,
                            verify=False)
        return req, req.status_code

def check_health():
    req, code = reqApi("/healthz", "GET")
    try:
        if code == 200 and req.text == "healthy":
            return True, code
        else:
            return False, code
    except:
        return False, code

import requests

def msgV1(to, isRoom, content):
    """
    发送 POST 请求，通过 Webhook 上传文件。
    :param to: 目标
    :param isRoom: 是否是群聊
    :param content: 文件路径或文件数据
    """
    # 健康检查
    status, code = check_health()
    if not status:
        return False, "微信登录失效", code

    try:
        # 如果 content 是文件路径，打开文件
        if isinstance(content, str):
            content_file = open(content, 'rb')
        else:
            # 如果 content 已经是文件数据（例如 io.BytesIO），直接使用
            content_file = content

        # 设置 headers 和文件上传的参数
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        # 文件上传部分
        files = {
            'content': content_file,  # 'content' 是目标服务器接收文件的字段名
        }

        # 请求体参数
        data = {
            'to': to,
            'isRoom': isRoom,
        }

        # 发送请求
        response = reqApi("/webhook/msg", method="POST", headers=headers, data=data, files=files)

        content_file.close()  # 关闭文件流
        return True, response, 200  # 成功，返回响应和状态码
    except Exception as e:
        print(f"发送请求时发生错误: {e}")
        return None, "微信发送失败", 500

