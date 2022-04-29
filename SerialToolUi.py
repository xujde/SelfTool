import time, threading, random
from PyQt5.QtWidgets import (QWidget, QPushButton, QMainWindow, QAction, QTextEdit, QLineEdit,
                             QGridLayout, QFileDialog, QLabel, QRadioButton, QMenu, QGroupBox, QScrollBar, QAbstractSlider,
                             QListWidget, QCheckBox, QListWidgetItem, QDesktopWidget, QComboBox, QMessageBox, QProgressBar)
from PyQt5.QtGui import QIcon, QPainter, QFont, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import Qt, QSize, QRect, QTimer, pyqtSignal, QThread, QPoint, QMetaObject, QCoreApplication
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backend_bases import MouseButton
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.widgets import Cursor
import serial.tools.list_ports
import numpy as np

import System
import SerialToolSer
from System import LogModule
from System import LogLevel
from System import LogType
from SerialToolSer import SerialWriteType

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决坐标轴中文显示问题
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号不显示的问题

PaintWithAxis_CacheData_Length = 10000 # 缓存绘图数据数量
PaintWithAxis_SlideShowData_Step = 10 # 滚动条移动一步，更新绘图数据个数
PaintWithAxis_ShowData_Length = 200 #默认显示绘图数据点个数,需要大于串口解析出的数据个数
PaintWithAxis_UpdateData_separator = ','
PaintWithAxis_UpdateData_Index = 1
PaintWithAxis_Zooom_Range = 2 #坐标轴刻度缩放幅度
PaintWithAxis_Display_The_Latest_Data = True #是否显示最新数据
PaintWithAxis_Setlim_Flag = False    #设置坐标轴范围限制标志,需要互斥

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
        self.ShowDataNum = PaintWithAxis_ShowData_Length     # X轴最大值,要大于1（即X轴长度）
        self.CacheDataNum = PaintWithAxis_CacheData_Length
        self.YData_Max = 120    # Y轴最大值
        self.Updata_Count = 0  # 累计更新Updata_Count个数据后更新绘图，必须小于self.ShowDataNum
        self.Sign_Num = 2
        self.HLine = [self.Axis.axhline(0, visible=True) for i in range(self.Sign_Num)]#平行于X轴
        self.VLine = [self.Axis.axvline(0, visible=True) for i in range(self.Sign_Num)]#平行于Y轴
        self.Update_X_Data = np.arange((self.CacheDataNum - self.ShowDataNum), self.CacheDataNum)
        self.Update_Y_Data = [0] * self.ShowDataNum
        self.Cache_Y_Data = [0] * self.CacheDataNum
        self.UseCursor = Cursor(self.Axis, useblit=True, color='Yellow', linewidth=2)

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
        self.XData_Max = np.max(x_data)
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
        # self.Axis2 = self.Axis.twinx()
        # self.Axis2.set_ylim(np.min(y_data), np.max(y_data) + 2)
        # self.Axis2.set_ylabel('y2坐标')

    def Change_Axis_XYlim(self, X_Data, Y_Data):
        self.Axis.set_xlim(np.min(X_Data), np.max(X_Data), auto=True)
        self.Axis.set_ylim(np.min(Y_Data), np.max(Y_Data), auto=True)  # y轴稍微多一点，会好看一点

        self.XData_Max = np.max(X_Data)
        self.YData_Max = np.max(Y_Data)

        # self.Axis2 = self.Axis.twinx()
        # self.Axis2.set_ylim(np.min(Y_Data), np.max(Y_Data))
        # self.Axis2.set_ylabel('y2坐标')

    def Change_Axis_Xlim(self, X_Data):
        self.Axis.set_xlim(np.min(X_Data), np.max(X_Data), auto=True)
        self.XData_Max = np.max(X_Data)

