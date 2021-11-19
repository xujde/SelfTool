import sys
from enum import Enum

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

class Serial_Tool_Log():
    def __init__(self, parent=None):
        self.LogType = 1  # 1为print打印
        self.LogModule = 0
        self.LogLevel = 0

    def Log_Output(self, l_Module, l_Level, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
        try:
            if ((self.LogModule & (1 << int(str(l_Module.value)))) and (self.LogLevel >= int(str(l_Level.value)))):
                if (self.LogType == 1):
                    print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)
        except Exception as e:
            print("LOG OUTPUT ERROR:", e, str(l_Module.value), str(l_Level.value))

    def Change_Type(self, cType):
        self.LogType = cType

    def Change_Module(self, cModule, cSwitch):
        if cSwitch:
            self.LogModule |= (1 << cModule)
        else:
            self.LogModule &= ~(1 << cModule)

    def Change_Level(self, cLevel):
        self.LogLevel = cLevel

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