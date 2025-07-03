from flask_limiter import Limiter
from utils.utils import get_ip_from_forwarded_for

limiter = Limiter(key_func=get_ip_from_forwarded_for)