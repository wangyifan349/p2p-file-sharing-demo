import hashlib
import os
from flask import Flask, jsonify, send_file
app = Flask(__name__)
# 存储文件的字典，键为文件哈希，值为文件路径
file_storage = {}
def hash_file_content(file_path):
    """
    计算文件的 SHA-256 哈希值
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
        print("读取文件错误:", file_path, e)
    return hasher.hexdigest()
def initialize_file_storage():
    """
    遍历上传目录，计算文件哈希，并存入字典
    """
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    # 遍历 uploads 目录，不使用嵌套或列表表达式
    for root, dirs, files in os.walk(uploads_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            # 判断是否为文件
            if os.path.isfile(file_path):
                file_hash = hash_file_content(file_path)
                file_storage[file_hash] = file_path
                print("添加文件:", file_path, "哈希:", file_hash)
@app.route('/search/<file_hash>', methods=['GET'])
def search_file(file_hash):
    """
    根据文件哈希检查文件是否存在
    """
    exists = file_hash in file_storage
    # 返回 JSON 格式，确保客户端得到准确响应
    return jsonify({'exists': exists})
@app.route('/retrieve/<file_hash>', methods=['GET'])
def retrieve_file(file_hash):
    """
    根据文件哈希返回文件
    """
    file_path = file_storage.get(file_hash)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404


initialize_file_storage()
app.run(port=5000, debug=True)



