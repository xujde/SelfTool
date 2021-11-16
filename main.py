# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import sys, random, time, threading, os, ctypes
# 这里我们提供必要的引用。基本控件位于pyqt5.qtwidgets模块中。
from PyQt5.QtWidgets import (QWidget, QToolTip, QPushButton, QApplication, QDesktopWidget, QMessageBox,
                             QHBoxLayout, QVBoxLayout, QMainWindow, QAction, qApp,  QTextEdit, QLCDNumber, QSlider,
                             QInputDialog, QLineEdit, QGridLayout, QFileDialog, QLabel, QRadioButton, QMenu,
                             QComboBox, QLineEdit, QListWidget, QCheckBox, QListWidgetItem, QGroupBox)
from PyQt5.QtGui import QFont, QIcon, QPainter, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import QCoreApplication, Qt, QRect, QSize, pyqtSignal, QThread, QPoint, QMetaObject, QTimer
from matplotlib.backend_bases import MouseButton
from serial import Serial
import serial.tools.list_ports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib
import numpy as np

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决坐标轴中文显示问题
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号不显示的问题

Ser_Open_Flag = False  #串口打开标志
oneself = False  # 标志为模块自己运行
PaintWithAxis_Start_Flag = False  #绘图打开标志
PaintWithAxis_UpdateData = " "
PaintWithAxis_UpdateData_Flag = False #发送串口接收数据信号标志
PaintWithAxis_UpdateData_separator = ','

#复选框
class ComboCheckBox(QComboBox):
    def loadItems(self, items):
        self.items = items
        self.items.insert(0, '全部')
        self.row_num = len(self.items)
        self.Selectedrow_num = 0
        self.qCheckBox = []
        self.qLineEdit = QLineEdit()
        self.qLineEdit.setReadOnly(True)
        self.qListWidget = QListWidget()
        self.addQCheckBox(0)
        self.qCheckBox[0].stateChanged.connect(self.All)
        for i in range(0, self.row_num):
            self.addQCheckBox(i)
            self.qCheckBox[i].stateChanged.connect(self.showMessage)
        self.setModel(self.qListWidget.model())
        self.setView(self.qListWidget)
        self.setLineEdit(self.qLineEdit)
        # self.qLineEdit.textChanged.connect(self.printResults)

    def showPopup(self):
        #  重写showPopup方法，避免下拉框数据多而导致显示不全的问题
        select_list = self.Selectlist()  # 当前选择数据
        self.loadItems(items=self.items[1:])  # 重新添加组件
        for select in select_list:
            index = self.items[:].index(select)
            self.qCheckBox[index].setChecked(True)  # 选中组件
        return QComboBox.showPopup(self)

    def printResults(self):
        list = self.Selectlist()
        print(list)

    def addQCheckBox(self, i):
        self.qCheckBox.append(QCheckBox())
        qItem = QListWidgetItem(self.qListWidget)
        self.qCheckBox[i].setText(str(self.items[i]))
        self.qListWidget.setItemWidget(qItem, self.qCheckBox[i])

    def Selectlist(self):
        Outputlist = []
        for i in range(1, self.row_num):
            if self.qCheckBox[i].isChecked() == True:
                Outputlist.append(self.qCheckBox[i].text())
        self.Selectedrow_num = len(Outputlist)
        return Outputlist

    def showMessage(self):
        Outputlist = self.Selectlist()
        self.qLineEdit.setReadOnly(False)
        self.qLineEdit.clear()
        show = ';'.join(Outputlist)

        if self.Selectedrow_num == 0:
            self.qCheckBox[0].setCheckState(0)
        elif self.Selectedrow_num == self.row_num - 1:
            self.qCheckBox[0].setCheckState(2)
        else:
            self.qCheckBox[0].setCheckState(1)
        self.qLineEdit.setText(show)
        self.qLineEdit.setReadOnly(True)

    def All(self, zhuangtai):
        if zhuangtai == 2:
            for i in range(1, self.row_num):
                self.qCheckBox[i].setChecked(True)
        elif zhuangtai == 1:
            if self.Selectedrow_num == 0:
                self.qCheckBox[0].setCheckState(2)
        elif zhuangtai == 0:
            self.clear()

    def clear(self):
        for i in range(self.row_num):
            self.qCheckBox[i].setChecked(False)

    def currentText(self):
        text = QComboBox.currentText(self).split(';')
        if text.__len__() == 1:
            if not text[0]:
                return []
        return text

