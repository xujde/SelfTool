import random, time, threading
from PyQt5.QtWidgets import (QWidget, QToolTip, QPushButton, QApplication, QDesktopWidget, QMessageBox,
                             QHBoxLayout, QVBoxLayout, QMainWindow, QAction, qApp,  QTextEdit, QLCDNumber, QSlider,
                             QInputDialog, QLineEdit, QGridLayout, QFileDialog, QLabel, QRadioButton,
                             QComboBox, QLineEdit, QListWidget, QCheckBox, QListWidgetItem, QGroupBox, QMenu)
from PyQt5.QtGui import QFont, QIcon, QPainter, QColor, QPen, QBrush, QPixmap
from PyQt5.QtCore import QCoreApplication, Qt, QRect, QSize, pyqtSignal, QThread, QPoint, QMetaObject, QTimer
from serial import Serial
import serial.tools.list_ports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib
import numpy as np

#以下为自定义模块
import ToolSystem
from ToolSystem import LogModule
from ToolSystem import LogLevel
from ToolSystem import LogType

matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 解决坐标轴中文显示问题
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号不显示的问题


#复选框
class Tool_ComboCheckBox(QComboBox):
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

class Tool_Draw(QWidget):
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

class Tool_Widget(QWidget):
    def __init__(self, UseLog):
        super().__init__()
        self.UseLog = UseLog

        self.Tool_Widget_Init()

    def Tool_Widget_Init(self):
        self.ToolUI_Setup()
        self.ToolUI_Layout()

    def ToolUI_Setup(self):
        #单选框
        self.ToolComboBoxList = ['Self', 'Serial', 'Servers']
        self.ToolComboBox = QLabel('单选框')
        self.Tool_ComboBox = QComboBox(self)
        self.Tool_ComboBox.addItems(self.ToolComboBoxList)
        self.Tool_ComboBox.setMinimumSize(QSize(100, 20))

        #复选框
        self.ToolComboCheckBoxList = ['main', 'system', 'Ui', 'serial', 'socket']
        self.ToolComboCheckBox = QLabel('复选框')
        self.Tool_ComboCheckBox = Tool_ComboCheckBox()
        self.Tool_ComboCheckBox.loadItems(self.ToolComboCheckBoxList)
        self.Tool_ComboCheckBox.setMinimumSize(QSize(100, 20))

        #行编辑和文本编辑框
        self.ToolInputLineEdit = QLineEdit()
        self.ToolOutputtextEdit = QTextEdit()

        #按钮
        self.ToolClearInputQPushButton = QPushButton("清空输入框", self)
        self.ToolClearOutputQPushButton = QPushButton("清空输出框", self)

        #单选按钮
        self.ToolQRadioButton1 = QRadioButton('单选按钮1', self)
        self.ToolQRadioButton2 = QRadioButton('单选按钮2', self)
        self.ToolQRadioButton1.setChecked(True)

        self.ToolClearInputQPushButton.clicked.connect(self.ToolPushButtonClickedHandle)
        self.ToolClearOutputQPushButton.clicked.connect(self.ToolPushButtonClickedHandle)

        self.ToolQRadioButton1.toggled.connect(self.ToolRadioButtonClickedHandle)
        self.ToolQRadioButton2.toggled.connect(self.ToolRadioButtonClickedHandle)

    def ToolUI_Layout(self):
        grid = QGridLayout()
        grid.setSpacing(20)

        X_Index = 1;Y_Index = 0
        Y_ToolComboBoxStep = 1
        X_ToolComboCheckBoxOffset = 1;Y_TooltextEditStep = 1
        Y_ToolPushButtonOffset = 2;Y_ToolPushButtonStep = 1
        X_TooltextEditOffset = 2;Y_TooltextEditOffset = 2;Y_TooltextEditStep = 1
        Y_ToolRadioButtontOffset = 4;X_ToolRadioButtonStep = 2

        grid.addWidget(self.ToolComboBox, X_Index, Y_Index)
        grid.addWidget(self.Tool_ComboBox, X_Index, Y_Index + Y_ToolComboBoxStep)

        grid.addWidget(self.ToolComboCheckBox, X_Index + X_ToolComboCheckBoxOffset, Y_Index)
        grid.addWidget(self.Tool_ComboCheckBox, X_Index + X_ToolComboCheckBoxOffset, Y_Index + Y_TooltextEditStep)

        grid.addWidget(self.ToolInputLineEdit, X_Index + X_TooltextEditOffset, Y_Index + Y_TooltextEditOffset)
        grid.addWidget(self.ToolOutputtextEdit, X_Index + X_TooltextEditOffset, Y_Index + Y_TooltextEditOffset + Y_TooltextEditStep)

        grid.addWidget(self.ToolClearInputQPushButton, X_Index , Y_Index + Y_ToolPushButtonOffset)
        grid.addWidget(self.ToolClearOutputQPushButton, X_Index , Y_Index + Y_ToolPushButtonOffset + Y_ToolPushButtonStep)

        grid.addWidget(self.ToolQRadioButton1, X_Index, Y_Index + Y_ToolRadioButtontOffset)
        grid.addWidget(self.ToolQRadioButton2, X_Index + X_ToolRadioButtonStep, Y_Index + Y_ToolRadioButtontOffset)

        self.setLayout(grid)

    def ToolPushButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "清空输入框":
            self.ToolInputLineEdit.clear()

        if sender.text() == "清空输出框":
            self.ToolOutputtextEdit.clear()

    def ToolRadioButtonClickedHandle(self):
        sender = self.sender()

        if sender.text() == "单选按钮1":
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3,"单选按钮1")

        if sender.text() == "单选按钮2":
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level3,"单选按钮2")

