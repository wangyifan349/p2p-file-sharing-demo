import requests
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Predefined list of node URLs
node_list = [
    'http://node1.example.com:5000',
    'http://node2.example.com:5000',
    'http://node3.example.com:5000',
    # Add more node URLs as needed
]

# Lock for thread-safe operations on shared list
results_lock = threading.Lock()

def search_file_on_node(node_url, file_hash, results, log_callback):
    # Send GET request to node URL for search endpoint
    try:
        log_callback("Searching " + node_url + " ...")
        response = requests.get(node_url + '/search/' + file_hash, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                results_lock.acquire()
                results.append(node_url)
                results_lock.release()
                log_callback("File found on " + node_url)
            else:
                log_callback("File not found on " + node_url)
        else:
            log_callback("Failed on " + node_url + ", HTTP code: " + str(response.status_code))
    except requests.RequestException as e:
        log_callback("Error connecting to " + node_url + ": " + str(e))

def find_file(file_hash, log_callback):
    # Start a thread for each node and check for file existence
    results = []
    threads = []
    for i in range(len(node_list)):
        node_url = node_list[i]
        thread = threading.Thread(target=search_file_on_node, args=(node_url, file_hash, results, log_callback))
        threads.append(thread)
        thread.start()
    for i in range(len(threads)):
        threads[i].join()
    return results

def download_file(node_url, file_hash, log_callback):
    # Download file from specified node using stream read
    try:
        log_callback("Downloading file from " + node_url + " ...")
        response = requests.get(node_url + '/retrieve/' + file_hash, stream=True, timeout=10)
        if response.status_code == 200:
            file_name = "downloaded_" + file_hash
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            log_callback("Download completed from " + node_url + " as " + file_name)
        else:
            log_callback("Download failed: File not found on " + node_url + ", HTTP code: " + str(response.status_code))
    except requests.RequestException as e:
        log_callback("Error downloading from " + node_url + ": " + str(e))

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Distributed File Sharing Client")
        self.geometry("650x450")
        self.hash_label = tk.Label(self, text="File Hash:")
        self.hash_label.pack(pady=5)
        self.hash_entry = tk.Entry(self, width=60)
        self.hash_entry.pack(pady=5)
        self.hash_entry.insert(0, "your_file_hash_here")
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=5)
        self.search_button = tk.Button(self.button_frame, text="Search File", command=self.start_search)
        self.search_button.grid(row=0, column=0, padx=5)
        self.download_button = tk.Button(self.button_frame, text="Download Selected", command=self.start_download)
        self.download_button.grid(row=0, column=1, padx=5)
        self.log_area = scrolledtext.ScrolledText(self, width=80, height=20, state='disabled')
        self.log_area.pack(padx=10, pady=10)
        self.nodes_listbox = tk.Listbox(self, width=80, height=5)
        self.nodes_listbox.pack(pady=(0,10))
        self.available_nodes = []

    def log(self, message):
        # Update the log area with a new message
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def start_search(self):
        # Clear previous log and results; start search in a new thread
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.nodes_listbox.delete(0, tk.END)
        self.available_nodes = []
        file_hash = self.hash_entry.get().strip()
        if file_hash == "":
            messagebox.showwarning("Warning", "Please input a file hash!")
            return
        thread = threading.Thread(target=self.search_thread, args=(file_hash,), daemon=True)
        thread.start()

    def search_thread(self, file_hash):
        # Execute search and update the listbox with found nodes
        self.log("Starting search for file hash: " + file_hash)
        nodes_found = find_file(file_hash, self.log)
        self.available_nodes = nodes_found
        if len(nodes_found) > 0:
            self.log("Search completed. Found file on the following node(s):")
            for i in range(len(nodes_found)):
                self.nodes_listbox.insert(tk.END, nodes_found[i])
            answer = messagebox.askyesno("Download", "File found. Would you like to download from the first node?")
            if answer:
                self.start_download(selected_index=0)
        else:
            self.log("Search completed. File not found on any node.")

    def start_download(self, selected_index=None):
        # Start download from selected node in a new thread
        file_hash = self.hash_entry.get().strip()
        if file_hash == "":
            messagebox.showwarning("Warning", "Please input a file hash!")
            return
        if len(self.available_nodes) == 0:
            messagebox.showinfo("Info", "No available node to download from. Please search first.")
            return
        index = selected_index
        if index is None:
            cur_selection = self.nodes_listbox.curselection()
            if len(cur_selection) == 0:
                messagebox.showinfo("Info", "Please select a node from the list to download.")
                return
            index = cur_selection[0]
        try:
            node_url = self.available_nodes[index]
        except IndexError:
            messagebox.showerror("Error", "Selected node index out of range.")
            return
        thread = threading.Thread(target=download_file, args=(node_url, file_hash, self.log), daemon=True)
        thread.start()

if __name__ == '__main__':
    app = Application()
    app.mainloop()
