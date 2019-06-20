"""
webframe.py

功能:用于模拟网站后端应用工作流程
"""
from socket import *
import json, sys
from settings import *
from select import *
from urls import *  # 导入路由

# frame 绑定地址
frame_address = (frame_ip, frame_port)


# 网站应用类
class Application:
    def __init__(self):
        self.sockfd = socket()
        self.sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, DEBUG)
        self.sockfd.bind(frame_address)
        self.ep = epoll()  # 生成epoll 对象
        self.fdmap = {}  # 建立查找字典,用于通过fileno查找IO对象

    def start(self):
        self.sockfd.listen(5)
        print("Listen the port %d" % frame_port)
        self.ep.register(self.sockfd, EPOLLIN)
        self.fdmap[self.sockfd.fileno()] = self.sockfd
        while True:
            events = self.ep.poll()
            for fd, event in events:
                if fd == self.sockfd.fileno():
                    connfd, addr = self.fdmap[fd].accept()
                    print("Connect from", addr)
                    self.ep.register(connfd, EPOLLIN | EPOLLET)
                    self.fdmap[connfd.fileno()] = connfd
                elif event & EPOLLIN:
                    self.handle(self.fdmap[fd])  # 处理http 请求
                    self.ep.unregister(fd)
                    del self.fdmap[fd]

    def handle(self, connfd):
        request = connfd.recv(1024).decode()
        request = json.loads(request)
        # request-->{'method':'GET','info':'/'}
        if request['method'] == 'GET':
            if request['info'] == '/' \
                    or request['info'][-5:] == '.html':
                response = self.get_html(request['info'])
            else:
                response = self.get_data(request['info'])
        elif request['method'] == 'POST':
            pass

        # 　将response发送给httpserver
        responses = json.dumps(response)
        connfd.send(responses.encode())
        connfd.close()

    # 处理网页请求
    def get_html(self, info):
        # print(info)
        if info == "/":
            filename = STATIC_DIR + "/index.html"
        else:
            filename = STATIC_DIR + info
        try:
            fd = open(filename)
        except Exception:
            f = open(STATIC_DIR + "/404.html")
            return {'status': '404', 'data': f.read()}
        else:
            return {'status': '200', 'data': fd.read()}

    # 处理其他请求  info==>/time
    def get_data(self, info):
        # urls ==> [('/time',),(),()]
        for url, fun in urls:
            if url == info:
                return {'status': '200', 'data': fun()}
        return {'status': '404', 'data': "Sorry...."}


app = Application()
try:
    app.start()  # 启动应用
except:
    sys.exit("Webframe Exit!")