class Serial_Tool_Draw(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI() #界面绘制交给InitUi方法

    def initUI(self, Form):
        self.text = u'\u041b\u0435\u0432 \u041d\u0438\u043a\u043e\u043b\u0430\
        \u0435\u0432\u0438\u0447 \u0422\u043e\u043b\u0441\u0442\u043e\u0439: \n\
        \u0410\u043d\u043d\u0430 \u041a\u0430\u0440\u0435\u043d\u0438\u043d\u0430'


        #设置窗口的位置和大小
        self.setGeometry(300, 300, 300, 200)
        self.center()
        # 设置窗口的标题
        self.setWindowTitle('Draw')
        # 设置窗口的图标，引用当前目录下的icon.jpeg图片
        self.setWindowIcon(QIcon('icon.jpeg'))
        self.show()

    def Start(self):
        self.show()

    # 控制窗口显示在屏幕中心的方法
    def center(self):
        # 获得窗口
        qr = self.frameGeometry()
        # 获得屏幕中心点
        cp = QDesktopWidget().availableGeometry().center()
        # 显示到屏幕中心
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        # self.drawText(event, qp, self.text)
        # self.drawPoints(qp, 10, 10)
        # self.drawRectangles(qp, '#d4d4d4', 0, 0, 100, 10, 35, 90, 60)
        self.drawLines(qp,Qt.SolidLine, 2, 10, 15, 100, 25)
        # self.drawBrushes(qp)
        qp.end()

    def drawText(self, event, qp, text):
        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawText(event.rect(), Qt.AlignCenter, text)

    def drawPoints(self, qp, x, y):
        size = self.size()
        qp.drawPoint(x, y)
        # for i in range(1000):
        #     x = random.randint(1, size.width() - 1)
        #     y = random.randint(1, size.height() - 1)
        #     qp.drawPoint(x, y)

    def drawRectangles(self, qp, Color_Name, R, G, B, X, Y, X_Size, Y_Size):
        col = QColor(0, 0, 0)
        col.setNamedColor(Color_Name)
        qp.setPen(col)

        qp.setBrush(QColor(R, G, B))
        qp.drawRect(X, Y, X_Size, Y_Size)
        #
        # qp.setBrush(QColor(255, 80, 0, 160))
        # qp.drawRect(130, 35, 90, 60)
        #
        # qp.setBrush(QColor(25, 0, 90, 200))
        # qp.drawRect(250, 35, 90, 60)

    def drawLines(self, qp, Pen_Style, Pen_Wide, X1, Y1, X2, Y2):
        pen = QPen(Qt.black, Pen_Wide, Qt.SolidLine)
        pen.setStyle(Pen_Style)
        qp.setPen(pen)
        qp.drawLine(X1, Y1, X2, Y2)

        # pen.setStyle(Qt.DashLine)
        # qp.setPen(pen)
        # qp.drawLine(20, 80, 250, 80)
        #
        # pen.setStyle(Qt.DashDotLine)
        # qp.setPen(pen)
        # qp.drawLine(20, 120, 250, 120)
        #
        # pen.setStyle(Qt.DotLine)
        # qp.setPen(pen)
        # qp.drawLine(20, 160, 250, 160)
        #
        # pen.setStyle(Qt.DashDotDotLine)
        # qp.setPen(pen)
        # qp.drawLine(20, 200, 250, 200)

        # pen.setStyle(Qt.CustomDashLine)
        # pen.setDashPattern([1, 4, 5, 4])
        # qp.setPen(pen)
        # qp.drawLine(20, 240, 250, 240)

    def drawBrushes(self, qp):
        brush = QBrush(Qt.SolidPattern)
        qp.setBrush(brush)
        qp.drawRect(10, 15, 90, 60)

        brush.setStyle(Qt.Dense1Pattern)
        qp.setBrush(brush)
        qp.drawRect(130, 15, 90, 60)

        brush.setStyle(Qt.Dense2Pattern)
        qp.setBrush(brush)
        qp.drawRect(250, 15, 90, 60)

        brush.setStyle(Qt.DiagCrossPattern)
        qp.setBrush(brush)
        qp.drawRect(10, 105, 90, 60)

        brush.setStyle(Qt.Dense5Pattern)
        qp.setBrush(brush)
        qp.drawRect(130, 105, 90, 60)

        brush.setStyle(Qt.Dense6Pattern)
        qp.setBrush(brush)
        qp.drawRect(250, 105, 90, 60)

        brush.setStyle(Qt.HorPattern)
        qp.setBrush(brush)
        qp.drawRect(10, 195, 90, 60)

        brush.setStyle(Qt.VerPattern)
        qp.setBrush(brush)
        qp.drawRect(130, 195, 90, 60)

        brush.setStyle(Qt.BDiagPattern)
        qp.setBrush(brush)
        qp.drawRect(250, 195, 90, 60)

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

class Serial_Tool_Log():
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

class Serial_Tool_PaintWithAxisThread(QThread):
    signal = pyqtSignal(str) #信号

    def __init__(self,parent=None):
        super(Serial_Tool_PaintWithAxisThread,self).__init__(parent)

    def start_timer(self):
       self.start() #启动线程

    def run(self):
        global  PaintWithAxis_UpdateData_Flag
        while PaintWithAxis_Start_Flag:
            if(Ser_Open_Flag and PaintWithAxis_UpdateData_Flag):
                #Value = 1#random.randint(1, 100) #可换成需要的真实数据
                self.signal.emit(PaintWithAxis_UpdateData) #发送信号
                PaintWithAxis_UpdateData_Flag = True
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
        self.Axis.set_xlim(np.min(x_data), np.max(x_data), auto = True)
        self.Axis.set_ylim(np.min(y_data), np.max(y_data) + 2, auto = True)  # y轴稍微多一点，会好看一点

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

class Serial_Tool_PaintWithAxisUi(QMainWindow):
    def __init__(self, Log):
        super(Serial_Tool_PaintWithAxisUi, self).__init__()
        self.UseLog = Log
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
            global PaintWithAxis_Start_Flag
            PaintWithAxis_Start_Flag = True
            self.TimeStamp = time.time()
            self.PaintWithAxisThread = Serial_Tool_PaintWithAxisThread()
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
        #需要增加接收到的数据比坐标轴最大值更大处理
        y_data = self.Update_Data_Analyse(New_data)
        self.LineFigure.Updata_Count = len(y_data)
        for i in range(0, self.LineFigure.Data_Num - self.LineFigure.Updata_Count):
            self.LineFigure.Update_Y_Data[i] = self.LineFigure.Update_Y_Data[i + self.LineFigure.Updata_Count]
        for j in range(0, self.LineFigure.Updata_Count):
            self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - self.LineFigure.Updata_Count + j - 1] = y_data[j]
        self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)  # 更新数据
        self.LineFigure.draw()  # 重新画图

        # x_data = int(time.time() - self.TimeStamp)
        # if (x_data%self.LineFigure.Updata_Count):
        #     self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - self.LineFigure.Updata_Count + x_data - 1] = New_data
        #     # print("no attend", x_data, New_data)
        # else:
        #     self.LineFigure.Update_Y_Data[self.LineFigure.Data_Num - 1] = New_data
        #     if(x_data != 0):
        #         self.TimeStamp = time.time()
        #         self.UseLog.Log_Output("x:", x_data, "TimeStamp:", int(self.TimeStamp),"New_data:", New_data)
        #         self.UseLog.Log_Output("y:", self.LineFigure.Update_Y_Data)
        #         self.LineFigure.Line.set_ydata(self.LineFigure.Update_Y_Data)  # 更新数据
        #         self.LineFigure.draw()  # 重新画图
        #
        #         #数据往前移
        #         for i in range(0, self.LineFigure.Data_Num - self.LineFigure.Updata_Count):
        #             self.LineFigure.Update_Y_Data[i] = self.LineFigure.Update_Y_Data[i + self.LineFigure.Updata_Count]

    def PushButtonClickedHandle(self):
        global PaintWithAxis_Start_Flag
        sender = self.sender()

        if sender.text() == "开始":
            if not PaintWithAxis_Start_Flag:
                PaintWithAxis_Start_Flag = True
                self.TimeStamp = time.time()
                self.PaintWithAxisThread = Serial_Tool_PaintWithAxisThread()
                self.PaintWithAxisThread.signal.connect(self.UpdateData_UseSignal)
                self.PaintWithAxisThread.start()
        if sender.text() == "停止":
            PaintWithAxis_Start_Flag = False

        if sender.text() == "保存":
            fname = QFileDialog.getOpenFileName(self, 'Open file', '/first.png')
            # 增加对文件格式的判断
            try:
                self.LineFigure.UseFigure.savefig(fname[0], dpi=400, bbox_inches='tight')
                self.UseLog("Save Picture Success")
            except Exception as e:
                self.UseLog("Save Picture Error:", e)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            global PaintWithAxis_Start_Flag
            PaintWithAxis_Start_Flag = False
            event.accept()
        else:
            event.ignore()
    #动态调整窗口大小
    def resizeEvent(self, event):
        Change_wide = event.size().width()
        Change_high = event.size().height()
        self.UseLog.Log_Output("Change_wide:", Change_wide, ",Change_high:", Change_high)
        self.groupBox.setGeometry(QRect(self.Start_X, self.Start_Y, Change_wide - 2 * self.Start_X, Change_high - 2 * self.Start_Y))

    def Mouse_pressEvent(self, event):
        self.UseLog.Log_Output("event.xdata", event.xdata, "event.ydata", event.ydata, "event.button", event.button)
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

        self.XDiffLineEdit.setText(str(float(self.X2LineEdit.text()) - float(self.X1LineEdit.text())))
        self.YDiffLineEdit.setText(str(float(self.Y2LineEdit.text()) - float(self.Y1LineEdit.text())))

        self.LineFigure.draw()  # 重新画图

    def XYButton(self):
        sender = self.sender()
        if sender.text() == "XY1":
            self.Sign_Select = 1
            self.UseLog.Log_Output("XY1")

        if sender.text() == "XY2":
            self.Sign_Select = 2
            self.UseLog.Log_Output("XY2")

    def Update_Data_Analyse(self, Source_Data):
        #解析接收到的字符串数据，先按指定分隔符切片，再将切片之后的数据转换成整型
        Source_List = Source_Data.split(PaintWithAxis_UpdateData_separator)
        Result_List = [0 for i in range(len(Source_List))]
        print("Source_List len:", len(Source_List))
        # for i in range(len(Source_List)):
        #     Result_List[i] = int(Source_List)
        return Result_List

