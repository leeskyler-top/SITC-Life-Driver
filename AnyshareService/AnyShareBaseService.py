from .globals import headers
from LoadEnviroment.LoadEnv import pan_baseurl
from CasService.CasLogin import get_tokenid, cookie_dict
import requests


def reqApi(name, method="GET", json={}, params=None):
    if method == "GET" and not params:
        req = requests.get(pan_baseurl + name, headers=headers, cookies=cookie_dict, verify=False)
        return req.json(), req.status_code
    elif method == "GET" and params:
        req = requests.get(pan_baseurl + name, headers=headers, cookies=cookie_dict, params=params, verify=False)
        return req.json(), req.status_code
    elif method == "POST":
        req = requests.post(pan_baseurl + name, headers=headers, cookies=cookie_dict, json=json, params=params,
                            verify=False)
        return req.json(), req.status_code
    elif method == "PATCH":
        req = requests.patch(pan_baseurl + name, headers=headers, cookies=cookie_dict, json=json, verify=False)
        return req.json(), req.status_code


def set_token_id():
    tokenid = get_tokenid()
    params = {
        "tokenid": tokenid
    }
    return params


# 获取入口文件夹
def entrydoc():
    params = set_token_id()
    params['method'] = 'get'
    req, code = reqApi("/entrydoc2", method="POST", params=params)
    return req, code


# dirs files
def listDir(docid):
    params = set_token_id()
    params['method'] = 'list'
    req, code = reqApi("/dir", method="POST", params=params, json={
        "by": "name",
        "docid": docid,
        "sort": "asc"
    })
    return req, code


def createDir(parent_docid: str, name: str = "新建文件夹"):
    params = set_token_id()
    params['method'] = 'create'
    req, code = reqApi("/dir", method="POST", params=params, json={
        "docid": parent_docid,
        "name": name
    })
    return req, code


def delDir(docid: str):
    params = set_token_id()
    params['method'] = 'delete'
    req, code = reqApi("/dir", method="POST", params=params, json={
        "docid": docid,
    })
    return req, code


def openShareLink(docid: str):
    params = set_token_id()
    params['method'] = 'open'
    req, code = reqApi("/link", method="POST", params=params, json={
        "docid": docid
    })
    return req, code

def getLinkDetail(docid: str):
    params = set_token_id()
    params['method'] = 'getdetail'
    req, code = reqApi("/link", method="POST", params=params, json={
        "docid": docid
    })
    return req, code


def closeShareLink(docid: str):
    params = set_token_id()
    params['method'] = 'open'
    req = requests.post(pan_baseurl + "/link", headers=headers, cookies=cookie_dict, json={
        "docid": docid,
    }, params=params, verify=False)
    return {}, req.status_code

def setShareLink(docid: str, end_time, limittimes:int = -1, perm: int = 7, use_password: bool = False):
    params = set_token_id()
    params['method'] = 'set'
    req, code = reqApi("/link", method="POST", params=params, json={
        "docid": docid,
        "endtime": end_time,
        "open": use_password,
        "limittimes": limittimes,
        "perm": perm
    })
    return req, code