import time, threading, random
from PyQt5.QtWidgets import (QWidget, QPushButton, QMainWindow, QAction, QTextEdit, QLineEdit,
                             QGridLayout, QFileDialog, QLabel, QRadioButton, QMenu, QGroupBox,
                             QListWidget, QCheckBox, QListWidgetItem, QDesktopWidget, QComboBox, QMessageBox)
from PyQt5.QtGui import QIcon, QPainter, QFont, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import Qt, QSize, QRect, QTimer, pyqtSignal, QThread, QPoint, QMetaObject, QCoreApplication
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import serial.tools.list_ports
import numpy as np

import System
import SerialToolSer
from System import LogModule
from System import LogLevel
from System import LogType

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决坐标轴中文显示问题
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号不显示的问题

oneself = False  # 标志为模块自己产生随机数绘图
PaintWithAxis_UpdateData_separator = ','
PaintWithAxis_UpdateData_Index = 1


class Serial_Tool_PaintThread(QThread):
    signal = pyqtSignal() #信号

    def __init__(self,parent=None):
        super(Serial_Tool_PaintThread,self).__init__(parent)

    def start_timer(self):
       self.start() #启动线程

    def run(self):
        while True:
            self.signal.emit() #发送信号
            time.sleep(0.1)

class Serial_Tool_PaintUi(QWidget):
    def SetupUi(self, Form):
        self.Title = QLabel(Form)
        self.Title.setGeometry(QRect(10, 10, 351, 31))
        self.Title.setAlignment(Qt.AlignCenter)
        self.Title.setObjectName("Title")

        self.CurValue = QLabel(Form)
        self.CurValue.setGeometry(QRect(430, 10, 91, 31))
        self.CurValue.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.CurValue_Show = QLabel(Form)
        self.CurValue_Show.setGeometry(QRect(520, 10, 111, 31))
        self.CurValue_Show.setText("")

        self.Show_Paint = QLabel(Form)
        self.Show_Paint.setGeometry(QRect(10, 50, 950, 400))
        self.Show_Paint.setText("")

        self.start_Button = QPushButton(Form)
        self.start_Button.setGeometry(QRect(680, 5, 121, 41))

        self.stop_Button = QPushButton(Form)
        self.stop_Button.setGeometry(QRect(800, 5, 121, 41))

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.CurValue.setText(_translate("Form", "测量值当前值: "))
        self.Title.setText(_translate("Form", "测量值实时反馈折线图"))
        self.start_Button.setText(_translate("Form", "启动"))
        self.stop_Button.setText(_translate("Form", "停止"))

class Serial_Tool_Paint(QWidget):
    def __init__(self, parent=None):
        super(Serial_Tool_Paint, self).__init__(parent)
        self.Paint_Ui = Serial_Tool_PaintUi()
        self.Paint_Ui.SetupUi(self) #初始化ui

        self.init() #初始化变量
        self.Signal_Func() #信号槽链接函数

        if oneself == True:#如果是模块自己运行则启动多线程发送随机数
            self.PaintThread = Serial_Tool_PaintThread() #多线程实例化
            self.PaintThread.start_timer() #启动线程
            self.PaintThread.signal.connect(self.Create_Random_Num) #线程启动槽函数

    #链接信号槽函数
    def Signal_Func(self):
        self.Paint_Ui.start_Button.clicked.connect(self.Start_Handle) #启动按钮单击信号
        self.Paint_Ui.stop_Button.clicked.connect(self.Stop_Handle)  #停止按钮单击信号

    #生成随机数
    def Create_Random_Num(self):
        num = random.uniform(0, 5) # 生成随机数，浮点类型
        num1 = round(num, 2) # 控制随机数的精度，保留两位小数
        self.Change_PointList(num1)

    #初始化变量函数
    def init(self):
        self.UsePaint = QPainter()  # 绘制类实例
        self.Picture = QPixmap(950,400) #设置图片大小
        self.PointList = [ [0, 0] ] #保存绘制点位列表
        self.X_Part = 100 #X轴分成多少等份
        self.Y_Part = 5 #Y轴分成多少等份

        self.X_Part1 = 950/self.X_Part #每一等份的宽度
        self.Y_Part1 = 400/self.Y_Part #每一等份的高度

        self.Run_Flag = False #运行标志位

    #启动按钮槽函数，置位运行标志
    def Start_Handle(self):
        self.Run_Flag = True

    #停止按钮槽函数，复位运行标志
    def Stop_Handle(self):
        self.Run_Flag = False

    #修改列表点位
    def Change_PointList(self, value):
        if self.Run_Flag == True:
            self.Paint_Ui.CurValue_Show.setText(str(value)) #设置标签显示当前值
            self.Begin_X = 0    #初始化起点
            self.Begin_Y = 400  #初始化起点
            if len(self.PointList) >= (self.X_Part+1): #X轴950化成95等份
                self.PointList = self.PointList[-self.X_Part: ] #截取列表保留后95位
                for i in self.PointList: #遍历列表，每个点位X轴左移一位(即减小1)
                    i[0] -= self.X_Part1
            x = self.PointList[-1][0] + self.X_Part1 #新增点位的X轴
            y = value                        #新增点位的Y轴
            self.PointList.append([x, y]) #将新增的点位添加到列表

            self.Picture.fill(Qt.white)  # 设置为白底色
            self.ReadPonitDraw()  # 读取列表点位进行绘制

    #读取列表点位进行绘制
    def ReadPonitDraw(self):
        #解析列表中点位进行移位计算
        for PointList in self.PointList:
            self.End_X = PointList[0]        # X轴终点位置
            # 输入的数值为0-5.画布高度为400，画布左上角为0，0。改为左下角为0，0
            self.End_Y = 400 - PointList[1] * self.Y_Part1
            self.Uptate_Paint() #调用绘制图形

        self.Paint_Ui.Show_Paint.setPixmap(self.Picture) # 将图像显示在标签上

    #绘制函数
    def Uptate_Paint(self):
        self.UsePaint.begin(self.Picture) # 开始在目标设备上面绘制
        self.UsePaint.setPen(QPen(QColor("black"), 1))# 设置画笔颜色，粗细
        # 绘制一条指定了端点坐标的线，绘制从（self.beg_x,self.beg_y）到（self.end_x,self.end_y）的直线
        self.UsePaint.drawLine(QPoint(self.Begin_X, self.Begin_Y),QPoint(self.End_X, self.End_Y) )
        self.UsePaint.end() #结束在目标设备上面绘制
        self.Begin_X = self.End_X #改变结束后的坐标
        self.Begin_Y = self.End_Y

