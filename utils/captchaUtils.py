import io
from gtts import gTTS
import uuid
import base64
import random
import string
from captcha.image import ImageCaptcha

NATO_PHONETIC = {
    'A': 'Alpha', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
    'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliett',
    'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
    'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
    'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee', 'Z': 'Zulu',
    '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
    '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine',
}


def to_nato_phonetic(text):
    return ' - '.join(NATO_PHONETIC.get(c.upper(), c) for c in text)


def generate_captcha_voice(answer: str):
    # 每个字符之间加空格方便听
    spaced_text = ' - '.join(answer)
    tts = gTTS(text=to_nato_phonetic(spaced_text), lang='en')
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    # base64 返回前端
    audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
    return audio_base64


def generate_captcha(include_letters: bool = True, include_numbers: bool = True, length: int = 4, width: int = 120,
                     height: int = 35, font_size: int = 24, type: str = 'image'):
    # 防止全关时启用默认
    if not include_letters and not include_numbers:
        include_letters = include_numbers = True


    # 定义安全字符集（剔除易混字符）
    letter_set = ''.join(c for c in string.ascii_letters if c not in 'IlOo')
    number_set = ''.join(c for c in string.digits if c != '0')

    chars = ''
    if include_letters:
        chars += letter_set
    if include_numbers:
        chars += number_set

    answer = ''.join(random.choices(chars, k=length))
    if type == 'image':
        image = ImageCaptcha(width=width, height=height, font_sizes=[font_size])
        data = image.generate(answer)
        data = base64.b64encode(data.read()).decode('utf-8')
    else:
        data = generate_captcha_voice(answer)

    captcha_uuid = str(uuid.uuid4())

    return captcha_uuid, data, answer
