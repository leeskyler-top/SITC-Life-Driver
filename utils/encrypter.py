import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64

from LoadEnviroment.LoadEnv import backend_aes_key, server_aes_rsa_private_key


def encrypt_with_backend_key(plain_text: str):
    """用后端密钥加密数据（用于存储）"""
    if plain_text is None:
        return None
    iv = get_random_bytes(16)  # CBC模式需要16字节IV
    cipher = AES.new(backend_aes_key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plain_text.encode(), AES.block_size))
    return base64.b64encode(iv + encrypted).decode()


def decrypt_with_backend_key(encrypted_data: str):
    if encrypted_data is None:
        return None
    """用后端密钥解密数据（从存储读取）"""
    data = base64.b64decode(encrypted_data)
    iv = data[:16]
    cipher = AES.new(backend_aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data[16:]), AES.block_size).decode()


def generate_and_encrypt_aes_key(public_key, aes_key: bytes = None):
    # 1. 生成随机32字节AES key
    if aes_key is None:
        aes_key = os.urandom(32)
        print(f"生成的AESKey（hex）: {aes_key.hex()}")

    # 2. 用公钥RSA-OAEP-SHA256加密AESKey
    encrypted = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return base64.b64encode(encrypted).decode()


def load_private_key(key_path: str):
    """加载 PEM 格式的 RSA 私钥"""
    with open(key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # 如果私钥有密码，在此处传入
            backend=default_backend()
        )
    return private_key


def rsa_decrypt(encrypted_data: bytes, private_key) -> bytes | str:
    """RSA-OAEP 解密数据"""
    try:
        encrypted_data = base64.b64decode(encrypted_data)
        decrypted = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    except Exception as e:
        raise ValueError(f"RSA 解密失败: {str(e)}")


private_key = load_private_key(server_aes_rsa_private_key)
public_key = private_key.public_key()
PUBLIC_KEY_PEM = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')


def decrypt_aes_gcm(encrypted_json: dict, aes_key: bytes) -> dict:
    iv = base64.b64decode(encrypted_json['iv'])
    ciphertext = base64.b64decode(encrypted_json['ciphertext'])
    tag = base64.b64decode(encrypted_json['tag'])
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
    cipher.update(b"")
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(plaintext.decode())