class Serial_Tool_PaintWithAxisThread(QThread):
    signal = pyqtSignal(str) #信号

    def __init__(self, GlobalVal, parent=None):
        super(Serial_Tool_PaintWithAxisThread,self).__init__(parent)
        self.UseGlobalVal = GlobalVal

    def start_timer(self):
       self.start() #启动线程

    def run(self):
        while System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_Start_Flag'):
            if(System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'Serial_Open_Flag') and System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_UpdateData_Flag')):
                #Value = 1#random.randint(1, 100) #可换成需要的真实数据
                self.signal.emit(System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_UpdateData')) #发送信号
                System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_UpdateData_Flag', False)
            # else:
            #     Value = random.randint(1, 100)
            #     self.signal.emit(Value)  # 发送信号
            time.sleep(1)

class Serial_Tool_PaintWithAxis(FigureCanvas):
    """
    创建画板类
    """
    def __init__(self, width=3.2, height=2.7):
        self.UseFigure = Figure(figsize=(width, height), dpi=70)
        super(Serial_Tool_PaintWithAxis, self).__init__(self.UseFigure)
        self.Axis = self.UseFigure.add_subplot(111)  # 111表示1行1列，第一张曲线图
        self.Data_Num = 200     # X轴最大值,要大于1（即X轴长度）
        self.YData_Max = 120    # Y轴最大值
        self.Updata_Count = 0  # 累计更新Updata_Count个数据后更新绘图，必须小于self.Data_Num
        self.Sign_Num = 2
        self.HLine = [self.Axis.axhline(0, visible=True) for i in range(self.Sign_Num)]#平行于X轴
        self.VLine = [self.Axis.axvline(0, visible=True) for i in range(self.Sign_Num)]#平行于Y轴

    def Add_Line(self, x_data, y_data, y2_data=None):
        self.Line = Line2D(x_data, y_data)  # 绘制2D折线图

        # ------------------调整折线图基本样式---------------------#

        # self.Line.set_ls('--')  # 设置连线
        # self.Line.set_marker('*') # 设置每个点
        self.Line.set_color('red')  # 设置线条颜色

        self.Axis.grid(True)  # 添加网格
        self.Axis.set_title('动态曲线')  # 设置标题

        # 设置xy轴最大最小值,找到x_data, y_data最大最小值
        self.Axis.set_xlim(np.min(x_data), np.max(x_data) + 2, auto = True)
        self.Axis.set_ylim(np.min(y_data), np.max(y_data) + 2, auto = True)  # y轴稍微多一点，会好看一点
        self.XData_Max = np.min(x_data)
        self.YData_Max = np.max(y_data)

        self.Axis.set_xlabel('x坐标')  # 设置坐标名称
        self.Axis.set_ylabel('y坐标')

        # 在曲线下方填充颜色
        # self.ax.fill_between(x_data, y_data, color='g', alpha=0.1)

        self.Axis.legend([self.Line], ['Temp'])  # 添加图例

        # ------------------------------------------------------#
        self.Axis.add_line(self.Line)


        # 绘制第二条曲线
        # self.Line2 = Line2D(x_data, y2_data)
        # self.Axis.add_line(self.Line2)
        # self.Line2.set_color('red')  # 设置线条颜色
        # self.Axis.legend([self.Line, self.Line2], ['sinx', 'cosx'])  # 添加图例
        #
        self.Axis2 = self.Axis.twinx()
        self.Axis2.set_ylim(np.min(y_data), np.max(y_data) + 2)
        self.Axis2.set_ylabel('y2坐标')

    def Change_Axis_XYlim(self, X_Data, Y_Data):
        self.Axis.set_xlim(np.min(X_Data), np.max(X_Data) + 2, auto=True)
        self.Axis.set_ylim(np.min(Y_Data), np.max(Y_Data) + 2, auto=True)  # y轴稍微多一点，会好看一点

        self.XData_Max = np.min(X_Data)
        self.YData_Max = np.max(Y_Data)

        self.Axis2 = self.Axis.twinx()
        self.Axis2.set_ylim(np.min(Y_Data), np.max(Y_Data) + 2)
        self.Axis2.set_ylabel('y2坐标')

class Serial_Tool_PaintWithAxisUi(QMainWindow):
    def __init__(self, Log, GlobalVal):
        super(Serial_Tool_PaintWithAxisUi, self).__init__()
        self.UseLog = Log
        self.UseGlobalVal = GlobalVal
        self.Sign_Select = 1

        self.setWindowTitle('绘制动态曲线')
        Wide = 1000;High = 800
        self.Start_X = 10;self.Start_Y = 10
        self.resize(Wide, High)

        # 创建一个groupbox, 用来画动态曲线
        self.groupBox = QGroupBox(self)
        self.groupBox.setGeometry(QRect(self.Start_X, self.Start_Y, Wide - 2*self.Start_X, High - 2*self.Start_Y))

        self.LineFigureLayout = QGridLayout(self.groupBox)

        self.Button_Init()

        self.LineEdit_Init()

        self.Load_DynamicLine()  # 加载动态曲线

        self.setLayout(self.LineFigureLayout)

        if oneself == True:  # 如果是模块自己运行则启动多线程发送随机数
            # 创建定时器，使曲线图动态更新
            self.UseTimer = QTimer()
            self.UseTimer.start(10)
            self.TimeStamp = time.time()
            self.UseTimer.timeout.connect(self.UpdateData_OneSelf)
        else:
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', True)
            self.TimeStamp = time.time()
            self.PaintWithAxisThread = Serial_Tool_PaintWithAxisThread(self.UseGlobalVal)
            self.PaintWithAxisThread.signal.connect(self.UpdateData_UseSignal)
            self.PaintWithAxisThread.start()

    def Load_DynamicLine(self):
        self.LineFigure = Serial_Tool_PaintWithAxis()

        self.LineFigure.UseFigure.canvas.mpl_connect('button_press_event', self.Mouse_pressEvent)  # 鼠标事件处理

        self.LineFigureLayout.addWidget(self.LineFigure, 0, 0, 1, 5)

        if oneself == True:  # 如果是模块自己运行则启动多线程发送随机数
            # 准备数据，绘制曲线
            x_data = np.arange(-4, 4, 0.02)
            y_data = np.sin(x_data)
            # y2_data = np.cos(x_data)
            # self.LineFigure.Add_Line(x_data, y_data, y2_data)
        else:
            x_data = np.arange(0, self.LineFigure.Data_Num, 1)
            y_data = [self.LineFigure.YData_Max for i in range(self.LineFigure.Data_Num)]
            for i in range(1, self.LineFigure.Data_Num):
                y_data[i] = random.randint(1, self.LineFigure.YData_Max)

        self.LineFigure.Update_Y_Data = [0]*self.LineFigure.Data_Num
        if(self.LineFigure.Updata_Count > self.LineFigure.Data_Num):
            self.LineFigure.Updata_Count = self.LineFigure.Data_Num
        elif (self.LineFigure.Updata_Count < 1):
            self.LineFigure.Updata_Count = 1

        self.LineFigure.Add_Line(x_data, y_data)

    def Button_Init(self):
        self.StartButton = QPushButton('开始', self)
        self.StopButton = QPushButton("停止", self)
        self.SaveButton = QPushButton("保存", self)
        self.StartButton.clicked.connect(self.PushButtonClickedHandle)
        self.StopButton.clicked.connect(self.PushButtonClickedHandle)
        self.SaveButton.clicked.connect(self.PushButtonClickedHandle)
        self.LineFigureLayout.addWidget(self.StartButton, 1, 0)
        self.LineFigureLayout.addWidget(self.StopButton, 1, 1)
        self.LineFigureLayout.addWidget(self.SaveButton, 1, 2)

    def LineEdit_Init(self):
        X1LineEdit = QLabel('X1')
        Y1LineEdit = QLabel('Y1')
        X2LineEdit = QLabel('X2')
        Y2LineEdit = QLabel('Y2')
        XDiffLineEdit = QLabel('X-Diff')
        YDiffLineEdit = QLabel('Y-Diff')

        self.X1LineEdit = QLineEdit()
        self.Y1LineEdit = QLineEdit()
        self.X2LineEdit = QLineEdit()
        self.Y2LineEdit = QLineEdit()
        self.XDiffLineEdit = QLineEdit()
        self.YDiffLineEdit = QLineEdit()

        self.XY1Button = QRadioButton('XY1', self)
        self.XY2Button = QRadioButton('XY2', self)
        self.XY1Button.setChecked(True)

        self.LineFigureLayout.addWidget(self.XY1Button, 2, 0)
        self.LineFigureLayout.addWidget(X1LineEdit, 2, 1)
        self.LineFigureLayout.addWidget(self.X1LineEdit, 2, 2)
        self.LineFigureLayout.addWidget(Y1LineEdit, 2, 3)
        self.LineFigureLayout.addWidget(self.Y1LineEdit, 2, 4)
        self.LineFigureLayout.addWidget(self.XY2Button, 3, 0)
        self.LineFigureLayout.addWidget(X2LineEdit, 3, 1)
        self.LineFigureLayout.addWidget(self.X2LineEdit, 3, 2)
        self.LineFigureLayout.addWidget(Y2LineEdit, 3, 3)
        self.LineFigureLayout.addWidget(self.Y2LineEdit, 3, 4)
        self.LineFigureLayout.addWidget(XDiffLineEdit, 4, 1)
        self.LineFigureLayout.addWidget(self.XDiffLineEdit, 4, 2)
        self.LineFigureLayout.addWidget(YDiffLineEdit, 4, 3)
        self.LineFigureLayout.addWidget(self.YDiffLineEdit, 4, 4)

        self.XY1Button.toggled.connect(self.XYButton)
        self.XY2Button.toggled.connect(self.XYButton)

        self.X1LineEdit.setText(str(0.0))
        self.Y1LineEdit.setText(str(0.0))
        self.X2LineEdit.setText(str(0.0))
        self.Y2LineEdit.setText(str(0.0))
        self.XDiffLineEdit.setText(str(0.0))
        self.YDiffLineEdit.setText(str(0.0))

    def UpdateData_OneSelf(self):
        dt = time.time() - self.TimeStamp
        x_data = np.arange(-4, 4, 0.02)
        z_data = np.sin(x_data + dt)  # 准备动态数据

        h_data = np.cos(x_data + dt)

        self.LineFigure.Line.set_ydata(z_data)  # 更新数据
        # self.LineFigure.Line2.set_ydata(h_data)
        self.LineFigure.draw()  # 重新画图

    def UpdateData_UseSignal(self, New_data):
        y_data = self.Update_Data_Analyse(New_data)
        if len(y_data) > 0:
            self.LineFigure.Updata_Count = len(y_data)
            for i in range(0, self.LineFigure.Data_Num - self.LineFigure.Updata_Count):
                self.LineFigure.Update_Y_Data[i] = self.LineFigure.Update_Y_Data[i + self.LineFigure.Updata_Count]
            for j in range(0, self.LineFigure.Updata_Count):
                self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - self.LineFigure.Updata_Count + j] = y_data[j]
            if(np.max(self.LineFigure.Update_Y_Data) > self.LineFigure.YData_Max):#接收到的数据比坐标轴最大值大时更新坐标轴
                Update_X_data = np.arange(0, self.LineFigure.Data_Num, 1)
                self.LineFigure.Change_Axis_XYlim(Update_X_data, self.LineFigure.Update_Y_Data)
            self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)  # 更新数据
            self.LineFigure.draw()  # 重新画图

        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "y_data len:", len(y_data), "y:", self.LineFigure.Update_Y_Data)

        # x_data = int(time.time() - self.TimeStamp)
        # if (x_data%self.LineFigure.Updata_Count):
        #     self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - self.LineFigure.Updata_Count + x_data - 1] = New_data
        #     # print("no attend", x_data, New_data)
        # else:
        #     self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - 1] = New_data
        #     if(x_data != 0):
        #         self.TimeStamp = time.time()
        #         self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "x:", x_data, "TimeStamp:", int(self.TimeStamp),"New_data:", New_data)
        #         self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "y:", self.LineFigure.Update_Y_Data)
        #         self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)  # 更新数据
        #         self.LineFigure.draw()  # 重新画图
        #
        #         #数据往前移
        #         for i in range(0, self.LineFigure.Data_Num - self.LineFigure.Updata_Count):
        #             self.LineFigure.Update_Y_Data[i] = self.LineFigure.Update_Y_Data[i + self.LineFigure.Updata_Count]

    def PushButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "开始":
            if not System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_Start_Flag'):
                System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', True)
                self.TimeStamp = time.time()
                self.PaintWithAxisThread = Serial_Tool_PaintWithAxisThread(self.UseGlobalVal)
                self.PaintWithAxisThread.signal.connect(self.UpdateData_UseSignal)
                self.PaintWithAxisThread.start()
        if sender.text() == "停止":
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', False)

        if sender.text() == "保存":
            fname = QFileDialog.getOpenFileName(self, 'Open file', '/first.png')
            # 增加对文件格式的判断
            try:
                self.LineFigure.UseFigure.savefig(fname[0], dpi=400, bbox_inches='tight')
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "Save Picture Success")
            except Exception as e:
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level1, "Save Picture Error:", e)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', False)
            event.accept()
        else:
            event.ignore()
    #动态调整窗口大小
    def resizeEvent(self, event):
        Change_wide = event.size().width()
        Change_high = event.size().height()
        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "Change_wide:", Change_wide, ",Change_high:", Change_high)
        self.groupBox.setGeometry(QRect(self.Start_X, self.Start_Y, Change_wide - 2 * self.Start_X, Change_high - 2 * self.Start_Y))

    def Mouse_pressEvent(self, event):
        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "event.xdata", event.xdata, "event.ydata", event.ydata, "event.button", event.button)
        if event.button == MouseButton.LEFT:
            self.LineFigure.HLine[self.Sign_Select - 1].set_ydata(event.ydata)
            self.LineFigure.HLine[self.Sign_Select - 1].set_visible(True)
            if self.Sign_Select == 1:
                self.Y1LineEdit.setText(str(event.ydata))
            elif self.Sign_Select == 2:
                self.Y2LineEdit.setText(str(event.ydata))

        if event.button == MouseButton.RIGHT:
            self.LineFigure.VLine[self.Sign_Select - 1].set_xdata(event.xdata)
            self.LineFigure.VLine[self.Sign_Select - 1].set_visible(True)
            if self.Sign_Select == 1:
                self.X1LineEdit.setText(str(event.xdata))
            elif self.Sign_Select == 2:
                self.X2LineEdit.setText(str(event.xdata))

        if event.button == MouseButton.MIDDLE:
            self.LineFigure.HLine[self.Sign_Select - 1].set_visible(False)
            self.LineFigure.VLine[self.Sign_Select - 1].set_visible(False)

        if(self.X1LineEdit.text() != None and self.X2LineEdit.text() != None):
            self.XDiffLineEdit.setText(str(float(self.X2LineEdit.text()) - float(self.X1LineEdit.text())))
        if(self.Y2LineEdit.text() != None and self.Y1LineEdit.text() != None):
            self.YDiffLineEdit.setText(str(float(self.Y2LineEdit.text()) - float(self.Y1LineEdit.text())))

        self.LineFigure.draw()  # 重新画图

    def XYButton(self):
        sender = self.sender()
        if sender.text() == "XY1":
            self.Sign_Select = 1
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "XY1")

        if sender.text() == "XY2":
            self.Sign_Select = 2
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "XY2")

    def Update_Data_Analyse(self, Source_Data):
        #解析接收到的字符串数据，先按指定分隔符切片，再将切片之后的数据转换成整型
        Source_List = Source_Data.split('\r\n') #分出行数据
        for i in range(len(Source_List) - 1):
            Source_List[i] = Source_List[i].split(PaintWithAxis_UpdateData_separator)

        Result_List = [0 for i in range(len(Source_List) - 1)]
        for i in range(len(Source_List) - 1):
            Result_List[i] = [0 for j in range(len(Source_List[i]))]

        for i in range(len(Source_List) - 1):
            for j in range(len(Source_List[i])):
                try:
                    Result_List[i][j] = float(Source_List[i][j])
                except Exception as e:
                    self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level1, "str to float Error", e)
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "Source_List[", i, "][", j, "]:", Source_List[i][j], type(Source_List[i][j]), Result_List[i][j])

        if len(Source_List) < PaintWithAxis_UpdateData_Index or len(Result_List) < PaintWithAxis_UpdateData_Index:   #源数据不完整无法解析出想要的数据
            Error_List = []
            return Error_List

        return Result_List[PaintWithAxis_UpdateData_Index]

