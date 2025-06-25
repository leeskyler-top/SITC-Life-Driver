from flask import Blueprint
from Controller.globals import json_response
from Handler.Handler import record_history, admin_required
from LoadEnviroment.LoadEnv import save_histories_days, save_histories_count
from Model import History
import socket

history_controller = Blueprint('history_controller', __name__)

@history_controller.route('', methods=['GET'], endpoint='get_messages')
@admin_required
@record_history
def get_histories():
    histories = History.get_all_histories()
    History.cleanup_old_records(save_histories_days=save_histories_days, max_records=save_histories_count)
    return json_response("success", "所有值班计划已列出", data=histories, code=200)

@history_controller.route('/internal-ip', methods=['GET'])
def get_internal_ip():
    try:
        # 创建一个UDP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个外部地址（不会实际发送数据）
        s.connect(("1.1.1.1", 80))
        # 获取本机的IP地址
        ip = s.getsockname()[0]
    except Exception as e:
        print(f"获取内网IP时发生错误: {e}")
        ip = None
    finally:
        s.close()
    return json_response("success", "OK", data={'internal_ip': ip}, code=200)
