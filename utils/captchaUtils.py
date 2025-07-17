import uuid
import base64
import random
import string
from captcha.image import ImageCaptcha


def generate_captcha(include_letters=True, include_numbers=True, length=4):
    # 防止全关时启用默认
    if not include_letters and not include_numbers:
        include_letters = include_numbers = True

    chars = ''
    if include_letters:
        chars += string.ascii_letters
    if include_numbers:
        chars += string.digits

    answer = ''.join(random.choices(chars, k=length))
    image = ImageCaptcha()
    data = image.generate(answer)

    image_data = base64.b64encode(data.read()).decode('utf-8')
    captcha_uuid = str(uuid.uuid4())

    return captcha_uuid, image_data, answer