class Serial_Tool_SerThread(QThread, threading.Thread):
    Signal = pyqtSignal(str)

    def __init__(self, Function, parent=None):
        super(Serial_Tool_SerThread, self).__init__(parent)
        self.Function = Function
        self.setDaemon(True)

    def __del__(self):
        # 线程状态改变与线程终止
        self.wait()

    def run(self):
        while Ser_Open_Flag:
            self.Function(self.Signal)
            self.sleep(2)

class Serial_Tool_Ser(Serial):
    def __init__(self, portx, buand, bytesize, stopbits, parity, timeout):
        self.Open_Ret = False
        self.Strglo = " "
        self.UseSer = serial.Serial(portx, buand, timeout=timeout)
        if self.UseSer.isOpen:
            print(bytesize, stopbits, parity)
            self.UseSer.BYTESIZES = bytesize
            self.UseSer.STOPBITS = stopbits
            self.UseSer.PARITIES = parity
            self.UseSer._reconfigure_port()
            self.Open_Ret = True
            global Ser_Open_Flag
            Ser_Open_Flag = True
            try:
                self.SerThread = Serial_Tool_SerThread(self.SerialReadData)
            except Exception as e:
                print("Serial_Tool_Ser 创建线程异常：", e)

    # 显示接收串口数据
    def SerialReadData(self, Signal):
        global PaintWithAxis_UpdateData
        global PaintWithAxis_UpdateData_Flag
        # 循环接收数据，此为死循环，可用线程实现
        if(self.UseSer.isOpen):
            self.Strglo = time.strftime("[%Y-%m-%d %H:%M:%S (R)]", time.localtime())
            # Signal.emit(self.Strglo)
            if self.UseSer.in_waiting:
                # print("in_waiting", self.UseSer.in_waiting)
                try :
                    ReadString =  self.UseSer.read( self.UseSer.in_waiting).decode(encoding = 'utf-8')
                    self.Strglo += ReadString
                except Exception as e:
                    print("SerialReadData Error:", e)
                # print("Strglo :", self.Strglo, type(self.Strglo))
                Signal.emit(self.Strglo)
                PaintWithAxis_UpdateData = ReadString
                PaintWithAxis_UpdateData_Flag = True

    # 关闭串口
    def SerialColsePort(self):
        if self.UseSer.isOpen():
            global Ser_Open_Flag
            Ser_Open_Flag = False
            self.Open_Ret = False
            self.UseSer.close()

    # 写数据
    def SerialWritePort(self, text):
        self.Send_Count = 0
        if self.UseSer.isOpen:
            self.Send_Count = self.UseSer.write(text.encode("gbk"))  # 写数据

