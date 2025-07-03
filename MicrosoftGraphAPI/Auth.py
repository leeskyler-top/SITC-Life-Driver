import base64
import hashlib
import time
import uuid
import jwt  # PyJWT
from cryptography import x509
from cryptography.hazmat.primitives import serialization
import requests

from LoadEnviroment.LoadEnv import ms_client_id, ms_tenant_id, ms_client_secret, ms_client_secret_type, upload_folder


def build_client_assertion():
    with open(ms_client_secret, "rb") as f:
        pem_data = f.read()

    private_key = serialization.load_pem_private_key(pem_data, password=None)

    # 提取证书 x5t (SHA-1 Thumbprint, base64url)
    cert = x509.load_pem_x509_certificate(pem_data)
    thumbprint = base64.urlsafe_b64encode(
        hashlib.sha1(cert.public_bytes(serialization.Encoding.DER)).digest()
    ).decode("utf-8").rstrip("=")

    now = int(time.time())
    payload = {
        "aud": f"https://login.microsoftonline.com/{ms_tenant_id}/v2.0",
        "iss": ms_client_id,
        "sub": ms_client_id,
        "jti": str(uuid.uuid4()),
        "exp": now + 600,
        "nbf": now,
        "iat": now,
    }
    headers = {
        "alg": "RS256",
        "typ": "JWT",
        "x5t": thumbprint  # ✅ 添加 SHA-1 Thumbprint
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

    return token


def getAppAccessToken(scope="https://graph.microsoft.com/.default"):
    url = f"https://login.microsoftonline.com/{ms_tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": ms_client_id,
        "scope": scope,
        "grant_type": "client_credentials"
    }

    if ms_client_secret_type == "secret":
        data["client_secret"] = ms_client_secret
    elif ms_client_secret_type == "key":
        data["client_assertion_type"] = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        data["client_assertion"] = build_client_assertion()
    else:
        raise ValueError("ms_client_secret_type must be 'secret' or 'key'")

    resp = requests.post(url, data=data)
    return resp.json(), resp.status_code


def get_site_id(access_token):
    url = "https://graph.microsoft.com/v1.0/sites/root"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    resp = requests.get(url, headers=headers)
    return resp.json()["id"]


def get_drive_id(access_token, site_id):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    resp = requests.get(url, headers=headers)
    return resp.json()['value'][0]['id']


def return_url(site_id, drive_id):
    upload_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{upload_folder}/"
    download_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
    return upload_url, download_url
