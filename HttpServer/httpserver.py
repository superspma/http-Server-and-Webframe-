"""
httpserver.py
功能:
httpserver部分 主程序
"""

from socket import *
from threading import Thread
from config import *
import re, sys
import json

# 服务器地址
ADDR = (HOST, PORT)


def connect_frame(env):
    """
    :param env:得到要发送给frame的请求字典
    :return: 从frame得到的数据
    """
    # 建立socket客户端
    s = socket()
    try:
        s.connect((frame_ip, frame_port))
    except Exception as e:
        print(e)
        return
    # 将env转换为json
    data = json.dumps(env)
    s.send(data.encode())
    # 接收从frame返回的数据 (1M)
    data = s.recv(1024 * 1024).decode()
    return json.loads(data)  # 字典


# 实现http功能
class HTTPServer:
    def __init__(self):
        self.address = ADDR
        self.create_socket()
        self.bind()

    def create_socket(self):
        self.sockfd = socket()
        self.sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, DEBUG)

    def bind(self):
        self.sockfd.bind(self.address)
        self.ip = self.address[0]
        self.port = self.address[1]

    # 启动服务
    def server_forever(self):
        self.sockfd.listen(5)
        print("Listen the port %d" % self.port)

        while True:
            connfd, addr = self.sockfd.accept()
            print("Connect from", addr)
            # 完成多线程并发模型
            client = Thread(target=self.handle, args=(connfd,))
            client.setDaemon(True)
            client.start()

    # 处理浏览器请求
    def handle(self, connfd):
        request = connfd.recv(4096).decode()
        print(request)
        pattern = r"(?P<method>[A-Z]+)\s+(?P<info>/\S*)"
        try:
            # env 格式 {method:'GET',info:'/'}
            env = re.match(pattern, request).groupdict()
        except:
            connfd.close()
            return
        else:
            # data  格式 {status:'200',data:'ccccc'}
            data = connect_frame(env)  # 用户与frame交互
            if data:
                self.response(connfd, data)

    # 将data组织为response 发送给浏览器
    def response(self, connfd, data):
        if data['status'] == "200":
            self.http_(connfd, data)

        elif data['status'] == "404":
            self.http_(connfd, data)

        elif data['status'] == "500":
            pass

    def http_(self, connfd, data):
        response = "HTTP/1.1 %s OK\r\n" \
                   "Connect-Type:text/html\r\n" \
                   "\r\n" \
                   "%s" % (data['status'], data['data'])
        connfd.send(response.encode())


httpd = HTTPServer()
try:
    httpd.server_forever()  # 启动httpserver
except Exception:
    sys.exit("Httpserver 退出!")
