import socket, threading, time
from PyQt5.QtCore import QThread, pyqtSignal
from enum import Enum
from queue import Queue

import ServersSystem
from ServersSystem import LogModule
from ServersSystem import LogLevel

Servers_Support_Client_Link_Num =  10
Servers_Support_RecvData_Max = 2048 #接收的最大数据量

Servers_TCP_Port = 2608 #TCP端口号
Servers_UDP_Port = 1997 #UDP端口号

class Protocol(Enum):
    TCP = 1
    UDP = 2
    MQTT = 3

class Servers_Socket():
    def __init__(self, Log, GlobalVal, Queue):
        self.UseLog = Log
        self.UseGlobalVal = GlobalVal
        self.UseQueue = Queue
        self.UseProtocol = Protocol.TCP #默认为TCP
        self.host = socket.gethostname()  # 获取本地主机名
        self.Socket_Create()

    def Socket_Create(self):
        self.DataHandle = Servers_DataHandle(self)
        ServersSystem.Servers_GlobalManager.Global_Set(self.UseGlobalVal, 'SocketSendDataNum', 0)
        ServersSystem.Servers_GlobalManager.Global_Set(self.UseGlobalVal, 'SocketRecvDataNum', 0)
        if self.UseProtocol == Protocol.TCP:
            self.Socket = socket.socket()  # 创建 socket 对象
            self.port = Servers_TCP_Port  # 设置端口
            self.Socket.bind((self.host, self.port))  # 绑定端口
            self.Socket.listen(5)  # 等待客户端连接
            try:
                self.AccpetThread = Servers_AcceptThread(self)
                self.AccpetThread.start()
            except Exception as e:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Create AcceptThread Error:", e)
        elif self.UseProtocol == Protocol.UDP:
            self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 创建 socket 对象
            self.port = Servers_UDP_Port  # 设置端口
            self.Socket.bind((self.host, self.port))  # 绑定端口
            try:
                self.UDPThread = Servers_UDPThread(self)
                self.UDPThread.start()
            except Exception as e:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Create UDPThread Error:", e)

    def Socket_Recv(self, Client_Id):
        try:
            if self.UseProtocol == Protocol.TCP:
                data = Client_Id.recv(Servers_Support_RecvData_Max)  # 接收数据
            elif self.UseProtocol == Protocol.UDP:
                data, Addr = self.Socket.recvfrom(Servers_Support_RecvData_Max)
            else:
                return 0
            PutQueueMsg = str("收：") + str(data)
            self.UseQueue.put(PutQueueMsg)
            self.DataHandle.Data_Analyse(Client_Id, data)
            Num = ServersSystem.Servers_GlobalManager.Global_Get(self.UseGlobalVal, 'SocketRecvDataNum') + len(data)
            ServersSystem.Servers_GlobalManager.Global_Set(self.UseGlobalVal, 'SocketRecvDataNum', Num)
        except ConnectionResetError as e:
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, 'Recv Error:', e)
            return 0
        return len(data)

    def Socket_Send(self, Client_Id, Send_Msg):
        self.DataHandle.Data_Packet(Client_Id, Send_Msg)

    def Socket_Close_Client(self, Client_Id):
        Client_Id.close()
        self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Servers close :", Client_Id)

    def Servers_Socket_Close(self):
        self.Socket.close()

    def Socket_ProtocolSwitch(self, NewProtocol):
        try:
            if NewProtocol == self.UseProtocol.name:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "UseProtocol the same as NewProtocol")
            elif NewProtocol == Protocol.TCP.name:
                self.Socket.close()
                self.UseProtocol = Protocol.TCP
                self.Socket_Create()
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Protocol Switch to :", NewProtocol)
            elif NewProtocol ==  Protocol.UDP.name:
                self.Socket.close()
                self.UseProtocol = Protocol.UDP
                self.Socket_Create()
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Protocol Switch to :", NewProtocol)
            else:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Not Support this Protocol:", NewProtocol)
        except Exception as e:
            print(e)

