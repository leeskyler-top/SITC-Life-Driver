from flask import Blueprint
from flask_jwt_extended import jwt_required

from Controller.globals import json_response
from Handler.Handler import record_history, admin_required
from LoadEnviroment.LoadEnv import save_histories_days, save_histories_count
from Model import History

history_controller = Blueprint('history_controller', __name__)

@history_controller.route('', methods=['GET'], endpoint='get_messages')
@admin_required
@record_history
def get_histories():
    histories = History.get_all_histories()
    History.cleanup_old_records(save_histories_days=save_histories_days, max_records=save_histories_count)
    return json_response("success", "所有值班计划已列出", data=histories, code=200)
