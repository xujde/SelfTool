import socket, threading, time
from PyQt5.QtCore import QThread, pyqtSignal

from ServersSystem import LogModule
from ServersSystem import LogLevel

Servers_Support_Client_Link_Num =  10
Servers_Support_RecvData_Max = 2048 #接收的最大数据量

class Servers_ClientHandleThread(QThread, threading.Thread):
    Signal = pyqtSignal(socket.socket)

    def __init__(self, Client_id, Log, parent=None):
        super(Servers_ClientHandleThread, self).__init__(parent)
        self.Client_id = Client_id
        self.UseLog = Log

    def run(self):
        while (getattr(self.Client_id, "_closed") == False):
            try:
                recvdata = self.Client_id.recv(Servers_Support_RecvData_Max) #接收数据
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level5, "Client_id:", self.Client_id, ",recv data:", recvdata.decode())
            except ConnectionAbortedError as e:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Servers close :", self.Client_id, e)
                self.Signal.emit(self.Client_id)
                break

            if len(recvdata) == 0:
                self.Signal.emit(self.Client_id)
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, self.Client_id, " close")
                break


class Servers_AcceptThread(QThread, threading.Thread):
    def __init__(self, Socket, Log, parent=None):
        super(Servers_AcceptThread, self).__init__(parent)
        self.Socket = Socket
        self.UseLog = Log
        self.Client_id = []
        self.Client_addr = []
        self.ClientHandleThread = []
        self.ClientLinkTime = [0 for i in range(Servers_Support_Client_Link_Num)]
        self.Client_Link_Num = 0

    def run(self):
        while True:
            client_id, client_addr = self.Socket.accept()  # 建立客户端连接
            try:
                ClientHandleThread = Servers_ClientHandleThread(client_id, self.UseLog)# 创建客户端
                ClientHandleThread.Signal.connect(self.Change_ClientLinkFlag)
                ClientHandleThread.start()
            except Exception as e:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "create ClientHandleThread Error:", e)

            Index = self.Client_Link_Num%Servers_Support_Client_Link_Num

            if (self.Client_Link_Num >= Servers_Support_Client_Link_Num):
                #先查找是否有客户端主动断开连接
                for i in range(len(self.ClientLinkTime)):
                    if self.ClientLinkTime[i] == 0:
                        Index = i
                        break

                #查找最早建立的连接
                time_min_index = 0
                for j in range(len(self.ClientLinkTime)):
                    if self.ClientLinkTime[j] < self.ClientLinkTime[time_min_index]:
                        time_min_index = j
                Index = time_min_index

                #断开连接
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
            self.ClientLinkTime[Index] = time.time()

            self.Client_Link_Num = self.Client_Link_Num + 1

            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level2, 'Index:', Index, '连接地址：', self.Client_addr[Index], 'ClientLinkTime:', self.ClientLinkTime[Index])

    def Change_ClientLinkFlag(self, cClient_id):
        self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level6, "Change_ClientLinkFlag:", cClient_id)
        for i in range(len(self.Client_id)):
            if self.Client_id[i] == cClient_id:
                self.ClientLinkTime[i] = 0
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client", i, "close success")

class Servers_Socket():
    def __init__(self, Log):
        self.UseLog = Log
        self.Socket = socket.socket()  # 创建 socket 对象
        self.host = socket.gethostname()  # 获取本地主机名
        self.port = 2608  # 设置端口
        self.Socket.bind((self.host, self.port))  # 绑定端口
        self.Socket.listen(5)  # 等待客户端连接
        try:
            self.AccpetThread = Servers_AcceptThread(self.Socket, self.UseLog)
            self.AccpetThread.start()
        except Exception as e:
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Create AcceptThread Error:", e)

    def Socket_Recv(self, Client_id):
        try:
            data = Client_id.recv(Servers_Support_RecvData_Max)  # 接收数据
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, 'recive:', data.decode())  # 打印接收到的数据
        except ConnectionResetError as e:
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, 'Recv Error:', e)

    def Socket_Send(self, Client_id, Send_Msg):
        self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Send_Msg:", Send_Msg)
        Client_id.send(Send_Msg.encode())

    def Socket_Close_Client(self, Client_id):
        Client_id.close()
