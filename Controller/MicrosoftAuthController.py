from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.limiter import limiter

from Handler.Handler import record_history, cloudflare_worker_required
from MicrosoftGraphAPI.Auth import getAppAccessToken, return_url, get_drive_id, get_site_id
from .globals import json_response


microsoft_auth_controller = Blueprint('microsoft_auth_controller', __name__)

@microsoft_auth_controller.route("/auth/callback", methods=['GET'])
@jwt_required()
@cloudflare_worker_required
@record_history
@limiter.limit("1 per minute", key_func=lambda: get_jwt_identity())
def auth_callback():
    scope = request.args.get("scope")
    if scope:
        response, code = getAppAccessToken(scope)
    else:
        response, code = getAppAccessToken()
    if 200 <= code < 300:
        site_id = get_site_id(response['access_token'])
        drive_id = get_drive_id(response['access_token'], site_id)
        upload_url, doanload_url = return_url(site_id, drive_id)
        response['upload_baseurl'] = upload_url
        response['download_baseurl'] = doanload_url
        response['expired_at'] = (datetime.now().timestamp() + response['expires_in'] - 350) * 1000
        response['drive_id'] = drive_id
        response['site_id'] = site_id
        return json_response(status="success", message="Microsoft Graph 已认证", data=response, code=code)
    return json_response(status="fail", message="Microsoft Graph 认证失败", data=response, code=400)
