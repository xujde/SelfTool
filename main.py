import socket, sys, threading, time # 导入 socket 模块
from PyQt5.QtWidgets import QApplication

Servers_Support_Client_Link_Num =  10
Servers_Support_RecvData_Max = 2048 #接收的最大数据量

class Servers_Log():
    def __init__(self, parent=None):
        self.LogSwitch = False
        self.LogType = 1 #1为print打印

    def Log_Output(self, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
        if self.LogSwitch:
            if(self.LogType == 1):
                print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)

    def Change_Switch(self, Sw):
        self.LogSwitch = Sw

    def Change_Type(self, Tp):
        self.LogType = Tp

class Servers_ClientHandleThread(threading.Thread):
    def __init__(self, Client_id, parent=None):
        super(Servers_ClientHandleThread, self).__init__(parent)
        self.Client_id = Client_id

    def run(self):
        while (getattr(self.Client_id, "_closed") == False):
            try:
                recvdata = self.Client_id.recv(Servers_Support_RecvData_Max) #接收数据
                print("Client_id:", self.Client_id, ",recv data:", recvdata.decode())
            except ConnectionAbortedError as e:
                print("Servers close :", self.Client_id, e)
                break

            if len(recvdata) == 0:
                print(self.Client_id, " close")
                break


class Servers_AcceptThread(threading.Thread):
    def __init__(self, Socket, parent=None):
        super(Servers_AcceptThread, self).__init__(parent)
        self.Socket = Socket
        self.Client_id = []
        self.Client_addr = []
        self.ClientHandleThread = []
        self.Client_Link_Num = 0

    def run(self):
        while True:
            client_id, client_addr = self.Socket.accept()  # 建立客户端连接
            try:
                ClientHandleThread = Servers_ClientHandleThread(client_id)# 创建客户端
                ClientHandleThread.start()
            except Exception as e:
                print("create ClientHandleThread Error:", e)

            Index = self.Client_Link_Num%Servers_Support_Client_Link_Num

            if (self.Client_Link_Num >= Servers_Support_Client_Link_Num):
                self.Client_id[Index].close()
                self.Client_id.pop(Index)
                self.Client_addr.pop(Index)
                self.ClientHandleThread.pop(Index)

                self.Client_id.insert(Index, client_id)
                self.Client_addr.insert(Index, client_addr)
                self.ClientHandleThread.insert(Index, ClientHandleThread)
            else:
                self.Client_id.append(client_id)
                self.Client_addr.append(client_addr)
                self.ClientHandleThread.append(ClientHandleThread)

            self.Client_Link_Num = self.Client_Link_Num + 1

            print('Index:', Index, '连接地址：', self.Client_addr[Index])


class Servers_Socket():
    def __init__(self):
        self.Socket = socket.socket()  # 创建 socket 对象
        self.host = socket.gethostname()  # 获取本地主机名
        self.port = 2608  # 设置端口
        self.Socket.bind((self.host, self.port))  # 绑定端口
        self.Socket.listen(5)  # 等待客户端连接
        try:
            self.AccpetThread = Servers_AcceptThread(self.Socket)
            self.AccpetThread.start()
        except Exception as e:
            print("Create AcceptThread Error:", e)
        # self.UseLog = Log

    def Socket_Recv(self, Client_id):
        try:
            data = Client_id.recv(Servers_Support_RecvData_Max)  # 接收数据
            print('recive:', data.decode())  # 打印接收到的数据
        except ConnectionResetError as e:
            print('Recv Error:', e)

    def Socket_Send(self, Client_id, Send_Msg):
        print("Send_Msg:", Send_Msg)
        Client_id.send(Send_Msg.encode())

    def Socket_Close_Client(self, Client_id):
        Client_id.close()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app = QApplication(sys.argv)

    s = Servers_Socket()

    sys.exit(app.exec_())
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
