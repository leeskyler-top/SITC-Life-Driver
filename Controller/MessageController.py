from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from Model import User
from Model.Message import Message
from Model.User import PositionEnum
from .globals import json_response

message_controller = Blueprint('message_controller', __name__)


@message_controller.route('', methods=['GET'], endpoint='get_messages')
@jwt_required()
def get_messages():
    current_user_id = get_jwt_identity()
    user = User.get_user_by_id(current_user_id)  # 替换为你的查询方法

    if (user["position"] in [
        PositionEnum.MINISTER, PositionEnum.VICE_MINISTER, PositionEnum.DEPARTMENT_LEADER
    ]) or (user["is_admin"]):
        messages = Message.list_user_messages(current_user_id, True)
        return json_response("success", "获取成功", messages, code=200)
    messages = Message.list_user_messages(current_user_id, False)
    return json_response("success", "获取成功", messages, code=200)


@message_controller.route('/read', methods=['GET'], endpoint='read_all')
@jwt_required()
def read_all():
    current_user_id = get_jwt_identity()
    Message.mark_all_private_messages_read(current_user_id)
    return json_response("success", "全部已读完成", code=200)


@message_controller.route('/read/<int:message_id>', methods=['GET'], endpoint='read')
@jwt_required()
def read(message_id):
    current_user_id = get_jwt_identity()
    message = Message.get_message_by_id(message_id)
    if (not message) or (message['user_id'] != int(current_user_id)):
        return json_response("success", "未找到消息", code=404)
    Message.mark_message_read_by_id(message_id)
    return json_response("success", "已读完成", code=200)