class Servers_AcceptThread(QThread, threading.Thread):
    Signal = pyqtSignal(int)

    def __init__(self, Servers, parent=None):
        super(Servers_AcceptThread, self).__init__(parent)
        self.Servers = Servers
        self.Socket = Servers.Socket
        self.UseLog = Servers.UseLog
        self.Client_id = []
        self.Client_addr = []
        self.ClientHandleThread = []
        self.ClientLinkTime = [0 for i in range(Servers_Support_Client_Link_Num)]
        self.Client_Link_Num = 0

    def __del__(self):
        for i in range(len(self.Client_id)):
            self.Client_id[i].close()

    def run(self):
        while True:
            try:
                client_id, client_addr = self.Socket.accept()  # 建立客户端连接
                try:
                    ClientHandleThread = Servers_ClientHandleThread(client_id, self.Servers)# 创建客户端
                    ClientHandleThread.Signal.connect(self.Change_ClientLinkFlag)
                    ClientHandleThread.start()
                except Exception as e:
                    self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "create ClientHandleThread Error:", e)
            except Exception as e:
                self.__del__()
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Servers_AcceptThread accept Error:", e)
                break

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
                self.Servers.Socket_Close_Client(self.Servers, self.Client_id[Index])
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
            self.Signal.emit(self.Client_Link_Num)
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level2, 'Index:', Index, '连接地址：', self.Client_addr[Index], 'ClientLinkTime:', self.ClientLinkTime[Index])

    def Change_ClientLinkFlag(self, cClient_id):
        self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level6, "Change_ClientLinkFlag:", cClient_id)
        for i in range(len(self.Client_id)):
            if self.Client_id[i] == cClient_id:
                self.ClientLinkTime[i] = 0
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client", i, "close success")


class Servers_ClientHandleThread(QThread, threading.Thread):
    Signal = pyqtSignal(socket.socket)

    def __init__(self, Client_id, Servers, parent=None):
        super(Servers_ClientHandleThread, self).__init__(parent)
        self.Servers = Servers
        self.Client_id = Client_id
        self.UseLog = Servers.UseLog
        self.UseGlobalVal = Servers.UseGlobalVal

    def __del__(self):
        # 线程状态改变与线程终止
        self.wait()

    def run(self):
        while (getattr(self.Client_id, "_closed") == False):
            recvdatalen = self.Servers.Socket_Recv(self.Client_id)
            if recvdatalen == 0:
                self.Signal.emit(self.Client_id)
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client close", self.Client_id)
                break


class Servers_UDPThread(QThread, threading.Thread):
    Signal = pyqtSignal(int)

    def __init__(self, Servers, parent=None):
        super(Servers_UDPThread, self).__init__(parent)
        self.Servers = Servers
        self.Socket = Servers.Socket
        self.UseLog = Servers.UseLog
        self.UseGlobalVal = Servers.UseGlobalVal
        self.Client_Link_Num = 0

    def __del__(self):
        # 线程状态改变与线程终止
        self.wait()

    def run(self):
        while True:
            try:
                self.Servers.Socket_Recv(None)
                self.Client_Link_Num = self.Client_Link_Num + 1
                self.Signal.emit(self.Client_Link_Num)
            except Exception as e:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Servers_UDPThread Error:", e)
                break


class Servers_DataHandle():
    def __init__(self, Servers, parent=socket):
        self.Servers = Servers
        self.UseGlobalVal = Servers.UseGlobalVal
        self.UseProtocol = Servers.UseProtocol
        self.UseLog = Servers.UseLog
        self.UseQueue = Servers.UseQueue

    def Data_Analyse(self, Client, RecvData):
        try:
            if self.UseProtocol == Protocol.TCP:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client id:", Client, ",Recv data:", RecvData.decode())
                #可增加需要回复的相关数据
                self.Data_Packet(Client, RecvData)
            elif self.UseProtocol == Protocol.UDP:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client addr:", Client, ",Recv data:", RecvData)
                # 可增加需要回复的相关数据
                self.Data_Packet(Client, RecvData)
        except Exception as e:
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Data_Analyse Error:", e)

    def Data_Packet(self, Client, SendData):
        try:
            if self.UseProtocol == Protocol.TCP:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client id:", Client, ",Send data:",  SendData)
                #可增加对回复数据的自定义打包
                Num =  Client.send(SendData)
                Num = Num + ServersSystem.Servers_GlobalManager.Global_Get(self.UseGlobalVal, 'SocketSendDataNum')
                ServersSystem.Servers_GlobalManager.Global_Set(self.UseGlobalVal, 'SocketSendDataNum', Num)
                PutQueueMsg = str("发：") + str(SendData)
                self.UseQueue.put(PutQueueMsg)
            elif self.UseProtocol == Protocol.UDP:
                self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level3, "Client addr:", Client, ",Send data:",  SendData)
                # 可增加对回复数据的自定义打包
                Num = self.Servers.Socket.sendto(SendData, Client)
                Num = Num + ServersSystem.Servers_GlobalManager.Global_Get(self.UseGlobalVal, 'SocketSendDataNum')
                ServersSystem.Servers_GlobalManager.Global_Set(self.UseGlobalVal, 'SocketSendDataNum', Num)
                PutQueueMsg = str("发：") + str(SendData)
                self.UseQueue.put(PutQueueMsg)
        except Exception as e:
            self.UseLog.Log_Output(LogModule.SocModule, LogLevel.Level1, "Data_Packet Error:", e)
