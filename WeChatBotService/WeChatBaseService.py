from .globals import wechat_webhook_service
import requests


def msgV1(session_id, file_stream, filename):
    files = {'file': (filename, file_stream)}
    try:
        response = requests.post(f"{wechat_webhook_service}/upload", files=files, data={'session_id': session_id})
        return True, response.json(), 200  # 返回API的响应
    except Exception as e:
        print(f"文件上传到API时发生错误: {e}")
        return False, f"文件上传到API时发生错误: {e}", 500
