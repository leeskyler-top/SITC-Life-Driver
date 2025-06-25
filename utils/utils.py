import subprocess
import zipfile
import os
import io
import base64
import shutil
from werkzeug.utils import secure_filename
import utils.imghdr as imghdr
from PIL import Image
from LoadEnviroment.LoadEnv import rar_path

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """检查文件扩展名和实际类型"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file_stream):
    """使用Pillow严格验证图片完整性和格式"""
    try:
        # 将文件流转换为字节（确保指针重置）
        file_stream.seek(0)
        img_bytes = file_stream.read()

        # 通过内存中的字节验证
        with Image.open(io.BytesIO(img_bytes)) as img:
            img.verify()  # 验证完整性
            return img.format.lower() in ALLOWED_EXTENSIONS
    except Exception:
        return False
    finally:
        file_stream.seek(0)  # 无论如何都重置指针


def detect_mime(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            header = f.read(32)
            file_type = imghdr.what(None, header)
            return f'image/{file_type}' if file_type else 'application/octet-stream'
    return None


def rm_results():
    path = os.path.join(os.getcwd(), 'results', 'zip_file')
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"文件夹 {path} 已存在，已删除旧文件。")


def zip_file_in_parts(input_data, part_size_mb, output_dir, original_filename="file.bin"):
    part_size_bytes = part_size_mb * 1024 * 1024  # 将MB转为字节
    input_stream = io.BytesIO(input_data)  # 使用BytesIO将二进制数据包装为文件对象

    part_num = 1
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在
    while input_stream.tell() < len(input_data):
        # 设置每个部分的压缩文件名
        part_filename = os.path.join(output_dir, f"{original_filename}.part{part_num}.zip")

        # 创建一个ZIP文件
        with zipfile.ZipFile(part_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            start_pos = input_stream.tell()
            end_pos = min(start_pos + part_size_bytes, len(input_data))

            # 读取部分数据并写入ZIP文件
            zipf.writestr(original_filename, input_stream.read(end_pos - start_pos))

        print(f"Part {part_num} saved as {part_filename}")
        part_num += 1


def rar_file_in_parts(input_data, part_size_mb, output_dir, original_filename="file.bin"):
    """
    使用 WinRAR 命令行工具将二进制数据压缩为分卷 RAR 文件。

    :param input_data: 待压缩的二进制数据
    :param part_size_mb: 每个分卷的大小（MB）
    :param output_dir: 输出目录
    :param original_filename: 原始文件名（仅作为压缩包内文件名）
    """
    part_size_bytes = part_size_mb * 1024 * 1024  # 转换为字节
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在

    # 写入临时文件（RAR 不支持直接操作内存数据）
    temp_file_path = os.path.join(output_dir, original_filename)
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(input_data)

    # RAR 压缩文件路径
    rar_output_path = os.path.join(output_dir, f"{original_filename}.rar")

    # 调用 WinRAR 命令行工具进行分卷压缩
    try:
        subprocess.run(
            [
                f"{rar_path}", "a",  # "a" 表示添加文件到压缩包
                "-v" + str(part_size_mb) + "m",  # 设置分卷大小
                "-ep1",  # 排除文件路径，仅保留文件本体
                rar_output_path,  # 压缩包路径
                temp_file_path,  # 要压缩的文件
            ],
            check=True,
        )
        print(f"分卷压缩完成，输出目录：{part_size_bytes}")
        return True
    except FileNotFoundError:
        print("WinRAR 的 'rar' 命令未找到，请确保已安装并配置到系统 PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"压缩过程中发生错误：{e}")
        return False
    finally:
        # 删除临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def image_to_base64_url(image_path):
    # 读取图片文件
    with open(image_path, "rb") as image_file:
        # 将图片内容编码为 Base64
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    # 获取图片的扩展名
    file_extension = image_path.split('.')[-1].lower()

    # 根据扩展名选择 MIME 类型
    if file_extension in ['jpg', 'jpeg']:
        mime_type = 'image/jpeg'
    elif file_extension == 'png':
        mime_type = 'image/png'
    elif file_extension == 'gif':
        mime_type = 'image/gif'
    elif file_extension == 'bmp':
        mime_type = 'image/bmp'
    else:
        raise ValueError("Unsupported file type")

    # 创建 Base64 URL
    base64_url = f"data:{mime_type};base64,{encoded_string}"

    return base64_url


def download_file(url):
    """
    从 URL 下载文件内容并返回二进制数据。

    :param url: 文件的下载 URL
    :return: 文件的二进制数据
    """
    import requests

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"下载失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"下载文件时发生错误: {e}")
        raise


def embed_zip_into_jpg(jpg_path, zip_data, output_path):
    """
    将压缩包嵌入到 JPG 图片中，不影响图片显示，并支持解压。

    :param jpg_path: 原始 JPG 图片路径
    :param zip_data: 待嵌入的压缩包二进制数据
    :param output_path: 输出嵌入后的 JPG 文件路径
    """
    try:
        # 读取图片的二进制数据
        with open(jpg_path, 'rb') as jpg_file:
            jpg_data = jpg_file.read()

        # 将压缩包数据附加到图片数据尾部
        combined_data = jpg_data + zip_data

        # 保存嵌入后的图片
        with open(output_path, 'wb') as output_file:
            output_file.write(combined_data)

        print(f"嵌入完成！嵌入后的图片保存为：{output_path}")
        print("可通过修改文件扩展名为 .zip 或 .rar 后解压获取嵌入的内容。")
    except Exception as e:
        print(f"发生错误：{e}")
