import socket, threading, time
from PyQt5.QtWidgets import (QWidget, QMenu, QMainWindow, QAction, QTextEdit,QGridLayout, QFileDialog,
                             QPushButton, QLabel, QRadioButton, QComboBox, QLineEdit, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QRect, QSize, pyqtSignal, QThread
import matplotlib
from queue import Queue

#以下为自定义模块
import ServersSystem
from ServersSystem import LogModule
from ServersSystem import LogLevel
from ServersSystem import LogType
import ServersSocket
from ServersSocket import Protocol

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决坐标轴中文显示问题
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号不显示的问题

class Servers_UiUpdateWidgetMsg_Thread(QThread, threading.Thread):  # 继承父类threading.Thread
    Signal = pyqtSignal(str)

    def __init__(self, Widget):
        super().__init__()
        self.UseWidget = Widget
        self.UseQueue = Widget.UseQueue
        self.UseLog = Widget.UseLog

    def run(self):
        while True:
            # 阻塞程序，时刻监听接收消息
            try:
                msg = self.UseQueue.get()
                Message = (time.strftime("[%Y-%m-%d %H:%M:%S ]", time.localtime()) + msg)
                self.Signal.emit(Message)
                self.UseLog.NormalLog_Output(LogModule.SocModule, LogLevel.Level6, "Servers_UiUpdateMsg_Thread Recv Msg:", msg)
            except Exception as e:
                self.UseLog.ErrorLog_Output("Servers_UiUpdateMsg_Thread Error:", e)


class Servers_UiUpdateWidgetData_Thread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, threadID, name, counter, Widget):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.UseGlobalVal = Widget.UseGlobalVal
        self.Widget = Widget

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        while True:
            time.sleep(1)
            SendNum = ServersSystem.Servers_GlobalManager.Global_Get(self.UseGlobalVal, 'SocketSendDataNum')
            RecvNum = ServersSystem.Servers_GlobalManager.Global_Get(self.UseGlobalVal, 'SocketRecvDataNum')
            self.Widget.Servers_CommunicationData_Num.setText('发送数据量：'+ str(SendNum)+ ' Byte --- 接收数据量：'+ str(RecvNum)+ ' Byte')