class Serial_Tool_PaintWithAxisUi(QMainWindow):
    def __init__(self, Log, GlobalVal):
        super(Serial_Tool_PaintWithAxisUi, self).__init__()
        self.UseLog = Log
        self.UseGlobalVal = GlobalVal
        self.Sign_Select = 1

        global PaintWithAxis_Display_The_Latest_Data
        PaintWithAxis_Display_The_Latest_Data = True

        self.setWindowTitle('绘制动态曲线')
        Wide = 1000;High = 800
        self.Start_X = 10;self.Start_Y = 10
        self.resize(Wide, High)
        self.HorizontalScrollBarValue = 0
        self.VerticalScrollBarValue = 0

        # 创建一个groupbox, 用来画动态曲线
        self.groupBox = QGroupBox(self)
        self.groupBox.setGeometry(QRect(self.Start_X, self.Start_Y, Wide - 2*self.Start_X, High - 2*self.Start_Y))

        self.LineFigureLayout = QGridLayout(self.groupBox)

        self.Button_Setup()
        self.LineEdit_Setup()
        self.ScrollBar_Setup()
        self.Ui_Layout()

        self.Load_DynamicLine()  # 加载动态曲线

        self.setLayout(self.LineFigureLayout)

        System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', True)
        self.TimeStamp = time.time()
        self.PaintWithAxisThread = Serial_Tool_PaintWithAxisThread(self.UseGlobalVal)
        self.PaintWithAxisThread.signal.connect(self.UpdateData_UseSignal)
        self.PaintWithAxisThread.start()

    def Load_DynamicLine(self):
        self.LineFigure = Serial_Tool_PaintWithAxis()

        self.LineFigure.UseFigure.canvas.mpl_connect('button_press_event', self.Mouse_PressEvent)  # 鼠标点击事件处理
        self.LineFigure.UseFigure.canvas.mpl_connect('scroll_event', self.Mouse_ScrollEvent)  # 鼠标滚轮事件处理
        self.LineFigure.UseCursor.canvas.mpl_connect('motion_notify_event', self.Mouse_MoveEvent)   #鼠标移动事件处理

        self.LineFigureLayout.addWidget(self.LineFigure, 0, 0, 1, 5)

        x_data = np.arange(PaintWithAxis_CacheData_Length -  PaintWithAxis_ShowData_Length, PaintWithAxis_CacheData_Length, 1)#np.arange(0, PaintWithAxis_ShowData_Length, 1)
        y_data = [self.LineFigure.YData_Max for i in range(PaintWithAxis_ShowData_Length)]
        for i in range(1, PaintWithAxis_ShowData_Length):
            y_data[i] = random.randint(1, self.LineFigure.YData_Max)

        if(self.LineFigure.Updata_Count > PaintWithAxis_ShowData_Length):
            self.LineFigure.Updata_Count = PaintWithAxis_ShowData_Length
        elif (self.LineFigure.Updata_Count < 1):
            self.LineFigure.Updata_Count = 1

        self.LineFigure.Add_Line(x_data, y_data)

    def Button_Setup(self):
        self.StartButton = QPushButton('开始', self)
        self.StopButton = QPushButton("停止", self)
        self.SaveButton = QPushButton("保存", self)
        self.StartButton.clicked.connect(self.PushButtonClickedHandle)
        self.StopButton.clicked.connect(self.PushButtonClickedHandle)
        self.SaveButton.clicked.connect(self.PushButtonClickedHandle)

    def LineEdit_Setup(self):
        self.X1LineEdit = QLabel('X1')
        self.Y1LineEdit = QLabel('Y1')
        self.X2LineEdit = QLabel('X2')
        self.Y2LineEdit = QLabel('Y2')
        self.XDiffLineEdit = QLabel('X-Diff')
        self.YDiffLineEdit = QLabel('Y-Diff')
        self.MouseMoveMarkLabel = QLabel('X:None - Y:None')

        self.X1_LineEdit = QLineEdit()
        self.Y1_LineEdit = QLineEdit()
        self.X2_LineEdit = QLineEdit()
        self.Y2_LineEdit = QLineEdit()
        self.XDiff_LineEdit = QLineEdit()
        self.YDiff_LineEdit = QLineEdit()

        self.XY1Button = QRadioButton('XY1', self)
        self.XY2Button = QRadioButton('XY2', self)
        self.XY1Button.setChecked(True)

        self.XY1Button.toggled.connect(self.XYButton)
        self.XY2Button.toggled.connect(self.XYButton)

        self.X1_LineEdit.setText(str(0.0))
        self.Y1_LineEdit.setText(str(0.0))
        self.X2_LineEdit.setText(str(0.0))
        self.Y2_LineEdit.setText(str(0.0))
        self.XDiff_LineEdit.setText(str(0.0))
        self.YDiff_LineEdit.setText(str(0.0))

    def ScrollBar_Setup(self):
        self.HorizontalScrollBar = QScrollBar(orientation=True, maximum = PaintWithAxis_CacheData_Length/PaintWithAxis_SlideShowData_Step)#, pagestep = 10, singlestep = 5, value = 0)
        self.HorizontalScrollBar.actionTriggered.connect(self.ScrollBarSliderMovedHandle)
        # self.HorizontalScrollBar.sliderMoved.connect(self.ScrollBarSliderMovedHandle)
        self.HorizontalScrollBar.setValue(PaintWithAxis_CacheData_Length/PaintWithAxis_SlideShowData_Step)
        self.VerticalScrollBar = QScrollBar(maximum = 0)
        self.VerticalScrollBar.actionTriggered.connect(self.ScrollBarSliderMovedHandle)
        self.HorizontalScrollBarValue = self.HorizontalScrollBar.value()
        self.VerticalScrollBarValue = self.VerticalScrollBar.value()

    def Ui_Layout(self):
        self.LineFigureLayout.addWidget(self.StartButton, 1, 0)
        self.LineFigureLayout.addWidget(self.StopButton, 1, 1)
        self.LineFigureLayout.addWidget(self.MouseMoveMarkLabel, 1, 2)
        self.LineFigureLayout.addWidget(self.SaveButton, 1, 3)

        self.LineFigureLayout.addWidget(self.HorizontalScrollBar, 1, 4)
        self.LineFigureLayout.addWidget(self.VerticalScrollBar, 0, 6)  # 坐标轴从(0,0)开始，长度为5

        self.LineFigureLayout.addWidget(self.XY1Button, 2, 0)
        self.LineFigureLayout.addWidget(self.X1LineEdit, 2, 1)
        self.LineFigureLayout.addWidget(self.X1_LineEdit, 2, 2)
        self.LineFigureLayout.addWidget(self.Y1LineEdit, 2, 3)
        self.LineFigureLayout.addWidget(self.Y1_LineEdit, 2, 4)
        self.LineFigureLayout.addWidget(self.XY2Button, 3, 0)
        self.LineFigureLayout.addWidget(self.X2LineEdit, 3, 1)
        self.LineFigureLayout.addWidget(self.X2_LineEdit, 3, 2)
        self.LineFigureLayout.addWidget(self.Y2LineEdit, 3, 3)
        self.LineFigureLayout.addWidget(self.Y2_LineEdit, 3, 4)
        self.LineFigureLayout.addWidget(self.XDiffLineEdit, 4, 1)
        self.LineFigureLayout.addWidget(self.XDiff_LineEdit, 4, 2)
        self.LineFigureLayout.addWidget(self.YDiffLineEdit, 4, 3)
        self.LineFigureLayout.addWidget(self.YDiff_LineEdit, 4, 4)

    def UpdateData_UseSignal(self, New_data):
        global PaintWithAxis_Setlim_Flag

        while PaintWithAxis_Setlim_Flag:
            time.sleep(1)

        PaintWithAxis_Setlim_Flag = True
        OutListRangeFlag = 0 #测试验证使用稳定后删除！！！

        x_min, x_max = self.LineFigure.Axis.get_xlim()
        Update_Mark_Line_XMove = 0

        y_data = self.Update_Data_Analyse(New_data)
        try:
            if len(y_data) > 0:
                self.LineFigure.Updata_Count = len(y_data)
                if self.LineFigure.Updata_Count > PaintWithAxis_ShowData_Length:
                    self.LineFigure.Updata_Count = PaintWithAxis_ShowData_Length
                # 更新缓存数据
                for i in range(0, PaintWithAxis_CacheData_Length - self.LineFigure.Updata_Count):
                    self.LineFigure.Cache_Y_Data[i] = self.LineFigure.Cache_Y_Data[i + self.LineFigure.Updata_Count]
                    OutListRangeFlag = 1
                for j in range(0, self.LineFigure.Updata_Count):
                    self.LineFigure.Cache_Y_Data[PaintWithAxis_CacheData_Length - self.LineFigure.Updata_Count + j] = y_data[j]
                    OutListRangeFlag = 2

                if PaintWithAxis_Display_The_Latest_Data:   #更新显示最新数据
                    self.LineFigure.Update_Y_Data = [0 for i in range(PaintWithAxis_ShowData_Length)]
                    OutListRangeFlag = 3
                    for k in range(0, PaintWithAxis_ShowData_Length):
                            self.LineFigure.Update_Y_Data[k] = self.LineFigure.Cache_Y_Data[PaintWithAxis_CacheData_Length - PaintWithAxis_ShowData_Length + k]
                            OutListRangeFlag = 4
                    if (np.max(self.LineFigure.Update_Y_Data) > self.LineFigure.YData_Max):  # 接收到的数据比坐标轴最大值大时更新坐标轴
                        self.LineFigure.Update_X_Data = np.arange(PaintWithAxis_CacheData_Length - PaintWithAxis_ShowData_Length, PaintWithAxis_CacheData_Length, 1)
                        self.LineFigure.Change_Axis_XYlim(self.LineFigure.Update_X_Data, self.LineFigure.Update_Y_Data)
                    self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)
                    Update_Mark_Line_XMove = self.LineFigure.Updata_Count*-1    #数据增加，整体曲线往前移
                    OutListRangeFlag = 5
                else: #不显示最新数据，但更新X轴坐标范围
                    diff = 0; w = 0; n = 0; m = 0; v = 0; p = 0
                    x_change_min = 0;x_change_max = 0
                    #增加调整坐标轴范围之后范围限制
                    if x_min - self.LineFigure.Updata_Count < 0:
                        x_range = x_max - x_min + 1 #此处需要＋1，否则调整的X轴范围会越来越小
                        x_change_min = 0
                        x_change_max = x_range
                    else:
                        x_change_min = x_min - self.LineFigure.Updata_Count
                        x_change_max = x_max - self.LineFigure.Updata_Count + 1  #此处需要＋1，否则调整的X轴范围会越来越小
                    if (x_max - x_min) != (x_change_max - x_change_min):
                        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "UpdateData_UseSignal != x_min:", x_min, "x_max:", x_max, "x_change_min:", x_change_min, "x_change_max:", x_change_max)
                    self.LineFigure.Update_X_Data = np.arange(int(x_change_min), int(x_change_max))
                    self.LineFigure.Change_Axis_Xlim(self.LineFigure.Update_X_Data) #只更新X轴坐标范围
                    self.LineFigure.Line.set_xdata(self.LineFigure.Update_X_Data)
                    OutListRangeFlag = 6
                    #将历史显示值先记录下来
                    Update_Y_Data = [0 for p in range(len(self.LineFigure.Update_Y_Data))]
                    for p in range(len(self.LineFigure.Update_Y_Data)):
                        Update_Y_Data[p] = self.LineFigure.Update_Y_Data[p]
                        OutListRangeFlag = 7
                    # Y轴数据需要匹配X轴长度
                    if len(self.LineFigure.Update_X_Data) > len(self.LineFigure.Update_Y_Data):
                        diff = len(self.LineFigure.Update_X_Data) - len(self.LineFigure.Update_Y_Data)
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "UpdateData_UseSignal diff:", diff, "self.LineFigure.Update_X_Data len:", len(self.LineFigure.Update_X_Data), "self.LineFigure.Update_Y_Data len:", len(self.LineFigure.Update_Y_Data))

                    self.LineFigure.Update_Y_Data = [0 for p in range(len(self.LineFigure.Update_X_Data))]  #更新列表长度

                    if diff > 0:
                        for n in range(len(self.LineFigure.Cache_Y_Data)): #前面的值从self.LineFigure.Cache_Y_Data往前找历史值
                            if Update_Y_Data[0] == self.LineFigure.Cache_Y_Data[n]:
                                for w in range(len(Update_Y_Data)):
                                    if Update_Y_Data[w] != self.LineFigure.Cache_Y_Data[n + w]:
                                        break #不连续相同，继续查找
                                if w == (len(Update_Y_Data) - 1):
                                    for v in range(diff):
                                        self.LineFigure.Update_Y_Data[v] = self.LineFigure.Cache_Y_Data[n - diff + v]
                                        OutListRangeFlag = 8
                                    break #找到连续相同，并获取到历史值，退出查找
                        #很久之前的数据已经从缓存中删除
                        if w == 0 and v == 0:
                            for v in range(len(self.LineFigure.Update_Y_Data)):
                                self.LineFigure.Update_Y_Data[v] = self.LineFigure.Cache_Y_Data[v]
                                OutListRangeFlag = 9
                            m = len(Update_Y_Data)
                    else:
                        for n in range(len(self.LineFigure.Cache_Y_Data)): #前面的值从self.LineFigure.Cache_Y_Data往前找历史值
                            if Update_Y_Data[0] == self.LineFigure.Cache_Y_Data[n]:
                                for w in range(len(Update_Y_Data)):
                                    if Update_Y_Data[w] != self.LineFigure.Cache_Y_Data[n + w]:
                                        break #不连续相同，继续查找
                            if w == (len(Update_Y_Data) - 1):
                                break #已经找到连续相同，退出查找
                        if w != (len(Update_Y_Data) - 1):   #累计更新数据数量超过Cache_Y_Data长度，取Cache_Y_Data最早的值
                            for v in range(len(self.LineFigure.Update_Y_Data)):
                                self.LineFigure.Update_Y_Data[v] = self.LineFigure.Cache_Y_Data[v]
                                OutListRangeFlag = 11
                            m = len(Update_Y_Data)

                    while(m < len(Update_Y_Data)): #for m in range(len(Update_Y_Data)): 使用此for语句，m是从0开始计数
                        if m < len(self.LineFigure.Update_Y_Data):  #需要self.LineFigure.Update_X_Data和self.LineFigure.Update_Y_Data的长度小于Update_Y_Data的情况
                            self.LineFigure.Update_Y_Data[diff + m] = Update_Y_Data[m]
                            OutListRangeFlag = 10
                        m = m + 1


                    if (x_change_max - 1) == x_max:   #判断X坐标轴的变化，确定标记线移动方向和长度
                        if x_change_min != x_min:
                            Update_Mark_Line_XMove = x_change_min - x_min
                        else:
                            Update_Mark_Line_XMove = self.LineFigure.Updata_Count*-1
                    else:
                        Update_Mark_Line_XMove = x_change_max - x_max - 1 #此处不-1标记线移动的长度会比更新的数据长度小1

                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "n:", n, "m:", m, "v:", v, "w:", w, "p:", p, "diff", diff)
                    self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)


                    self.HorizontalScrollBar.setValue(int(x_change_max) / PaintWithAxis_SlideShowData_Step) #设置滚动条的值
                    self.HorizontalScrollBarValue = self.HorizontalScrollBar.value()
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "UpdateData_UseSignal x_min:", x_min, " x_max:", x_max)

                self.Update_Mark_Line(Update_Mark_Line_XMove)

                self.LineFigure.draw()  # 重新画图
        except Exception as e:
            self.UseLog.ErrorLog_Output("UpdateData_UseSignal Error:", e, "flag:", OutListRangeFlag)
            pass
        PaintWithAxis_Setlim_Flag = False

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
            fname = QFileDialog.getSaveFileName(self, 'Open file', '/*.png')
            # 增加对文件格式的判断
            try:
                self.LineFigure.UseFigure.savefig(fname[0], dpi=400, bbox_inches='tight')
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Save Picture Success")
            except Exception as e:
                self.UseLog.ErrorLog_Output("Save Picture Error:", e)

    def ScrollBarSliderMovedHandle(self):
        global PaintWithAxis_Setlim_Flag
        while PaintWithAxis_Setlim_Flag:
            time.sleep(1)
        PaintWithAxis_Setlim_Flag = True
        try:
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "ScrollBarSliderMovedHandle H:", self.HorizontalScrollBar.value(), "V:", self.VerticalScrollBar.value())

            global PaintWithAxis_Display_The_Latest_Data

            # 获取当前坐标轴范围
            x_min, x_max = self.LineFigure.Axis.get_xlim()
            y_min, y_max = self.LineFigure.Axis.get_ylim()

            if self.HorizontalScrollBarValue != self.HorizontalScrollBar.value():
                if x_min >= 0:
                    X_Range = x_max - x_min + 1 #此处需要＋1，否则调整的X轴范围会越来越小
                    StartHorIndex = int(x_min)
                else :
                    X_Range = x_max + 1
                    StartHorIndex = 0
                HorValueChange = self.HorizontalScrollBar.value() - self.HorizontalScrollBarValue #滚动条变化量
                StartHorIndex = StartHorIndex + (HorValueChange * PaintWithAxis_SlideShowData_Step)

                if StartHorIndex < 0:
                    StartHorIndex = 0
                if PaintWithAxis_CacheData_Length < int(StartHorIndex + X_Range):
                    StartHorIndex = PaintWithAxis_CacheData_Length - int(X_Range)

                self.LineFigure.Update_Y_Data = [0 for j in range(int(X_Range))]
                try:
                    for i in range(0, int(X_Range)): #获取当前坐标范围内数据
                        self.LineFigure.Update_Y_Data[i] = self.LineFigure.Cache_Y_Data[int(StartHorIndex) + i]
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "ScrollBarSliderMovedHandle StartHorIndex:", StartHorIndex, "x_min x_max:", x_min, x_max, "X_Range:", X_Range)
                except Exception as e:
                    self.UseLog.ErrorLog_Output("ScrollBarSliderMovedHandle Error StartHorIndex:", StartHorIndex, "X_Range:", X_Range, "i:", i, len(self.LineFigure.Update_Y_Data), len(self.LineFigure.Cache_Y_Data),"Error:", e)

                self.LineFigure.Update_X_Data = np.arange(int(StartHorIndex), int(StartHorIndex + X_Range))
                if np.max(self.LineFigure.Update_X_Data) == np.min(self.LineFigure.Update_X_Data):
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "== StartHorIndex:", StartHorIndex, "X_Range:", X_Range, "x_min x_max:", x_min, x_max)
                    return
                elif X_Range != (x_max - x_min + 1):
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "!= StartHorIndex:", StartHorIndex, "X_Range:", X_Range, "x_min x_max:", x_min, x_max)

                if len(self.LineFigure.Update_X_Data) == len(self.LineFigure.Update_Y_Data):
                    self.LineFigure.Change_Axis_Xlim(self.LineFigure.Update_X_Data) #更新X轴坐标
                    self.LineFigure.Line.set_xdata(self.LineFigure.Update_X_Data) #更新折线X轴数据，否则会出现未绘制过的X轴部分出现Y轴数据缺失显示
                    self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data) #更新折线Y轴数据,长度需要跟X轴数据一致，否则会出现“shape mismatch: objects cannot be broadcast to a single shape”错误

                self.HorizontalScrollBarValue = self.HorizontalScrollBar.value()

                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "ScrollBarSliderMovedHandle Update_Data len:", len(self.LineFigure.Update_X_Data), len(self.LineFigure.Update_Y_Data))
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level8, "ScrollBarSliderMovedHandle Cache_Y_Data:", self.LineFigure.Cache_Y_Data)
            elif self.VerticalScrollBarValue != self.VerticalScrollBar.value() :
                #改变Y轴的坐标轴范围
                Y_Change_min = y_min + (self.VerticalScrollBarValue - self.VerticalScrollBar.value())
                Y_Change_Max = y_max + (self.VerticalScrollBarValue - self.VerticalScrollBar.value())
                self.LineFigure.Axis.set_ylim(Y_Change_min, Y_Change_Max, auto=True)
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level8, "Y_Change_Max:", Y_Change_Max, "Y_Change_min:", Y_Change_min, self.VerticalScrollBarValue, self.VerticalScrollBar.value())
                self.VerticalScrollBarValue = self.VerticalScrollBar.value()
            self.LineFigure.draw()  # 重新画图
            PaintWithAxis_Display_The_Latest_Data = False #不自动显示最新的数据
        except Exception as e:
            self.UseLog.ErrorLog_Output("ScrollBarSliderMovedHandle Error:", e, "self.LineFigure.Update_X_Data len:", len(self.LineFigure.Update_X_Data), "self.LineFigure.Update_Y_Data len:", len(self.LineFigure.Update_Y_Data))
        PaintWithAxis_Setlim_Flag = False

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_Start_Flag', False)
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        # 动态调整窗口大小
        Change_wide = event.size().width()
        Change_high = event.size().height()
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "Change_wide:", Change_wide, ",Change_high:", Change_high)
        self.groupBox.setGeometry(QRect(self.Start_X, self.Start_Y, Change_wide - 2 * self.Start_X, Change_high - 2 * self.Start_Y))

    def Mouse_PressEvent(self, event):
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "event.xdata", event.xdata, "event.ydata", event.ydata, "event.button", event.button)
        if event.button == MouseButton.LEFT:
            self.LineFigure.VLine[self.Sign_Select - 1].set_xdata(event.xdata)
            self.LineFigure.VLine[self.Sign_Select - 1].set_visible(True)
            if self.Sign_Select == 1:
                self.X1_LineEdit.setText(str(event.xdata))
            elif self.Sign_Select == 2:
                self.X2_LineEdit.setText(str(event.xdata))

        if event.button == MouseButton.RIGHT:
            self.LineFigure.HLine[self.Sign_Select - 1].set_ydata(event.ydata)
            self.LineFigure.HLine[self.Sign_Select - 1].set_visible(True)
            if self.Sign_Select == 1:
                self.Y1_LineEdit.setText(str(event.ydata))
            elif self.Sign_Select == 2:
                self.Y2_LineEdit.setText(str(event.ydata))

        if event.button == MouseButton.MIDDLE:
            self.LineFigure.HLine[self.Sign_Select - 1].set_visible(False)
            self.LineFigure.VLine[self.Sign_Select - 1].set_visible(False)

        if(self.X1_LineEdit.text() != None and self.X2_LineEdit.text() != None):
            self.XDiff_LineEdit.setText(str(float(self.X2_LineEdit.text()) - float(self.X1_LineEdit.text())))
        if(self.Y2_LineEdit.text() != None and self.Y1_LineEdit.text() != None):
            self.YDiff_LineEdit.setText(str(float(self.Y2_LineEdit.text()) - float(self.Y1_LineEdit.text())))

        self.LineFigure.draw()  # 重新画图

    def Mouse_ScrollEvent(self, event):
        global PaintWithAxis_Setlim_Flag
        while PaintWithAxis_Setlim_Flag:
            time.sleep(1)
        PaintWithAxis_Setlim_Flag = True
        UpdateDataStartIndex = 0

        #触发事件轴域
        current_ax = event.inaxes
        #X轴和Y轴起止范围
        try:
            # x_min, x_max = current_ax.get_xlim()
            # y_min, y_max = current_ax.get_ylim()
            x_min, x_max = self.LineFigure.Axis.get_xlim()
            y_min, y_max = self.LineFigure.Axis.get_ylim()
            if x_min < 0:
                x_min = 0
            if x_max > PaintWithAxis_CacheData_Length:
                x_max = PaintWithAxis_CacheData_Length
        except AttributeError as e:
            self.UseLog.ErrorLog_Output("Mouse_ScrollEvent Error:", e)
            return

        #滚动鼠标时坐标轴刻度缩放幅度
        #计算出坐标轴中值
        x_mid = (x_max + x_min) / 2
        y_mid = (y_max + y_min) / 2
        if event.button == 'up':
            # # 鼠标向上滚，缩小坐标轴刻度范围，使得图形变大
            x_change_range = (x_max - x_min) / PaintWithAxis_Zooom_Range
            y_change_range = (y_max - y_min) / PaintWithAxis_Zooom_Range
        elif event.button == 'down':
            # 鼠标向下滚，增加坐标轴刻度范围，使得图形缩小
            x_change_range = (x_max - x_min) * PaintWithAxis_Zooom_Range
            y_change_range = (y_max - y_min) * PaintWithAxis_Zooom_Range

        if int(x_change_range) > PaintWithAxis_CacheData_Length:
            x_change_range = PaintWithAxis_CacheData_Length  # 显示出全部数据比例
        if int(x_change_range) < 2:
            x_change_range = 2

        x_change_min = x_mid - (x_change_range/2)
        x_change_max = x_mid + (x_change_range/2)
        y_change_min = y_mid - (y_change_range/2)
        y_change_max = y_mid + (y_change_range/2)

        if x_change_max > PaintWithAxis_CacheData_Length:
            x_change_max = PaintWithAxis_CacheData_Length
            x_change_min = PaintWithAxis_CacheData_Length - x_change_range
        if x_change_min < 1:
            x_change_min = 0
            x_change_max = x_change_range

        # current_ax.set(xlim=(x_change_min, x_change_max), ylim=(y_change_min, y_change_max))
        self.LineFigure.Axis.set_xlim(x_change_min, x_change_max, auto=True)
        self.LineFigure.Axis.set_ylim(y_change_min, y_change_max, auto=True)

        ################################# 增加显示数据的更新!!!#################################
        if x_change_min >= 0:
            X_Range = x_change_max - x_change_min + 1  # 此处需要＋1，否则调整的X轴范围会越来越小
            UpdateDataStartIndex = int(x_change_min)
        else:
            X_Range = x_change_max + 1
            UpdateDataStartIndex = 0

        if UpdateDataStartIndex < 0:
            UpdateDataStartIndex = 0
        if PaintWithAxis_CacheData_Length < int(UpdateDataStartIndex + X_Range):
            UpdateDataStartIndex = PaintWithAxis_CacheData_Length - int(X_Range)

        self.LineFigure.Update_Y_Data = [0 for j in range(int(X_Range))]
        try:
            for i in range(0, int(X_Range)):  # 获取当前坐标范围内数据
                self.LineFigure.Update_Y_Data[i] = self.LineFigure.Cache_Y_Data[int(UpdateDataStartIndex) + i]
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5,
                                         "Mouse_ScrollEvent UpdateDataStartIndex:", UpdateDataStartIndex, "x_change_min x_change_max:",
                                         x_change_min, x_change_max, "X_Range:", X_Range)
        except Exception as e:
            self.UseLog.ErrorLog_Output("Mouse_ScrollEvent Error StartHorIndex:", UpdateDataStartIndex, "X_Range:",
                                        X_Range, "i:", i, len(self.LineFigure.Update_Y_Data),
                                        len(self.LineFigure.Cache_Y_Data), "Error:", e)

        self.LineFigure.Update_X_Data = np.arange(int(UpdateDataStartIndex), int(UpdateDataStartIndex + X_Range))
        if np.max(self.LineFigure.Update_X_Data) == np.min(self.LineFigure.Update_X_Data):
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "#== UpdateDataStartIndex:", UpdateDataStartIndex, "X_Range:", X_Range, "x_change_min x_change_max:", x_change_min, x_change_max)
            return
        elif X_Range != (x_change_max - x_change_min + 1):
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "#!= UpdateDataStartIndex:", UpdateDataStartIndex, "X_Range:", X_Range, "x_change_min x_change_max:", x_change_min, x_change_max)

        if len(self.LineFigure.Update_X_Data) == len(self.LineFigure.Update_Y_Data):
            # self.LineFigure.Change_Axis_Xlim(self.LineFigure.Update_X_Data)  # 更新X轴坐标
            self.LineFigure.Line.set_xdata(self.LineFigure.Update_X_Data)  # 更新折线X轴数据，否则会出现未绘制过的X轴部分出现Y轴数据缺失显示
            self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)  # 更新折线Y轴数据,长度需要跟X轴数据一致，否则会出现“shape mismatch: objects cannot be broadcast to a single shape”错误

        # self.LineFigure.UseFigure.canvas.draw_idle()
        self.LineFigure.draw()  # 重新画图

        #同步更新滚动条
        After_x_min, Aftere_x_max = self.LineFigure.Axis.get_xlim()
        After_y_min, Aftere_y_max = self.LineFigure.Axis.get_ylim()

        self.Update_ScrollBar_Status( After_x_min, Aftere_x_max, After_y_min, Aftere_y_max)

        PaintWithAxis_Display_The_Latest_Data = False  # 不自动显示最新的数据
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Mouse_ScrollEvent  HorizontalScrollBar:", self.HorizontalScrollBar.value(), self.HorizontalScrollBar.maximum())
        PaintWithAxis_Setlim_Flag = False
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "x_min:", x_min, "x_max:", x_max, "x_mid:", x_mid, "x_change_range:", x_change_range, "x_change_min:", x_change_min, "x_change_max:", x_change_max, "After_x_min:", After_x_min, "Aftere_x_max:", Aftere_x_max)
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "y_min:", y_min, "y_max:", y_max, "y_mid:", y_mid, "y_change_range:", y_change_range, "y_change_min:", y_change_min, "y_change_max:", y_change_max, "After_y_min:", After_y_min, "Aftere_y_max:", Aftere_y_max)

    def Mouse_MoveEvent(self, event):
        self.MouseMoveMarkLabel.setText('X:' + str(event.xdata) + ' - Y:' + str(event.ydata))

    def XYButton(self):
        sender = self.sender()
        if sender.text() == "XY1":
            self.Sign_Select = 1
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "XY1")

        if sender.text() == "XY2":
            self.Sign_Select = 2
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "XY2")

    def Update_Data_Analyse(self, Source_Data):
        #解析接收到的字符串数据，先按指定分隔符切片，再将切片之后的数据转换成整型
        try:
            Source_List = Source_Data.split('\r\n') #分出行数据
            # print("Source_List", Source_List, len(Source_List))
            for i in range(len(Source_List)):
                Source_List[i] = Source_List[i].split(PaintWithAxis_UpdateData_separator)
                # print("Source_List[i]", Source_List[i], len(Source_List[i]))

            Result_List = [0 for i in range(len(Source_List))]
            # print("Result_List", len(Result_List))
            for i in range(len(Source_List)):
                Result_List[i] = [0 for j in range(len(Source_List[i]))]

            for i in range(len(Source_List)):
                for j in range(len(Source_List[i])):
                    try:
                        if Source_List[i][j] != '':
                            Result_List[i][j] = float(Source_List[i][j])
                    except Exception as e:
                        self.UseLog.ErrorLog_Output("Update_Data_Analyse str to float Error", e)
                        Error_List = []
                        return Error_List
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Source_List[", i, "][", j, "]:", Source_List[i][j], type(Source_List[i][j]), Result_List[i][j])
                    # print("Result_List[i]", Result_List[i], i, j, PaintWithAxis_UpdateData_Index)

            if (len(Source_List) - 1) < PaintWithAxis_UpdateData_Index or (len(Result_List) - 1) < PaintWithAxis_UpdateData_Index:   #源数据不完整无法解析出想要的数据
                Error_List = []
                return Error_List

            return Result_List[PaintWithAxis_UpdateData_Index]
        except Exception as e:
            self.UseLog.ErrorLog_Output("Update_Data_Analyse Error:", e)
            Error_List = []
            return Error_List

    def Update_ScrollBar_Status(self, After_x_min, Aftere_x_max, After_y_min, Aftere_y_max):
        Ver_Max = 0; Ver_Min = 0; VerBarValue = -1; VerBarLength = -1

        #横向滚动条处理
        if Aftere_x_max > PaintWithAxis_CacheData_Length:
            Aftere_x_max = PaintWithAxis_CacheData_Length
        self.HorizontalScrollBar.setValue(int(Aftere_x_max)/PaintWithAxis_SlideShowData_Step)
        self.HorizontalScrollBarValue = self.HorizontalScrollBar.value()

        #纵向滚动条处理
        After_y_range = Aftere_y_max - After_y_min
        Cache_Y_Data_Min = np.min(self.LineFigure.Cache_Y_Data)
        Cache_Y_Data_Max = np.max(self.LineFigure.Cache_Y_Data)
        Cache_Y_Data_range = Cache_Y_Data_Max - Cache_Y_Data_Min
        if After_y_range >= Cache_Y_Data_range and (Aftere_y_max >= Cache_Y_Data_Max and After_y_min <= Cache_Y_Data_Min):
                # 滚动条的长度为1
                VerBarLength = 0
        else:
            if Aftere_y_max >= Cache_Y_Data_Max:
                Ver_Max = Aftere_y_max
                # # 滚动条位于最上
                # VerBarValue = Ver_Min
            else:
                Ver_Max = Cache_Y_Data_Max

            if After_y_min <= Cache_Y_Data_Min:
                Ver_Min = After_y_min
                # # 滚动条位于最下
                # VerBarValue = Ver_Max
            else:
                Ver_Min = Cache_Y_Data_Min

        #可增加倍数值处理
        if VerBarLength == -1:
            VerBarLength = (Ver_Max - Ver_Min)
        if VerBarLength < 0:
            VerBarLength = 0
        if VerBarValue == -1:
            VerBarValue = (VerBarLength - After_y_min)
        if VerBarValue < 0:
            VerBarValue = 0

        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Aftere_y_max:", Aftere_y_max, "After_y_min:", After_y_min, "Cache_Y_Data_Max:", Cache_Y_Data_Max, "Cache_Y_Data_Min:", Cache_Y_Data_Min)
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "VerBarLength:", VerBarLength, "VerBarValue:", VerBarValue, "Ver_Max:", Ver_Max, "Ver_Min:", Ver_Min)
        self.VerticalScrollBar.setMaximum(VerBarLength)
        self.VerticalScrollBar.setValue(VerBarValue)
        self.VerticalScrollBarValue = self.VerticalScrollBar.value()

    def Update_Mark_Line(self, X_Move):
        for i in range(len(self.LineFigure.VLine)):
            X_Old = np.mean(self.LineFigure.VLine[i]. get_xdata())#标记为直线,取平均值
            X_Vline = X_Old + X_Move
            if X_Vline < 0:
                X_Vline = 0
            if self.LineFigure.VLine[i].get_visible():
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level8, "VLine:", i, "X_Old:", X_Old, "X_Move:", X_Move)
                self.LineFigure.VLine[i].set_xdata(X_Vline)
                if i == 0:
                    self.X1_LineEdit.setText(str(X_Vline))
                elif i == 1:
                    self.X2_LineEdit.setText(str(X_Vline))

        if (self.X1_LineEdit.text() != None and self.X2_LineEdit.text() != None):
            self.XDiff_LineEdit.setText(str(float(self.X2_LineEdit.text()) - float(self.X1_LineEdit.text())))


