import sys

class Servers_Log():
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