class Serial_Tool_Widget(QWidget):
    def __init__(self, Log, GlobalVal):
        super().__init__()
        self.UseLog = Log
        self.UseGlobalVal = GlobalVal
        self.initUI()

    def initUI(self):
        self.OpenPort = " "
        self.BaudRate = 0
        self.ByteSize = 8
        self.StopBits = 1
        self.Parity = None
        self.STRGLO = ""  # 读取的数据
        self.Format = True #True:十进制  False:十六进制

        self.port_list = list(serial.tools.list_ports.comports())
        self.Baud_Rate = ['110', '300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '38400', '56000', '57600',
                     '115200', '128000', '230400', '256000', '460800', '500000', '512000', '600000', '750000', '921600',
                     '1000000', '1500000', '2000000']
        self.Data_Bits = ['5', '6', '7', '8']
        self.Stop_Bits = ['1', '1.5', '2']
        self.Parity_Bits = ['None', 'Odd', 'Even', 'Mark', 'Space']
        self.PaintUpdateIndex_List = ['0', '1', '2', '3', '4']
        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level8, "list", self.port_list)

        self.Ui_SetUp()
        self.Ui_Layout()

        # self.setGeometry(300, 300, 800, 300)
        # self.setWindowTitle('Menu')
        # self.show()

    def Ui_SetUp(self):
        self.PortcomboBox = QLabel('端口号')
        self.BaudcomboBox = QLabel('波特率')
        self.DatacomboBox = QLabel('数据位')
        self.StopcomboBox = QLabel('停止位')
        self.ParitycomboBox = QLabel('奇偶校验')
        self.SendtextEdit = QLabel('数据输入框')
        self.RecvtextEdit = QLabel('数据显示框')
        self.PaintUpdateIndexcomboBox = QLabel('绘图数据下标')

        self.Sendtext_Edit = QLineEdit()#QTextEdit()
        self.Recvtext_Edit = QTextEdit()

        self.OpenButton = QPushButton('打开串口', self)
        self.CloseButton = QPushButton("关闭串口", self)
        self.SendButton = QPushButton("发送数据", self)
        self.ClearSendButton = QPushButton("清空发送框", self)
        self.ClearRecvButton = QPushButton("清空接收框", self)
        self.RefreshPortButton = QPushButton("刷新端口", self)
        self.RefreshPaintUpdateIndexButton = QPushButton("刷新绘图数据下标", self)
        self.DexButton = QRadioButton('Dex', self)
        self.HexButton = QRadioButton('Hex', self)
        self.DexButton.setChecked(True)

        self.OpenButton.clicked.connect(self.PushButtonClickedHandle)
        self.CloseButton.clicked.connect(self.PushButtonClickedHandle)
        self.SendButton.clicked.connect(self.PushButtonClickedHandle)
        self.ClearSendButton.clicked.connect(self.PushButtonClickedHandle)
        self.ClearRecvButton.clicked.connect(self.PushButtonClickedHandle)
        self.RefreshPortButton.clicked.connect(self.PushButtonClickedHandle)
        self.RefreshPaintUpdateIndexButton.clicked.connect(self.PushButtonClickedHandle)

        self.DexButton.toggled.connect(self.RadioButtonClickedHandle)
        self.HexButton.toggled.connect(self.RadioButtonClickedHandle)

        self.Port_comboBox = QComboBox(self)
        for i in range(0, len(self.port_list)):
            self.port_list[i] = str(self.port_list[i])
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level8, type(self.port_list[i]))
        self.Port_comboBox.addItems(self.port_list)

        self.Baud_comboBox = QComboBox(self)
        self.Baud_comboBox.addItems(self.Baud_Rate)
        Baud_comboBox_DefaultIndex = self.Baud_Rate.index('115200')
        self.Baud_comboBox.setCurrentIndex(Baud_comboBox_DefaultIndex)   #设置默认值

        self.Data_comboBox = QComboBox(self)
        self.Data_comboBox.addItems(self.Data_Bits)
        Data_comboBox_DefaultIndex = self.Data_Bits.index('8')
        self.Data_comboBox.setCurrentIndex(Data_comboBox_DefaultIndex)   #设置默认值

        self.Stop_comboBox = QComboBox(self)
        self.Stop_comboBox.addItems(self.Stop_Bits)

        self.Parity_comboBox = QComboBox(self)
        self.Parity_comboBox.addItems(self.Parity_Bits)

        self.PaintUpdateIndex_comboBox = QComboBox(self)
        self.PaintUpdateIndex_comboBox.addItems(self.PaintUpdateIndex_List)
        PaintUpdateIndex_comboBox_DefaultIndex = self.PaintUpdateIndex_List.index(str(PaintWithAxis_UpdateData_Index + 1))
        self.PaintUpdateIndex_comboBox.setCurrentIndex(PaintUpdateIndex_comboBox_DefaultIndex)  # 设置默认值

        self.Port_comboBox.setMinimumSize(QSize(100, 20))
        self.Baud_comboBox.setMinimumSize(QSize(100, 20))
        self.Data_comboBox.setMinimumSize(QSize(100, 20))
        self.Stop_comboBox.setMinimumSize(QSize(100, 20))
        self.Parity_comboBox.setMinimumSize(QSize(100, 20))
        self.PaintUpdateIndex_comboBox.setMinimumSize(QSize(100, 20))

    def Ui_Layout(self):
        grid = QGridLayout()
        grid.setSpacing(20)

        X_Index = 1;
        Y_Index = 0
        X_BoxStep = 1;
        Y_BoxStep = 1
        X_TextStep = 1;
        Y_TextStep = Y_BoxStep + 1;
        X_TextSize = 2;
        Y_TextSize = 3;
        X_LineSize = 1
        X_ButtonStep = 1;
        Y_ButtonStep = Y_TextStep + Y_TextSize + 1

        grid.addWidget(self.PortcomboBox, X_Index, Y_Index)
        grid.addWidget(self.Port_comboBox, X_Index, Y_Index + Y_BoxStep)
        grid.addWidget(self.BaudcomboBox, X_Index + X_BoxStep, Y_Index)
        grid.addWidget(self.Baud_comboBox, X_Index + X_BoxStep, Y_Index + Y_BoxStep)
        grid.addWidget(self.DatacomboBox, X_Index + 2 * X_BoxStep, Y_Index)
        grid.addWidget(self.Data_comboBox, X_Index + 2 * X_BoxStep, Y_Index + Y_BoxStep)
        grid.addWidget(self.StopcomboBox, X_Index + 3 * X_BoxStep, Y_Index)
        grid.addWidget(self.Stop_comboBox, X_Index + 3 * X_BoxStep, Y_Index + Y_BoxStep)
        grid.addWidget(self.ParitycomboBox, X_Index + 4 * X_BoxStep, Y_Index)
        grid.addWidget(self.Parity_comboBox, X_Index + 4 * X_BoxStep, Y_Index + Y_BoxStep)
        grid.addWidget(self.PaintUpdateIndexcomboBox, X_Index + 5 * X_BoxStep, Y_Index)
        grid.addWidget(self.PaintUpdateIndex_comboBox, X_Index + 5 * X_BoxStep, Y_Index + Y_BoxStep)

        grid.addWidget(self.DexButton, X_Index, Y_Index + Y_TextStep)
        grid.addWidget(self.HexButton, X_Index, Y_Index + 2 * Y_TextStep)
        grid.addWidget(self.Sendtext_Edit, X_Index + X_TextStep, Y_Index + Y_TextStep, X_LineSize, Y_TextSize)
        grid.addWidget(self.Recvtext_Edit, X_Index + 2 * X_TextStep, Y_Index + Y_TextStep, 2 * X_TextSize, Y_TextSize)

        grid.addWidget(self.SendtextEdit, X_Index + X_TextStep, Y_Index + Y_TextStep + Y_TextSize)
        grid.addWidget(self.RecvtextEdit, X_Index + 2 * X_TextStep, Y_Index + Y_TextStep + Y_TextSize)

        grid.addWidget(self.OpenButton, X_Index, Y_Index + Y_ButtonStep)
        grid.addWidget(self.CloseButton, X_Index + X_ButtonStep, Y_Index + Y_ButtonStep)
        grid.addWidget(self.SendButton, X_Index + 2 * X_ButtonStep, Y_Index + Y_ButtonStep)
        grid.addWidget(self.ClearSendButton, X_Index + 3 * X_ButtonStep, Y_Index + Y_ButtonStep)
        grid.addWidget(self.ClearRecvButton, X_Index + 4 * X_ButtonStep, Y_Index + Y_ButtonStep)
        grid.addWidget(self.RefreshPortButton, X_Index + 5 * X_ButtonStep, Y_Index + Y_ButtonStep)
        grid.addWidget(self.RefreshPaintUpdateIndexButton, X_Index + 6 * X_ButtonStep, Y_Index + Y_ButtonStep)

        self.setLayout(grid)

    def PushButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "打开串口":
            self.OpenPort = self.GetOpenPort(self.Port_comboBox.currentText())
            if len(self.Baud_comboBox.currentText()):
                self.BaudRate = int(self.Baud_comboBox.currentText())
            if len(self.Data_comboBox.currentText()):
                self.ByteSize = int(self.Data_comboBox.currentText())
            if len(self.Stop_comboBox.currentText()):
                self.StopBits = float(self.Stop_comboBox.currentText())
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level5, len(self.OpenPort), self.BaudRate, self.ByteSize, self.StopBits)
            if (len(self.OpenPort) != 0 or self.BaudRate != 0):
                self.Serial = SerialToolSer.Serial_Tool_Ser(self.OpenPort, self.BaudRate, self.ByteSize, self.StopBits, self.Parity, None, self.UseLog, self.UseGlobalVal)
                if (self.Serial.Open_Ret == True):  # 判断串口是否成功打开
                    try:
                        self.OpenButton.setEnabled(False)
                        self.Serial.SerThread.Signal.connect(self.ShowRecvData)
                        self.Serial.SerThread.start()
                        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' ' + self.OpenPort + ' Successful')
                    except Exception as e:
                        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level1, "打开串口异常:", e)
                else:
                    self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' Fail')
            else:
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, ' Please Select Port')

        if sender.text() == "关闭串口":
            self.OpenButton.setEnabled(True)
            if (self.Serial.Open_Ret == True):
                self.Serial.SerialColsePort()
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' Successful')

        if sender.text() == "发送数据":
            if (self.Serial.Open_Ret == True):
                if(self.Format):
                    self.Serial.SerialWritePort(self.Sendtext_Edit.text())
                    self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level5, "Dex 写入字节数：", self.Serial.Send_Count)
                    self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + self.Sendtext_Edit.text())
                else:
                    self.Serial.SerialWritePort(self.Sendtext_Edit.text().encode('utf-8').hex())
                    self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level5, "Hex 写入字节数：", self.Serial.Send_Count)
                    self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + self.Sendtext_Edit.text().encode('utf-8').hex())
            else:
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' ERROR')

        if sender.text() == "清空发送框":
            self.Sendtext_Edit.clear()

        if sender.text() == "清空接收框":
            self.Recvtext_Edit.clear()

        if sender.text() == "刷新端口":
            self.port_list = list(serial.tools.list_ports.comports())
            for i in range(0, len(self.port_list)):
                self.port_list[i] = str(self.port_list[i])
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, type(self.port_list[i]))
            self.Port_comboBox.clear()
            self.Port_comboBox.addItems(self.port_list)

        if sender.text() == "刷新绘图数据下标":
            global PaintWithAxis_UpdateData_Index
            Index = int(self.PaintUpdateIndex_comboBox.currentText())
            if Index != 0:
                PaintWithAxis_UpdateData_Index = Index - 1
            else:
                PaintWithAxis_UpdateData_Index = 0
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "绘图下标更新为：", PaintWithAxis_UpdateData_Index)

    def RadioButtonClickedHandle(self):
        sender = self.sender()
        if sender.text() == "Dex":
            self.Format = True
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "Dex")

        if sender.text() == "Hex":
            self.Format = False
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level6, "Hex")

    # 选定串口
    def GetOpenPort(self, port_str):
        if len(port_str):
            Front_index = port_str.find('(')
            Rear_index = port_str.find(')')
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, len(port_str), Front_index, Rear_index)
            return port_str[Front_index+1:Rear_index]
        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "Get Serial Port NUll")
        return ''

    def ShowRecvData(self, RecvData):
        self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3, "ShowRecvData:", RecvData,"len:", len(RecvData))
        if(len(RecvData)):
            try:
                self.Recvtext_Edit.append(RecvData)
            except Exception as e:
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level1, "ShowRecvData  Recvtext_Edit append Error:", e)