class Serial_Tool_UiUpdateWidgetStatus_Thread(threading.Thread):  # 继承父类threading.Thread
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
            SerOpenFlag = System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'Serial_Open_Flag')
            if SerOpenFlag:
                self.Widget.OpenButton.setEnabled(False)
            else:
                self.Widget.OpenButton.setEnabled(True)

class Serial_Tool_Widget(QWidget):
    def __init__(self, MainUI):
        super().__init__()
        self.UseLog = MainUI.UseLog
        self.UseGlobalVal = MainUI.UseGlobalVal
        self.initUI()

        try:
            self.UiUpdateWidgetStatusThread = Serial_Tool_UiUpdateWidgetStatus_Thread(1, "Serial_Tool_UiUpdateWidgetStatus_Thread", 2, self)
            self.UiUpdateWidgetStatusThread.setDaemon(True)
            self.UiUpdateWidgetStatusThread.start()
        except Exception as e:
            self.UseLog.ErrorLog_Output("Widget Create and start Thread Error:", e)

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
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level8, "list", self.port_list)

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
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level8, type(self.port_list[i]))
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
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, len(self.OpenPort), self.BaudRate, self.ByteSize, self.StopBits)
            if (len(self.OpenPort) != 0 or self.BaudRate != 0):
                try:
                    self.Serial = SerialToolSer.Serial_Tool_Ser(self.OpenPort, self.BaudRate, self.ByteSize, self.StopBits, self.Parity, None, self.UseLog, self.UseGlobalVal)
                    if (self.Serial.Open_Ret == True):  # 判断串口是否成功打开
                            self.OpenButton.setEnabled(False)
                            self.Serial.SerThread.Signal.connect(self.ShowRecvData)
                            self.Serial.SerThread.start()
                            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' ' + self.OpenPort + ' Successful')
                    else:
                        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' Fail')
                except Exception as e:
                    self.UseLog.ErrorLog_Output("打开串口异常:", e)
            else:
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, ' Please Select Port')

        if sender.text() == "关闭串口":
            self.OpenButton.setEnabled(True)
            if (self.Serial.Open_Ret == True):
                System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'Serial_Open_Flag', True)
                self.Serial.SerialColsePort()
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' Successful')

        if sender.text() == "发送数据":
            if 'Serial' in dir(self):
                if (self.Serial.Open_Ret == True):
                    if(self.Format):
                        self.Serial.SerialWritePort(self.Sendtext_Edit.text(), SerialWriteType.Dex)
                        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "Dex 写入字节数：", self.Serial.Send_Count)
                        self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + self.Sendtext_Edit.text())
                    else:
                        Sendtext = self.BuildSendData(self.Sendtext_Edit.text())  # 不进行转换 发送转成字节流时又转换成了ascii发送（例：02432D0D0A->30323433324430443041）
                        self.Serial.SerialWritePort(Sendtext, SerialWriteType.Hex)
                        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, "Hex 写入字节数：", self.Serial.Send_Count)
                        self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + str(Sendtext))
                else:
                    self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, sender.text() + ' ERROR')
            else:
                self.UseLog.ErrorLog_Output("PushButtonClickedHandle Send data not open serial!!")

        if sender.text() == "清空发送框":
            self.Sendtext_Edit.clear()

        if sender.text() == "清空接收框":
            self.Recvtext_Edit.clear()

        if sender.text() == "刷新端口":
            self.port_list = list(serial.tools.list_ports.comports())
            for i in range(0, len(self.port_list)):
                self.port_list[i] = str(self.port_list[i])
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, type(self.port_list[i]))
            self.Port_comboBox.clear()
            self.Port_comboBox.addItems(self.port_list)

        if sender.text() == "刷新绘图数据下标":
            global PaintWithAxis_UpdateData_Index
            Index = int(self.PaintUpdateIndex_comboBox.currentText())
            if Index != 0:
                PaintWithAxis_UpdateData_Index = Index - 1
            else:
                PaintWithAxis_UpdateData_Index = 0
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level6, "绘图下标更新为：", PaintWithAxis_UpdateData_Index)

    def RadioButtonClickedHandle(self):
        sender = self.sender()
        if sender.text() == "Dex" and self.Format == False and sender.isChecked():
            try:
                Hex2DexResult = self.StrHex2Dec(self.Sendtext_Edit.text())
            except Exception as e:
                self.HexButton.setChecked(True)
                self.UseLog.ErrorLog_Output("RadioButtonClickedHandle Hex2Dec Errror:", e)
                return
            self.Sendtext_Edit.setText(Hex2DexResult)
            self.Format = True

        if sender.text() == "Hex" and self.Format == True and sender.isChecked():
            try:
                Dec2HexResult = self.StrDec2Hex(self.Sendtext_Edit.text())
            except Exception as e:
                self.DexButton.setChecked(True)
                self.UseLog.ErrorLog_Output("RadioButtonClickedHandle Dec2Hex Errror:", e)
                return
            self.Sendtext_Edit.setText(Dec2HexResult)
            self.Format = False

    def BuildSendData(self, Source):
        nResult = Source.replace(" ", "")  # 删除空格
        nResult = bytes.fromhex(nResult)
        return nResult

    def StrDec2Hex(self, Source):
        lin = ['%02X' % ord(i) for i in Source]
        return " ".join(lin)

    def StrHex2Dec(self, Source):
        nResult = ""
        nLen = len(Source)
        Start_Index = 0
        for i in range(nLen):
            if i == 0and (i+1 < nLen) and Source[i] != 0 and (Source[i + 1] != 'x' and Source[i + 1] != 'X'):
                Start_Index = i
                nResult += chr(int(Source[Start_Index:Start_Index + 2], 16))
                i = Start_Index + 2
                continue
            elif Source[i] == " " and (i+2 < nLen)  and (Source[i + 2] != 'x' and Source[i + 2] != 'X'):
                Start_Index = i + 1
                nResult += chr(int(Source[Start_Index:Start_Index + 2], 16))
                i = Start_Index + 2
                continue
            elif Source[i] == '0' and (i+1 < nLen)  and (Source[i + 1] == 'x' or Source[i + 1] == 'X'):
                Start_Index = i + 2
                nResult += chr(int(Source[Start_Index:Start_Index + 2], 16))
                i = Start_Index + 2
                continue
        return nResult

    def GetOpenPort(self, port_str):
        # 选定串口
        if len(port_str):
            Front_index = port_str.find('(')
            Rear_index = port_str.find(')')
            self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, len(port_str), Front_index, Rear_index)
            return port_str[Front_index+1:Rear_index]
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "Get Serial Port NUll")
        return ''

    def ShowRecvData(self, RecvData):
        self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level3, "ShowRecvData:", RecvData,"len:", len(RecvData))
        if(len(RecvData)):
            try:
                self.Recvtext_Edit.append(RecvData)
            except Exception as e:
                self.UseLog.ErrorLog_Output("ShowRecvData  Recvtext_Edit append Error:", e)