class Tool_MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.UseLog = ToolSystem.Self_Tool_Log()
        self.Tool_MainUI_Init()

    def Tool_MainUI_Init(self):
        self.UseWidget = Tool_Widget(self.UseLog)
        self.setCentralWidget(self.UseWidget)

        #创建状态栏的小窗口
        self.statusBar().showMessage('Ready')

        self.Tool_FileMenu_Init()
        self.Tool_LogMenu_Init()

        self.setGeometry(300, 300, 800, 300)
        self.setWindowIcon(QIcon('./Logo_Picture/ToolMainUI.jpeg'))
        self.setWindowTitle('SelfTool')
        self.show()

    def Tool_FileMenu_Init(self):
        self.Open_file_menu = QAction(QIcon('./Logo_Picture/Open.png'), "打开", self)
        self.Open_file_menu.setShortcut('Ctrl+' + 'O')
        self.Open_file_menu.setStatusTip('Open File')
        self.Open_file_menu.triggered.connect(self.Tool_ReloadDialog)
        self.Save_file_menu = QAction(QIcon('./Logo_Picture/Save.jpeg'), "保存", self)
        self.Save_file_menu.setShortcut('Ctrl+' + 'S')
        self.Save_file_menu.setStatusTip('Save File')
        self.Save_file_menu.triggered.connect(self.Tool_SaveDialog)
        # 创建一个菜单栏
        filemenubar = self.menuBar()
        # 添加菜单
        FileMenu = filemenubar.addMenu('&文件')
        # 添加事件
        FileMenu.addAction(self.Open_file_menu)
        FileMenu.addAction(self.Save_file_menu)

    def Tool_LogMenu_Init(self):
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

    def Tool_ReloadDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            f = open(fname[0], 'r', encoding = 'utf-8')
            with f:
                data = f.read()
                self.UseWidget.ToolInputLineEdit.setText(data)

    def Tool_SaveDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            self.UseLog.Log_Output(LogModule.UiModule, LogLevel.Level5, fname[0])
            f = open(fname[0], 'w', encoding = 'utf-8')
            with f:
                f.write(self.UseWidget.ToolOutputtextEdit.toPlainText())
            f.close()

    def Tool_LogOption(self):
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