class Serial_Tool_MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.UseLog = System.Serial_Tool_Log()
        self.UseGlobalVal = System.Serial_Tool_GlobalManager()  # 初始化参数
        self.Serial_Tool_MainUI_Init()

    def Serial_Tool_MainUI_Init(self):
        self.UseWidget = Serial_Tool_Widget(self.UseLog, self.UseGlobalVal)
        self.setCentralWidget(self.UseWidget)
        # self.MyDraw = Serial_Tool_Paint()#Serial_Tool_Draw()
        #创建状态栏的小窗口
        self.statusBar().showMessage('Ready')

        self.Open_file_menu = QAction(QIcon('./Logo_Picture/Open.png'), "打开", self)
        self.Open_file_menu.setShortcut('Ctrl+' + 'O')
        self.Open_file_menu.setStatusTip('Open File')
        self.Open_file_menu.triggered.connect(self.ReloadDialog)
        self.Save_file_menu = QAction(QIcon('./Logo_Picture/Save.jpeg'), "保存", self)
        self.Save_file_menu.setShortcut('Ctrl+' + 'S')
        self.Save_file_menu.setStatusTip('Save File')
        self.Save_file_menu.triggered.connect(self.SaveDialog)
        # 创建一个菜单栏
        filemenubar = self.menuBar()
        # 添加菜单
        FileMenu = filemenubar.addMenu('&文件')
        # 添加事件
        FileMenu.addAction(self.Open_file_menu)
        FileMenu.addAction(self.Save_file_menu)

        self.Start_Draw_menu = QAction(QIcon('./Logo_Picture/Save.jpeg'), "启动绘图", self)
        self.Start_Draw_menu.setShortcut('Ctrl+' + 'T')
        self.Start_Draw_menu.setStatusTip('Start Draw')
        self.Start_Draw_menu.triggered.connect(self.Start_Draw)
        # 创建一个菜单栏
        Drawmenubar = self.menuBar()
        DrawMenu = Drawmenubar.addMenu('&画图')
        DrawMenu.addAction(self.Start_Draw_menu)

        self.Serial_Tool_LogMenu_Init()

        self.setGeometry(300, 300, 800, 300)
        self.setWindowTitle('Serial_Tool')
        self.setWindowIcon(QIcon('./Logo_Picture/SerialToolMainUI.jpeg'))
        self.show()

    def Serial_Tool_LogMenu_Init(self):
        #日志输出类型UI选项
        self.LogTypeList = []

        Log_type = QAction("日志输出类型1", self, checkable=True)
        Log_type.setStatusTip('Use Print Output')
        Log_type.setChecked(True)
        Log_type.triggered.connect(self.Tool_LogOption)
        self.LogTypeList.append(Log_type)
        Log_type = QAction("日志输出类型2", self, checkable=True)
        Log_type.setStatusTip('Use File Output')
        Log_type.setChecked(False)
        Log_type.triggered.connect(self.Tool_LogOption)
        self.LogTypeList.append(Log_type)

        Log_type_menu = QMenu('日志输出类型', self)
        for i in range(len(self.LogTypeList)):
            Log_type_menu.addAction(self.LogTypeList[i])

        # 日志输出模块UI选项
        self.LogModuleList = []

        Log_Sysmodule = QAction("系统日志模块", self, checkable=True)
        Log_Sysmodule.setStatusTip('系统日志模块')
        Log_Sysmodule.setChecked(False)
        Log_Sysmodule.triggered.connect(self.Tool_LogOption)
        self.LogModuleList.append(Log_Sysmodule)
        Log_Uimodule = QAction("UI日志模块", self, checkable=True)
        Log_Uimodule.setStatusTip('UI日志模块')
        Log_Uimodule.setChecked(False)
        Log_Uimodule.triggered.connect(self.Tool_LogOption)
        self.LogModuleList.append(Log_Uimodule)
        Log_Sermodule = QAction("串口日志模块", self, checkable=True)
        Log_Sermodule.setStatusTip('串口日志模块')
        Log_Sermodule.setChecked(False)
        Log_Sermodule.triggered.connect(self.Tool_LogOption)
        self.LogModuleList.append(Log_Sermodule)

        Log_Modue_menu = QMenu('日志模块选项', self)
        for i in range(len(self.LogModuleList)):
            Log_Modue_menu.addAction(self.LogModuleList[i])

        # 日志输出等级UI选项
        self.LogLevelList = []

        for i in range(int(str(LogLevel.LogLevelMax.value))):
            Log_level = QAction("日志输出等级"+str(i+1), self, checkable=True)
            Log_level.setStatusTip('日志输出等级'+str(i+1))
            Log_level.setChecked(False)
            Log_level.triggered.connect(self.Tool_LogOption)
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

    def ReloadDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            f = open(fname[0], 'r', encoding = 'utf-8')
            with f:
                data = f.read()
                self.UseWidget.Recvtext_Edit.setText(data)

    def SaveDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        try:
            if fname[0]:
                self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level5, fname[0])
                f = open(fname[0], 'w', encoding = 'utf-8')
                with f:
                    f.write(self.UseWidget.Recvtext_Edit.toPlainText())
                f.close()
        except Exception as e:
            print("write file Error:", e)

    def Start_Draw(self):
        try:
            self.UseDraw = Serial_Tool_PaintWithAxisUi(self.UseLog,  self.UseGlobalVal) #Serial_Tool_Paint()
            self.UseDraw.setWindowIcon(QIcon('./Logo_Picture/PaintUI.jpeg'))
            self.UseDraw.show()
        except Exception as e:
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level1, "Draw New Paint Error:", e)

    def Tool_LogOption(self):
        sender = self.sender()
        try:

            for i in range(len(self.LogTypeList)):  # 日志输出类型选项只选其一
                if sender.text() == self.LogTypeList[i].text():
                    self.UseLog.Change_Type(LogType(i+1))
                    self.LogTypeList[i].setChecked(True)
                    for r in range(len(self.LogTypeList)):
                        if r != i:  # 将未选中的选项取消
                            self.LogTypeList[r].setChecked(False)
                            # print("LogTypeList", i, sender.text(), r)

            for j in range(len(self.LogModuleList)):  # 日志输出模块选项可多选
                if sender.text() == self.LogModuleList[j].text():
                    self.UseLog.Change_Module((j + 1), self.LogModuleList[j].isChecked())
                    self.LogModuleList[j].setChecked(self.LogModuleList[j].isChecked())
                    # print("LogModuleList", j, sender.text(), self.LogModuleList[j].isChecked())

            for k in range(len(self.LogLevelList)):  # 日志等级选项只选其一
                if sender.text() == self.LogLevelList[k].text():
                    self.UseLog.Change_Level(k + 1)
                    self.LogLevelList[k].setChecked(True)
                    for r in range(len(self.LogLevelList)):
                        if r != k:  # 将未选中的选项取消
                            self.LogLevelList[r].setChecked(False)
                            # print("LogLevelList", k, sender.text(), r)

        except Exception as e:
            print("log option error:", e)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.UseLog.Log_Close()
            event.accept()
        else:
            event.ignore()
