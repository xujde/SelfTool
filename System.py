import sys
from enum import Enum
import datetime

class LogModule(Enum):
    # 可根据不同工程包含的模块进行增加
    SysModule = 1
    UiModule = 2
    SerModule = 3

    LogModuleMax = 4

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


#调试日志功能
class Serial_Tool_Log():
    def __init__(self, parent=None):
        self.LogType = LogType.PrintType
        self.LogModule = 0
        self.LogLevel = 0

        if self.LogType == LogType.LogfileType:#输出日志到文件先创建日志文件
            self.Create_LogFile()

    def Log_Output(self, l_Module, l_Level, *cObjects, cSep=' ', cEnd='\n', cFile=sys.stdout, cFlush=False):
        try:
            if ((self.LogModule & (1 << int(str(l_Module.value)))) and (self.LogLevel >= int(str(l_Level.value)))):
                if(self.LogType == LogType.PrintType):
                    print(*cObjects, sep=cSep, end=cEnd, file=cFile, flush=cFlush)
                elif(self.LogType == LogType.LogfileType):
                    print(*cObjects, sep=cSep, end=cEnd, file=self.LogFile, flush=cFlush)
        except Exception as e:
            print("LOG OUTPUT ERROR:", e, str(l_Module.value), str(l_Level.value))

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
        self.LogFile = open('./SerialToolLog.txt', 'a', encoding='utf-8')
        self.LogFile.write(str(datetime.datetime.now()))
        self.LogFile.write('\n')

    def Log_Close(self):
        if self.LogType == LogType.LogfileType:
            self.LogFile.close()

## 使用字典管理自定义多文件共享全局变量
class Serial_Tool_GlobalManager():
    def __init__(self):
        global GlobalVal_dict
        #串口打开标志； 更新绘图数据标志； 更新绘图数据； 绘图打开标志
        GlobalVal_dict = {'Serial_Open_Flag' : False, 'PaintWithAxis_UpdateData_Flag' : False, 'PaintWithAxis_UpdateData' : " ",
                          'PaintWithAxis_Start_Flag' : False}

    def Global_Set(self, key, value):
        GlobalVal_dict[key] = value

    def Global_Get(self, key, defValue=None):
        try:
            return GlobalVal_dict[key]
        except KeyError:
            return defValue