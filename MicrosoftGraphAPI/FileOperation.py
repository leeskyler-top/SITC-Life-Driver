import requests

from MicrosoftGraphAPI.Auth import getAppAccessToken, get_site_id, get_drive_id, return_url


def permanentDelete(file_id):
    result, code = getAppAccessToken()
    site_id = get_site_id(result['access_token'])
    drive_id = get_drive_id(result['access_token'], site_id)
    _, doanload_url = return_url(site_id, drive_id)
    if code != 200:
        return 401
    url = f"{doanload_url}{file_id}/permanentDelete"
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    resp = requests.post(url, headers=headers)
    return resp.status_code
