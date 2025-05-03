from .globals import *
from .CasLogin import loadLocalCasCookie

loadLocalCasCookie(check_expired=True)

# 向外暴露的内容
__all__ = [
    'cas_cookie_path',
    'headers',
    'pan_sso_service',
    'cas_baseurl'
]
