from flask import Flask, jsonify, request, send_file
import hashlib
import os

app = Flask(__name__)

# 用于存储文件信息的字典，以哈希值为键，文件路径为值
file_storage = {}
# -------------------- 函数定义 --------------------
def hash_file_content(file_path):
    """计算给定文件的 SHA-256 哈希值"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            # 逐块读取文件内容，避免大文件带来的内存问题
            while chunk := f.read(8192):
                hasher.update(chunk)
    except IOError:
        pass  # 如果读取文件出现IO错误，不执行任何操作
    return hasher.hexdigest()

def initialize_file_storage():
    """初始化文件存储字典"""
    uploads_dir = 'uploads'  # 定义上传目录
    # 如果上传目录不存在，则创建它
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # 遍历 uploads 目录，计算每个文件的哈希值并存储
    for root, dirs, files in os.walk(uploads_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path):
                file_hash = hash_file_content(file_path)
                if file_hash:
                    file_storage[file_hash] = file_path

# -------------------- 路由定义 --------------------
@app.route('/search/<file_hash>', methods=['GET'])
def search_file(file_hash):
    """检查文件是否在存储中存在"""
    exists = file_hash in file_storage
    return jsonify({'exists': exists})

@app.route('/has/<file_hash>', methods=['POST'])
def has_file(file_hash):
    """上传文件哈希值并检查文件存在性"""
    exists = file_hash in file_storage
    return jsonify({'exists': exists})

@app.route('/retrieve/<file_hash>', methods=['GET'])
def retrieve_file(file_hash):
    """根据哈希值检索并返回文件内容"""
    file_path = file_storage.get(file_hash)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404
# -------------------- 主程序入口 --------------------

if __name__ == '__main__':
    # 初始化文件存储，加载已有文件
    initialize_file_storage()
    # 启动 Flask 服务器
    app.run(port=5000, debug=True)