class Serial_Tool_Widget(QWidget):
    def __init__(self, Log):
        super().__init__()
        self.UseLog = Log
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
        self.UseLog.Log_Output("list", self.port_list)

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

        self.Sendtext_Edit = QLineEdit()#QTextEdit()
        self.Recvtext_Edit = QTextEdit()

        self.OpenButton = QPushButton('打开串口', self)
        self.CloseButton = QPushButton("关闭串口", self)
        self.SendButton = QPushButton("发送数据", self)
        self.ClearSendButton = QPushButton("清空发送框", self)
        self.ClearRecvButton = QPushButton("清空接收框", self)
        self.refreshPortButton = QPushButton("刷新端口", self)
        self.DexButton = QRadioButton('Dex', self)
        self.HexButton = QRadioButton('Hex', self)
        self.DexButton.setChecked(True)

        self.OpenButton.clicked.connect(self.PushButtonClickedHandle)
        self.CloseButton.clicked.connect(self.PushButtonClickedHandle)
        self.SendButton.clicked.connect(self.PushButtonClickedHandle)
        self.ClearSendButton.clicked.connect(self.PushButtonClickedHandle)
        self.ClearRecvButton.clicked.connect(self.PushButtonClickedHandle)
        self.refreshPortButton.clicked.connect(self.PushButtonClickedHandle)

        self.DexButton.toggled.connect(self.RadioButtonClickedHandle)
        self.HexButton.toggled.connect(self.RadioButtonClickedHandle)

        self.Port_comboBox = QComboBox(self)
        for i in range(0, len(self.port_list)):
            self.port_list[i] = str(self.port_list[i])
            self.UseLog.Log_Output(type(self.port_list[i]))
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

        self.Port_comboBox.setMinimumSize(QSize(100, 20))
        self.Baud_comboBox.setMinimumSize(QSize(100, 20))
        self.Data_comboBox.setMinimumSize(QSize(100, 20))
        self.Stop_comboBox.setMinimumSize(QSize(100, 20))
        self.Parity_comboBox.setMinimumSize(QSize(100, 20))

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
        grid.addWidget(self.refreshPortButton, X_Index + 5 * X_ButtonStep, Y_Index + Y_ButtonStep)

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
            self.UseLog.Log_Output(len(self.OpenPort), self.BaudRate, self.ByteSize, self.StopBits)
            if (len(self.OpenPort) != 0 or self.BaudRate != 0):
                self.Serial = Serial_Tool_Ser(self.OpenPort, self.BaudRate, self.ByteSize, self.StopBits, self.Parity, None)
                if (self.Serial.Open_Ret == True):  # 判断串口是否成功打开
                    try:
                        self.OpenButton.setEnabled(False)
                        self.Serial.SerThread.Signal.connect(self.ShowRecvData)
                        self.Serial.SerThread.start()
                        self.UseLog.Log_Output(sender.text() + ' ' + self.OpenPort + ' Successful')
                    except Exception as e:
                        self.UseLog.Log_Output("打开串口异常:", e)
                else:
                    self.UseLog.Log_Output(sender.text() + ' Fail')
            else:
                self.UseLog.Log_Output(' Please Select Port')

        if sender.text() == "关闭串口":
            self.OpenButton.setEnabled(True)
            if (self.Serial.Open_Ret == True):
                self.Serial.SerialColsePort()
                self.UseLog.Log_Output(sender.text() + ' Successful')

        if sender.text() == "发送数据":
            if (self.Serial.Open_Ret == True):
                if(self.Format):
                    self.Serial.SerialWritePort(self.Sendtext_Edit.text())
                    self.UseLog.Log_Output("Dex 写入字节数：", self.Serial.Send_Count)
                    self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + self.Sendtext_Edit.text())
                else:
                    self.Serial.SerialWritePort(self.Sendtext_Edit.text().encode('utf-8').hex())
                    self.UseLog.Log_Output("Hex 写入字节数：", self.Serial.Send_Count)
                    self.Recvtext_Edit.append(time.strftime("[%Y-%m-%d %H:%M:%S (T)] ", time.localtime()) + self.Sendtext_Edit.text().encode('utf-8').hex())
            else:
                self.UseLog.Log_Output(sender.text() + ' ERROR')

        if sender.text() == "清空发送框":
            self.Sendtext_Edit.clear()

        if sender.text() == "清空接收框":
            self.Recvtext_Edit.clear()

        if sender.text() == "刷新端口":
            self.port_list = list(serial.tools.list_ports.comports())
            for i in range(0, len(self.port_list)):
                self.port_list[i] = str(self.port_list[i])
                self.UseLog.Log_Output(type(self.port_list[i]))
            self.Port_comboBox.clear()
            self.Port_comboBox.addItems(self.port_list)

    def RadioButtonClickedHandle(self):
        sender = self.sender()
        if sender.text() == "Dex":
            self.Format = True
            self.UseLog.Log_Output("Dex")

        if sender.text() == "Hex":
            self.Format = False
            self.UseLog.Log_Output("Hex")

    # 选定串口
    def GetOpenPort(self, port_str):
        if len(port_str):
            Front_index = port_str.find('(')
            Rear_index = port_str.find(')')
            self.UseLog.Log_Output(len(port_str), Front_index, Rear_index)
            return port_str[Front_index+1:Rear_index]
        self.UseLog.Log_Output("NUll")
        return ''

    def ShowRecvData(self, RecvData):
        self.UseLog.Log_Output("ShowRecvData:", RecvData,"len:", len(RecvData))
        if(len(RecvData)):
            try:
                self.Recvtext_Edit.append(RecvData)
            except Exception as e:
                self.UseLog.Log_Output("ShowRecvData  Recvtext_Edit append Error:", e)

