import hashlib
import os
from flask import Flask, jsonify, send_file

app = Flask(__name__)
# 存储文件的字典，键为文件哈希，值为文件路径
file_storage = {}
def hash_file_content(file_path):
    """
    计算并返回指定文件的 SHA-256 哈希值
    1. 打开文件，以二进制模式读取内容
    2. 采用分块读取方式计算哈希，防止大文件占用过多内存
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
    except IOError as e:
        print(f'Error reading file {file_path}: {e}')
    return hasher.hexdigest()
def initialize_file_storage():
    """
    初始化文件存储
    1. 遍历 uploads 目录及其子目录下的所有文件（使用 os.walk）
    2. 计算每个文件的 SHA-256 哈希，并将该哈希和对应文件路径存入 file_storage 字典
    """
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    for root, dirs, files in os.walk(uploads_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path):
                file_hash = hash_file_content(file_path)
                file_storage[file_hash] = file_path
                print(f'File {file_path} added, hash: {file_hash}')

@app.route('/search/<file_hash>', methods=['GET'])
def search_file(file_hash):
    """
    文件搜索接口
    1. 根据 URL 中传入的 file_hash 检查文件是否存在于 file_storage 中
    2. 返回 JSON 格式结果：{'exists': True} 或 {'exists': False}
    """
    exists = file_hash in file_storage
    return jsonify({'exists': exists})
@app.route('/retrieve/<file_hash>', methods=['GET'])
def retrieve_file(file_hash):
    """
    文件下载接口
    1. 根据 URL 中的 file_hash 判断文件是否存在于 file_storage 中
    2. 如果存在，使用 send_file 返回文件，并以附件格式下载
    3. 如果不存在，返回错误信息和 404 状态码
    """
    file_path = file_storage.get(file_hash)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # 初始化上传目录与文件存储
    initialize_file_storage()
    # 运行 Flask 服务，监听5000端口
    app.run(port=5000, debug=True)
