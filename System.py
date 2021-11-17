import sys

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