class Servers_Widget(QWidget, QThread):
    def __init__(self, UseLog, Soc, GlobalVal, Queue):
        super().__init__()
        self.UseLog = UseLog
        self.UseSoc = Soc
        self.UseGlobalVal = GlobalVal
        self.UseQueue = Queue
        self.Servers_Widget_Init()

        try:
            self.UiUpdateWidgetDataThread = Servers_UiUpdateWidgetData_Thread(1, "ServersDataUpdateThread", 2, self)
            self.UiUpdateWidgetDataThread.setDaemon(True)
            self.UiUpdateWidgetDataThread.start()
            self.UiUpdateWidgetMsgThread = Servers_UiUpdateWidgetMsg_Thread(self)
            self.UiUpdateWidgetMsgThread.setDaemon(True)
            self.UiUpdateWidgetMsgThread.Signal.connect(self.ServersShowRecvData)
            self.UiUpdateWidgetMsgThread.start()
        except Exception as e:
            self.UseLog.ErrorLog_Output("Widget Create and start Thread Error:", e)

    def Servers_Widget_Init(self):
        self.ServersUI_Setup()
        self.ServersUI_Layout()
        self.ServersUI_SignalInit()

    def ServersUI_Setup(self):
        #单选框
        self.ServersComboBoxList = ['TCP', 'UDP', 'HTTP', 'HTTPS', 'MQTT']
        self.ServersComboBox = QLabel('网络协议')
        self.Servers_ComboBox = QComboBox(self)
        self.Servers_ComboBox.addItems(self.ServersComboBoxList)
        self.Servers_ComboBox.setMinimumSize(QSize(100, 20))
        Servers_ComboBox_DefaultIndex = self.ServersComboBoxList.index(str(self.UseSoc.UseProtocol.name))
        self.Servers_ComboBox.setCurrentIndex(Servers_ComboBox_DefaultIndex)  # 设置默认值

        self.Servers_IpAddr = QLabel('服务器地址')
        self.Servers_Ip_Addr = QLabel()
        self.Servers_Ip_Addr.setGeometry(QRect(10, 20, 100, 20))
        self.Servers_PortNum = QLabel('服务器端口')
        self.Servers_Port_Num = QLabel()
        self.Servers_Port_Num.setGeometry(QRect(10, 20, 100, 20))
        self.Servers_LinkNum = QLabel()
        self.Servers_Link_Num = QLabel()
        self.Servers_Link_Num.setGeometry(QRect(10, 20, 100, 20))
        self.Servers_CommunicationData_Num = QLabel()
        self.ServersUpdateUiShow()

        #行编辑和文本编辑框
        self.ServersLineEdit = QLineEdit()
        self.ServerstextEdit = QTextEdit()

        #按钮
        self.ServersClearInputQPushButton = QPushButton("清空输入框", self)
        self.ServersClearOutputQPushButton = QPushButton("清空输出框", self)
        self.ServersSwitchProtocolQPushButton = QPushButton("切换协议", self)
        self.ServersClearInputQPushButton.clicked.connect(self.ServersPushButtonClickedHandle)
        self.ServersClearOutputQPushButton.clicked.connect(self.ServersPushButtonClickedHandle)
        self.ServersSwitchProtocolQPushButton.clicked.connect(self.ServersPushButtonClickedHandle)

        #单选按钮
        self.ServersHexQRadioButton = QRadioButton('Hex', self)
        self.ServersDexQRadioButton = QRadioButton('Dex', self)
        self.ServersDexQRadioButton.setChecked(True)
        self.ServersHexQRadioButton.toggled.connect(self.ServersRadioButtonClickedHandle)
        self.ServersDexQRadioButton.toggled.connect(self.ServersRadioButtonClickedHandle)

    def ServersUI_Layout(self):
        grid = QGridLayout()
        grid.setSpacing(20)

        X_Index = 1;Y_Index = 0 #X:行下标,Y:列下标
        Y_ServersComboBoxStep = 1
        X_ServersLabelOffset = 1;X_ServersLabelStep = 1;Y_ServersLabelStep = 1
        X_ServersPushButtonStep = 1;Y_ServersPushButtonOffset = 3
        X_ServersEditOffset = 1;X_ServersEditStep = 1;Y_ServersEditOffset = 2
        Y_ServersRadioButtontOffset = 4;X_ServersRadioButtonStep = 2
        Y_ServersCommunicationDataNumOffset = 2

        grid.addWidget(self.ServersComboBox, X_Index, Y_Index)
        grid.addWidget(self.Servers_ComboBox, X_Index, Y_Index + Y_ServersComboBoxStep)

        grid.addWidget(self.Servers_IpAddr, X_Index + X_ServersLabelOffset, Y_Index)
        grid.addWidget(self.Servers_Ip_Addr, X_Index +  X_ServersLabelOffset, Y_Index + Y_ServersLabelStep)

        grid.addWidget(self.Servers_PortNum, X_Index + X_ServersLabelOffset + X_ServersLabelStep, Y_Index)
        grid.addWidget(self.Servers_Port_Num, X_Index + X_ServersLabelOffset + X_ServersLabelStep, Y_Index + Y_ServersLabelStep)

        grid.addWidget(self.Servers_LinkNum, X_Index + X_ServersLabelOffset + X_ServersLabelStep*2, Y_Index)
        grid.addWidget(self.Servers_Link_Num, X_Index + X_ServersLabelOffset + X_ServersLabelStep*2, Y_Index + Y_ServersLabelStep)

        grid.addWidget(self.ServersLineEdit, X_Index + X_ServersEditOffset, Y_Index + Y_ServersEditOffset)
        grid.addWidget(self.ServerstextEdit, X_Index + X_ServersEditOffset + X_ServersEditStep, Y_Index + Y_ServersEditOffset)

        grid.addWidget(self.ServersClearInputQPushButton, X_Index + X_ServersPushButtonStep, Y_Index + Y_ServersPushButtonOffset)
        grid.addWidget(self.ServersClearOutputQPushButton, X_Index + 2*X_ServersPushButtonStep, Y_Index + Y_ServersPushButtonOffset)
        grid.addWidget(self.ServersSwitchProtocolQPushButton, X_Index + 3*X_ServersPushButtonStep, Y_Index + Y_ServersPushButtonOffset)

        grid.addWidget(self.ServersHexQRadioButton, X_Index, Y_Index + Y_ServersRadioButtontOffset)
        grid.addWidget(self.ServersDexQRadioButton, X_Index + X_ServersRadioButtonStep, Y_Index + Y_ServersRadioButtontOffset)

        grid.addWidget(self.Servers_CommunicationData_Num, X_Index, Y_Index + Y_ServersCommunicationDataNumOffset)
        self.setLayout(grid)

    def ServersUI_SignalInit(self):
        if self.UseSoc.UseProtocol == Protocol.TCP:
            self.UseSoc.AccpetThread.Signal.connect(self.ServersUpdateUiData)
        elif self.UseSoc.UseProtocol == Protocol.UDP:
            self.UseSoc.UDPThread.Signal.connect(self.ServersUpdateUiData)

    def ServersPushButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "清空输入框":
            self.ServersLineEdit.clear()

        if sender.text() == "清空输出框":
            self.ServerstextEdit.clear()

        if sender.text() == "切换协议":
            self.UseSoc.Socket_ProtocolSwitch(self.Servers_ComboBox.currentText())
            self.ServersUpdateUiShow()

    def ServersRadioButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "Hex":
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Hex")

        if sender.text() == "Dex":
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Dex")

    def ServersUpdateUiData(self, data):
        self.Servers_Link_Num.setText(str(data))

    def ServersUpdateUiShow(self):
        self.Servers_Ip_Addr.setText(str(socket.gethostbyname(self.UseSoc.host)))
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level2, socket.gethostbyname_ex(self.UseSoc.host))
        self.Servers_Port_Num.setText(str(self.UseSoc.port))
        self.Servers_CommunicationData_Num.setText('发送数据量：'+ str(0)+ ' Byte --- 接收数据量：'+ str(0)+ ' Byte')
        if self.UseSoc.UseProtocol == Protocol.TCP:
            self.Servers_LinkNum.setText('连接次数')
            self.Servers_Link_Num.setText(str(self.UseSoc.AccpetThread.Client_Link_Num))
        elif self.UseSoc.UseProtocol == Protocol.UDP:
            self.Servers_LinkNum.setText('通信次数')
            self.Servers_Link_Num.setText(str(self.UseSoc.UDPThread.Client_Link_Num))

    def ServersShowRecvData(self, RecvData):
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "ShowRecvData:", RecvData,"len:", len(RecvData))
        if(len(RecvData)):
            try:
                self.ServerstextEdit.append(RecvData)
            except Exception as e:
                self.UseLog.ErrorLog_Output("ServersShowRecvData  ServerstextEdit Error:", e)