class Serial_Tool_Progress_Thread(QThread):
    Signal = pyqtSignal(int)  # 定义信号类型为整型

    def __init__(self, nProgress):
        super(Serial_Tool_Progress_Thread, self).__init__()
        self.UseProgress = nProgress

    def run(self):
        for i in range(1, 100):
            if self.UseProgress.StartInitFlag == False:
                return
            time.sleep(self.UseProgress.StartInitTime/100)
            self.Signal.emit(i)  # 发射信号

class Serial_Tool_Progress(QWidget):
    def __init__(self):
        super(Serial_Tool_Progress, self).__init__()
        self.StartInitFlag = True
        self.StartInitTime = 2 #初始化时间，进度条显示加载完成时间
        self.UseProgressbar = QProgressBar(self)  # 进度条的定义(默认步骤最大值为99，最小值为0)
        self.UseProgressbar.setGeometry(30, 60, 500, 20) # 进度条的大小和位置，前两个是位置，后两个是大小
        self.UseProgressbar.setValue(0)
        self.show()
        self.ProgressThread = Serial_Tool_Progress_Thread(self)  # 实例化线程
        self.ProgressThread.Signal.connect(self.Signal_Accept)  # 将线程累中定义的信号链接到本类中的信号接收函数中
        self.ProgressThread.start()  # 启动线程，启动线程直接调用线程中的start方法，这个方法会调用run函数，因此不用调用run函数

    def Signal_Accept(self, ProgressIndex):
        self.UseProgressbar.setValue(int(ProgressIndex))  # 将线程的参数传入进度条
        if self.UseProgressbar.value() == 99:
            self.UseProgressbar.reset()

    def Exit(self):
        self.StartInitFlag = False
        self.close()


