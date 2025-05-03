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
        req = requests.post(wechat_webhook_service + name, data=data, json=json, params=params, files=files,
                            headers=headers,
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


def msgV1(to, isRoom, content, name="file.zip"):
    """
    发送 POST 请求，通过 Webhook 上传文件。
    :param to: 目标
    :param isRoom: 是否是群聊
    :param content: 文件路径或文件数据
    :param name: 文件名
    """
    # 健康检查
    status, code = check_health()
    if not status:
        return False, "微信登录失效", code

    try:
        # 检查 content 是文件路径还是二进制数据
        content_file = None
        if isinstance(content, str):  # 文件路径
            content_file = open(content, 'rb')
            file_data = content_file
        else:  # 已经是二进制数据
            file_data = content

        # 设置 headers 和文件上传的参数
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        # 文件上传部分，指定文件名
        files = {
            'content': (name, file_data, 'application/octet-stream'),  # 指定文件名和 MIME 类型
        }

        if isinstance(content, str):
            files['content'] = file_data

        # 请求体参数
        data = {
            'to': to,
            'isRoom': isRoom,
        }

        # 发送请求
        response, code = reqApi("/webhook/msg", method="POST", headers=headers, data=data, files=files)

        # 如果打开了文件流，则关闭它
        if content_file:
            content_file.close()

        return True, response, 200  # 成功，返回响应和状态码

    except Exception as e:
        print(f"发送请求时发生错误: {e}")
        return None, "微信发送失败", 500
