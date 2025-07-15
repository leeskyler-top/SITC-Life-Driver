from SQLService.globals import get_connection
from utils.encrypter import encrypt_with_backend_key, decrypt_with_backend_key


def enc_col(col_name: str, size: int = 256):
    """最简单直接的列加密函数"""
    with get_connection(database="SITC") as conn:
        with conn.cursor() as cursor:
            # 1. 改字段类型
            cursor.execute(f"ALTER TABLE users MODIFY {col_name} VARCHAR({size})")

            # 2. 查所有记录
            cursor.execute(f"SELECT id, {col_name} FROM users WHERE {col_name} IS NOT NULL")
            users = cursor.fetchall()
            # 3. 直接开干
            for user in users:
                try:
                    encrypted = encrypt_with_backend_key(str(user[col_name]))
                    cursor.execute(
                        f"UPDATE users SET {col_name} = %s WHERE id = %s",
                        (encrypted, user['id'])
                    )
                except Exception as e:
                    print(e)
                    pass  # 出错就跳过

            conn.commit()
    return "搞定！"