class Serial_Tool_MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.UseLog = Serial_Tool_Log()
        self.initUI()

    def initUI(self):
        self.UseWidget = Serial_Tool_Widget(self.UseLog)
        self.setCentralWidget(self.UseWidget)
        # self.MyDraw = Serial_Tool_Paint()#Serial_Tool_Draw()
        #创建状态栏的小窗口
        self.statusBar().showMessage('Ready')

        self.Open_file_menu = QAction(QIcon('Open.png'), "打开", self)
        self.Open_file_menu.setShortcut('Ctrl+' + 'O')
        self.Open_file_menu.setStatusTip('Open File')
        self.Open_file_menu.triggered.connect(self.ReloadDialog)
        self.Save_file_menu = QAction(QIcon('Save.jpeg'), "保存", self)
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

        self.Start_Draw_menu = QAction(QIcon('Save.jpeg'), "启动绘图", self)
        self.Start_Draw_menu.setShortcut('Ctrl+' + 'T')
        self.Start_Draw_menu.setStatusTip('Start Draw')
        self.Start_Draw_menu.triggered.connect(self.Start_Draw)
        # 创建一个菜单栏
        Drawmenubar = self.menuBar()
        DrawMenu = Drawmenubar.addMenu('&画图')
        DrawMenu.addAction(self.Start_Draw_menu)

        #显示勾选
        self.Log_Type1 = QAction("日志输出类型1", self, checkable = True)
        self.Log_Type1.setStatusTip('Use Print Output')
        self.Log_Type1.setChecked(True)
        self.Log_Type1.triggered.connect(self.Debug_Option)
        Log_Type_menu = QMenu('日志输出类型', self)
        Log_Type_menu.addAction(self.Log_Type1)
        self.Log_SwON = QAction("打开日志输出", self, checkable = True)
        self.Log_SwON.setStatusTip('Debug Switch ON')
        self.Log_SwON.setChecked(False)
        self.Log_SwON.triggered.connect(self.Debug_Option)
        self.Log_SwOFF = QAction("关闭日志输出", self, checkable = True)
        self.Log_SwOFF.setStatusTip('Debug Switch OFF')
        self.Log_SwOFF.setChecked(True)
        self.Log_SwOFF.triggered.connect(self.Debug_Option)
        Log_Sw_menu = QMenu('日志开关', self)
        Log_Sw_menu.addAction(self.Log_SwON)
        Log_Sw_menu.addAction(self.Log_SwOFF)
        # 创建一个菜单栏
        Logmenubar = self.menuBar()
        LogMenu = Logmenubar.addMenu('&日志')
        LogMenu.addMenu(Log_Sw_menu)
        LogMenu.addMenu(Log_Type_menu)

        self.setGeometry(300, 300, 800, 300)
        self.setWindowTitle('Menu')
        self.show()

    def ReloadDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            f = open(fname[0], 'r')
            with f:
                data = f.read()
                self.UseWidget.Recvtext_Edit.setText(data)

    def SaveDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            # self.UseLog.Log_Output(fname[0])
            f = open(fname[0], 'w')
            with f:
                f.write(self.MyWidget.Recvtext_Edit.toPlainText())
            f.close()

    def Start_Draw(self):
        try:
            self.UseDraw = Serial_Tool_PaintWithAxisUi(self.UseLog) #Serial_Tool_Paint()
            self.UseDraw.show()
        except Exception as e:
            self.UseLog.Log_Output("Error:", e)

    def Debug_Option(self):
        sender = self.sender()

        if sender.text() == "打开日志输出":
            self.UseLog.Change_Switch(True)
            self.Log_SwOFF.setChecked(False)
            self.Log_SwON.setChecked(True)

        if sender.text() == "关闭日志输出":
            self.UseLog.Change_Switch(False)
            self.Log_SwON.setChecked(False)
            self.Log_SwOFF.setChecked(True)

        if sender.text() == "日志输出类型1":
            self.UseLog.Change_Type(1)
            self.Log_Type1.setChecked(True)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # 创建应用程序和对象
    # 每一pyqt5应用程序必须创建一个应用程序对象。sys.argv参数是一个列表，从命令行输入参数。
    app = QApplication(sys.argv)
    ex = Serial_Tool_MainUI()
    # 系统exit()方法确保应用程序干净的退出
    # 的exec_()方法有下划线。因为执行是一个Python关键词。因此，exec_()代替
    sys.exit(app.exec_())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