class Servers_MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.UseLog = ServersSystem.Servers_Log()
        self.UseGlobalVal = ServersSystem.Servers_GlobalManager()  # 初始化参数
        self.UseQueue = Queue()
        self.UseSoc = ServersSocket.Servers_Socket(self.UseLog, self.UseGlobalVal, self.UseQueue)
        self.UseWidget = Servers_Widget(self.UseLog, self.UseSoc, self.UseGlobalVal, self.UseQueue)
        self.Servers_MainUI_Init()

    def Servers_MainUI_Init(self):
        self.setCentralWidget(self.UseWidget)

        #创建状态栏的小窗口
        self.statusBar().showMessage('Ready')

        self.Servers_FileMenu_Init()
        self.Servers_LogMenu_Init()

        self.setGeometry(300, 300, 800, 300)
        self.setWindowIcon(QIcon('./Logo_Picture/ServerMainUI.jpeg'))
        self.setWindowTitle('Servers')
        self.show()

    def Servers_FileMenu_Init(self):
        self.Open_file_menu = QAction(QIcon('./Logo_Picture/Open.png'), "打开", self)
        self.Open_file_menu.setShortcut('Ctrl+' + 'O')
        self.Open_file_menu.setStatusTip('Open File')
        self.Open_file_menu.triggered.connect(self.Servers_ReloadDialog)
        self.Save_file_menu = QAction(QIcon('./Logo_Picture/Save.jpeg'), "保存", self)
        self.Save_file_menu.setShortcut('Ctrl+' + 'S')
        self.Save_file_menu.setStatusTip('Save File')
        self.Save_file_menu.triggered.connect(self.Servers_SaveDialog)
        # 创建一个菜单栏
        filemenubar = self.menuBar()
        # 添加菜单
        FileMenu = filemenubar.addMenu('&文件')
        # 添加事件
        FileMenu.addAction(self.Open_file_menu)
        FileMenu.addAction(self.Save_file_menu)

    def Servers_LogMenu_Init(self):
        #日志输出类型UI选项
        self.LogTypeList = []

        Log_type = QAction("日志输出类型1", self, checkable=True)
        Log_type.setStatusTip('Use Print Output')
        Log_type.setChecked(True)
        Log_type.triggered.connect(self.Servers_LogOption)
        self.LogTypeList.append(Log_type)
        Log_type = QAction("日志输出类型2", self, checkable=True)
        Log_type.setStatusTip('Use File Output')
        Log_type.setChecked(False)
        Log_type.triggered.connect(self.Servers_LogOption)
        self.LogTypeList.append(Log_type)

        Log_type_menu = QMenu('日志输出类型', self)
        for i in range(len(self.LogTypeList)):
            Log_type_menu.addAction(self.LogTypeList[i])

        # 日志输出模块UI选项
        self.LogModuleList = []

        Log_Sysmodule = QAction("系统日志模块", self, checkable=True)
        Log_Sysmodule.setStatusTip('系统日志模块')
        Log_Sysmodule.setChecked(False)
        Log_Sysmodule.triggered.connect(self.Servers_LogOption)
        self.LogModuleList.append(Log_Sysmodule)
        Log_Uimodule = QAction("UI日志模块", self, checkable=True)
        Log_Uimodule.setStatusTip('UI日志模块')
        Log_Uimodule.setChecked(False)
        Log_Uimodule.triggered.connect(self.Servers_LogOption)
        self.LogModuleList.append(Log_Uimodule)
        Log_Socmodule = QAction("网络日志模块", self, checkable=True)
        Log_Socmodule.setStatusTip('网络日志模块')
        Log_Socmodule.setChecked(False)
        Log_Socmodule.triggered.connect(self.Servers_LogOption)
        self.LogModuleList.append(Log_Socmodule)

        Log_Modue_menu = QMenu('日志模块选项', self)
        for i in range(len(self.LogModuleList)):
            Log_Modue_menu.addAction(self.LogModuleList[i])

        # 日志输出等级UI选项
        self.LogLevelList = []

        for i in range(int(str(LogLevel.LogLevelMax.value))):
            Log_level = QAction("日志输出等级"+str(i+1), self, checkable=True)
            Log_level.setStatusTip('日志输出等级'+str(i+1))
            Log_level.setChecked(False)
            Log_level.triggered.connect(self.Servers_LogOption)
            self.LogLevelList.append(Log_level)

        Log_Level_menu = QMenu('日志输出等级', self)
        for i in range(len(self.LogLevelList)):
            Log_Level_menu.addAction(self.LogLevelList[i])

        # 创建一个菜单栏
        Logmenubar = self.menuBar()
        LogMenu = Logmenubar.addMenu('&日志')
        LogMenu.addMenu(Log_Modue_menu)
        LogMenu.addMenu(Log_Level_menu)
        LogMenu.addMenu(Log_type_menu)

    def Servers_ReloadDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            f = open(fname[0], 'r', encoding = 'utf-8')
            with f:
                data = f.read()
                self.UseWidget.ServersLineEdit.setText(data)

    def Servers_SaveDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, fname[0])
            f = open(fname[0], 'w', encoding = 'utf-8')
            with f:
                f.write(self.UseWidget.ServerstextEdit.toPlainText())
            f.close()

    def Servers_LogOption(self):
        sender = self.sender()
        try:

            for i in range(len(self.LogTypeList)):  #日志输出类型选项只选其一
                if sender.text() == self.LogTypeList[i].text():
                    self.UseLog.Change_Type(LogType(i+1))
                    self.LogTypeList[i].setChecked(True)
                    for r in range(len(self.LogTypeList)):
                        if r != i:  #将未选中的选项取消
                            self.LogTypeList[r].setChecked(False)
                            # print("LogTypeList", i, sender.text(), r)

            for j in range(len(self.LogModuleList)):    #日志输出模块选项可多选
                if sender.text() == self.LogModuleList[j].text():
                    self.UseLog.Change_Module((j+1), self.LogModuleList[j].isChecked())
                    self.LogModuleList[j].setChecked(self.LogModuleList[j].isChecked())
                    # print("LogModuleList", j, sender.text(), self.LogModuleList[j].isChecked())


            for k in range(len(self.LogLevelList)): #日志等级选项只选其一
                if sender.text() == self.LogLevelList[k].text():
                    self.UseLog.Change_Level(k+1)
                    self.LogLevelList[k].setChecked(True)
                    for r in range(len(self.LogLevelList)):
                        if r != k:  #将未选中的选项取消
                            self.LogLevelList[r].setChecked(False)
                            # print("LogLevelList", k, sender.text(), r)

        except Exception as e:
            self.UseLog.ErrorLog_Output("log option error:", e)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.UseLog.Log_Close()
            event.accept()
        else:
            event.ignore()
