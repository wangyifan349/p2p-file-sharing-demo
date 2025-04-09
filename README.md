## 简介  
这是一个简单的分布式文件共享示例项目。  
服务端使用 Flask 提供文件搜索与下载接口，客户端通过多线程在多个节点上检测和下载指定文件。

## Description  
This is a simple distributed file sharing demo.  
The server, built with Flask, provides file search and download endpoints while the client uses multithreading to query and download a file from multiple nodes.

## 目录 / Structure  
├── client.py       # 客户端代码 / Client code

├── server.py       # 服务端代码 / Server code

├── uploads/        # 文件存放目录 / Directory for uploaded files
└── README.md    


## 使用 / Usage

### 服务端 / Server  
1. 将文件放入 `uploads/` 目录。
 
   python server.py
  

### 客户端 / Client  
客户端中添加节点，并直接运行

   python client.py

## 许可 / License  
MIT License
