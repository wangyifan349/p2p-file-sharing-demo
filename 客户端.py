import requests
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# 预定义的节点列表
node_list = [
    'http://localhost:5000',
    # 添加更多节点
]
results_lock = threading.Lock()
# -------------------- 文件搜索逻辑 --------------------
def search_file_on_node(node_url, file_hash, results, log_callback, proxies):
    """向指定节点发送搜索请求"""
    try:
        log_callback(f"Searching {node_url} ...")
        response = requests.get(f"{node_url}/search/{file_hash}", timeout=5, proxies=proxies)
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                with results_lock:
                    results.append(node_url)
                log_callback(f"File found on {node_url}")
            else:
                log_callback(f"File not found on {node_url}")
        else:
            log_callback(f"Failed on {node_url}, HTTP code: {response.status_code}")
    except requests.RequestException as e:
        log_callback(f"Error connecting to {node_url}: {str(e)}")

def find_file(file_hash, log_callback, proxies):
    """启动线程进行文件搜索"""
    results = []
    threads = []
    for node_url in node_list:
        thread = threading.Thread(target=search_file_on_node, args=(node_url, file_hash, results, log_callback, proxies))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    return results
# -------------------- 文件下载逻辑 --------------------
def download_file(node_url, file_hash, log_callback, proxies, retry_count=0):
    """从节点下载文件"""
    try:
        log_callback(f"Downloading file from {node_url} ...")
        response = requests.get(f"{node_url}/retrieve/{file_hash}", stream=True, timeout=10, proxies=proxies)
        if response.status_code == 200:
            file_name = f"downloaded_{file_hash}"
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            log_callback(f"Download completed from {node_url} as {file_name}")
        else:
            log_callback(f"Download failed from {node_url}, HTTP code: {response.status_code}")
            if retry_count < len(node_list) - 1:
                next_node = (node_list.index(node_url) + 1) % len(node_list)
                download_file(node_list[next_node], file_hash, log_callback, proxies, retry_count + 1)
            else:
                log_callback("All retries failed.")
    except requests.RequestException as e:
        log_callback(f"Error downloading from {node_url}: {str(e)}")
        if retry_count < len(node_list) - 1:
            next_node = (node_list.index(node_url) + 1) % len(node_list)
            download_file(node_list[next_node], file_hash, log_callback, proxies, retry_count + 1)
        else:
            log_callback("All retries failed.")
# -------------------- 客户端应用 --------------------

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Distributed File Sharing Client")
        self.geometry("800x600")

        # 文件哈希输入框
        input_frame = tk.Frame(self)
        input_frame.pack(pady=15)
        
        self.hash_label = tk.Label(input_frame, text="File Hash:", font=("Helvetica", 12))
        self.hash_label.grid(row=0, column=0, padx=5)

        self.hash_entry = tk.Entry(input_frame, width=70, font=("Helvetica", 12))
        self.hash_entry.grid(row=0, column=1, padx=5)
        self.hash_entry.insert(0, "your_file_hash_here")

        # 代理设置
        self.proxy_frame = tk.LabelFrame(self, text="Proxy Settings", padx=10, pady=10, font=("Helvetica", 12))
        self.proxy_frame.pack(pady=10)

        self.proxy_label = tk.Label(self.proxy_frame, text="Proxy (host:port):", font=("Helvetica", 10))
        self.proxy_label.grid(row=0, column=0, padx=5)

        self.proxy_host_entry = tk.Entry(self.proxy_frame, width=30, font=("Helvetica", 10))
        self.proxy_host_entry.grid(row=0, column=1, padx=5)

        self.proxy_port_entry = tk.Entry(self.proxy_frame, width=10, font=("Helvetica", 10))
        self.proxy_port_entry.grid(row=0, column=2, padx=5)

        # 按钮区域
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=20)

        self.search_button = tk.Button(self.button_frame, text="Search File", width=20, command=self.start_search, font=("Helvetica", 12))
        self.search_button.grid(row=0, column=0, padx=15)

        self.download_button = tk.Button(self.button_frame, text="Download Selected", width=20, command=self.start_download, font=("Helvetica", 12))
        self.download_button.grid(row=0, column=1, padx=15)

        # 日志显示区域
        self.log_area = scrolledtext.ScrolledText(self, width=90, height=15, state='disabled', font=("Courier", 10))
        self.log_area.pack(padx=10, pady=10)

        # 节点列表显示区域
        self.nodes_listbox = tk.Listbox(self, width=90, height=5, font=("Helvetica", 12))
        self.nodes_listbox.pack(pady=(0, 10))
        self.available_nodes = []

    def log(self, message):
        """在日志区域中追加日志信息"""
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def get_proxies(self):
        """返回代理设置"""
        host = self.proxy_host_entry.get().strip()
        port = self.proxy_port_entry.get().strip()
        if host and port.isdigit():
            proxy_url = f"http://{host}:{port}"
            return {"http": proxy_url, "https": proxy_url}
        else:
            return None

    def start_search(self):
        """清除日志和节点列表，启动搜索线程"""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.nodes_listbox.delete(0, tk.END)
        self.available_nodes = []

        file_hash = self.hash_entry.get().strip()
        if not file_hash:
            messagebox.showwarning("Warning", "Please input a file hash!")
            return

        proxies = self.get_proxies()
        thread = threading.Thread(target=self.search_thread, args=(file_hash, proxies), daemon=True)
        thread.start()

    def search_thread(self, file_hash, proxies):
        """执行搜索逻辑，并将结果显示在列表框中"""
        self.log(f"Starting search for file hash: {file_hash}")
        nodes_found = find_file(file_hash, self.log, proxies)
        self.available_nodes = nodes_found

        if nodes_found:
            self.log(f"Search completed. File found on {len(nodes_found)} node(s):")
            for node in nodes_found:
                self.nodes_listbox.insert(tk.END, node)
            answer = messagebox.askyesno("Download", f"File found on {len(nodes_found)} node(s). Would you like to download from the first node?")
            if answer:
                self.start_download(selected_index=0)
        else:
            self.log("Search completed. File not found on any node.")

    def start_download(self, selected_index=None):
        """启动下载线程，从选定的节点下载文件"""
        file_hash = self.hash_entry.get().strip()
        if not file_hash:
            messagebox.showwarning("Warning", "Please input a file hash!")
            return

        if not self.available_nodes:
            messagebox.showinfo("Info", "No available node to download from. Please search first.")
            return

        index = selected_index
        if index is None:
            cur_selection = self.nodes_listbox.curselection()
            if not cur_selection:
                messagebox.showinfo("Info", "Please select a node from the list to download.")
                return
            index = cur_selection[0]

        try:
            node_url = self.available_nodes[index]
        except IndexError:
            messagebox.showerror("Error", "Selected node index out of range.")
            return

        proxies = self.get_proxies()
        thread = threading.Thread(target=download_file, args=(node_url, file_hash, self.log, proxies), daemon=True)
        thread.start()

if __name__ == '__main__':
    app = Application()
    app.mainloop()