class Serial_Tool_MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.UseProgress = Serial_Tool_Progress()
        self.UseLog = System.Serial_Tool_Log()
        self.UseGlobalVal = System.Serial_Tool_GlobalManager()  # 初始化参数
        self.Serial_Tool_MainUI_Init()

    def Serial_Tool_MainUI_Init(self):
        self.UseWidget = Serial_Tool_Widget(self)
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

        self.UseProgress.Exit()

    def Serial_Tool_LogMenu_Init(self):
        #日志输出类型UI选项
        self.LogTypeList = []

        Log_type = QAction("日志输出到控制台", self, checkable=True)
        Log_type.setStatusTip('Use Print Output')
        Log_type.setChecked(True)
        Log_type.triggered.connect(self.Tool_LogOption)
        self.LogTypeList.append(Log_type)
        Log_type = QAction("日志输出到文件", self, checkable=True)
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
        fname = QFileDialog.getSaveFileName(self, 'Open file', '/*.txt')
        try:
            if fname[0]:
                self.UseLog.NormalLog_Output(LogModule.UiModule, LogLevel.Level5, fname[0])
                f = open(fname[0], 'w', encoding = 'utf-8')
                with f:
                    f.write(self.UseWidget.Recvtext_Edit.toPlainText())
                f.close()
        except Exception as e:
            self.UseLog.ErrorLog_Output("write file Error:", e)

    def Start_Draw(self):
        try:
            self.UseDraw = Serial_Tool_PaintWithAxisUi(self.UseLog,  self.UseGlobalVal) #Serial_Tool_Paint()
            self.UseDraw.setWindowIcon(QIcon('./Logo_Picture/PaintUI.jpeg'))
            self.UseDraw.show()
        except Exception as e:
            self.UseLog.ErrorLog_Output("Draw New Paint Error:", e)

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
            self.UseLog.ErrorLog_Output("log option error:", e)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.UseLog.Log_Close()
            if 'UseDraw' in dir(self):#判断类中是否存在该属性
                self.UseDraw.close()
            event.accept()
        else:
            event.ignore()
