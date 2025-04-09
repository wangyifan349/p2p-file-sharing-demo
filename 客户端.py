import requests
import threading

# 模拟的节点地址列表
node_list = [
    'http://node1.example.com:5000',
    'http://node2.example.com:5000',
    'http://node3.example.com:5000',
    # 添加更多的节点地址
]
# 用于线程安全地修改结果列表
results_lock = threading.Lock()
def search_file_on_node(node_url, file_hash, results):
    """
    向单个节点请求文件哈希存在性
    1. 向节点发送 GET 请求，请求路径为: {node_url}/search/{file_hash}
    2. 如果响应成功且返回 JSON 中 'exists' 为 True，则将该节点地址添加到 results 列表中
    """
    try:
        response = requests.get(f'{node_url}/search/{file_hash}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                with results_lock:
                    results.append(node_url)
    except requests.RequestException as e:
        print(f"Error connecting to {node_url}: {e}")
def find_file(file_hash):
    """
    在所有节点上通过多线程方式查找文件
    1. 分别为每个节点创建线程，执行 search_file_on_node
    2. 等待所有线程执行完毕后返回包含文件存在的节点地址列表
    """
    results = []
    threads = []
    for node_url in node_list:
        thread = threading.Thread(
            target=search_file_on_node, 
            args=(node_url, file_hash, results)
        )
        threads.append(thread)
        thread.start()
    # 等待所有线程结束
    for thread in threads:
        thread.join()
    return results
def download_file(node_url, file_hash):
    """
    从指定节点下载文件
    1. 通过 GET 请求访问 {node_url}/retrieve/{file_hash}，流式读取响应体
    2. 将返回的文件内容保存到本地文件 "downloaded_{file_hash}"
    """
    try:
        response = requests.get(f'{node_url}/retrieve/{file_hash}', stream=True, timeout=10)
        if response.status_code == 200:
            file_name = f'downloaded_{file_hash}'
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f'File downloaded from {node_url} as {file_name}')
        else:
            print(f'File not found on {node_url}. HTTP code: {response.status_code}')
    except requests.RequestException as e:
        print(f"Error downloading from {node_url}: {e}")

if __name__ == '__main__':
    # 指定待搜索的文件哈希
    file_hash = 'your_file_hash_here'
    # 先在各个节点上搜索文件
    available_nodes = find_file(file_hash)
    if available_nodes:
        print(f'File found on nodes: {available_nodes}')
        # 从第一个返回的节点下载文件
        download_file(available_nodes[0], file_hash)
    else:
        print('File not found on any node')
