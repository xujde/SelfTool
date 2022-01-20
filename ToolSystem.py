import sys
from enum import Enum
import datetime
from PyQt5.QtWidgets import QWidget, QMessageBox

class LogModule(Enum):
    # 可根据不同工程包含的模块进行增加
    SysModule = 1
    UiModule = 2

    LogModuleMax = 3

class LogLevel(Enum):
    #默认定义8个输出等级，可根据不同工程进行添加
    Level1 = 1
    Level2 = 2
    Level3 = 3
    Level4 = 4
    Level5 = 5
    Level6 = 6
    Level7 = 7
    Level8 = 8

    LogLevelMax = Level8

class LogType(Enum):
    PrintType = 1 #print打印到stdout
    LogfileType = 2 #print输出到文件

#print输出重定向到变量中
class Self_Tool_ErrorLogFile():
    def __init__(self):
        self.ErrorLogMsg = ""
    #需要有write方法
    def write(self, Msg):
        self.ErrorLogMsg += Msg

    def Get(self):
        return self.ErrorLogMsg

    def Clear(self):
        self.ErrorLogMsg = ""

#调试日志功能
class Self_Tool_Log(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.LogType = LogType.PrintType
        self.LogModule = 0
        self.LogLevel = 0
        self.ErrorLogFile = Self_Tool_ErrorLogFile()

        if self.LogType == LogType.LogfileType:#输出日志到文件先创建日志文件
            self.Create_LogFile()

    def NormalLog_Output(self, l_Module, l_Level, *cObjects, cSep=' ', cEnd='\n', cFile=sys.stdout, cFlush=False):
        try:
            if ((self.LogModule & (1 << int(str(l_Module.value)))) and (self.LogLevel >= int(str(l_Level.value)))):
                if(self.LogType == LogType.PrintType):
                    print(*cObjects, sep=cSep, end=cEnd, file=cFile, flush=cFlush)
                elif(self.LogType == LogType.LogfileType):
                    print(*cObjects, sep=cSep, end=cEnd, file=self.LogFile, flush=cFlush)
        except Exception as e:
            print("LOG OUTPUT ERROR:", e, str(l_Module.value), str(l_Level.value))

    def ErrorLog_Output(self, *cObjects, cSep=' ', cEnd='\n', cFile=sys.stdout, cFlush=False):
        self.ErrorLogFile.Clear()
        print(*cObjects, sep=cSep, end=cEnd, file=self.ErrorLogFile, flush=cFlush)
        reply = QMessageBox.question(self, "Error", self.ErrorLogFile.Get(), QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            return

    def Change_Type(self, cType):
        if  self.LogType == cType:
            return
        elif self.LogType == LogType.LogfileType:#上一个类型是日志文件则先关闭
            self.LogFile.close()

        self.LogType = cType

        if self.LogType == LogType.LogfileType:#切换为输出日志到文件创建日志文件
            self.Create_LogFile()

    def Change_Module(self, cModule, cSwitch):
        if cSwitch:
            self.LogModule |= (1 << cModule)
        else:
            self.LogModule &= ~(1 << cModule)

    def Change_Level(self, cLevel):
        self.LogLevel = cLevel

    def Create_LogFile(self):
        self.LogFile = open('./SelfToolLog.txt', 'a', encoding='utf-8')
        self.LogFile.write(str(datetime.datetime.now()))
        self.LogFile.write('\n')

    def Log_Close(self):
        if self.LogType == LogType.LogfileType:
            self.LogFile.close()

## 使用字典管理自定义多文件共享全局变量
class Self_Tool_GlobalManager():
    def __init__(self):
        global GlobalVal_dict
        GlobalVal_dict = { }

    def Global_Set(self, Key, Value):
        GlobalVal_dict[Key] = Value

    def Global_Get(self, Key, DefaultValue=None):
        try:
            return GlobalVal_dict[Key]
        except KeyError:
            return DefaultValue