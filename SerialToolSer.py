import threading, time
from PyQt5.QtCore import QThread, pyqtSignal
from serial import Serial
import serial.tools.list_ports
import binascii
from enum import Enum

import System
from System import LogModule
from System import LogLevel

class SerialWriteType(Enum):
    # 可根据不同工程包含的模块进行增加
    Dex = 1
    Hex = 2

class Serial_Tool_SerThread(QThread, threading.Thread):
    Signal = pyqtSignal(str)

    def __init__(self, Function, GlobalVal, parent=None):
        super(Serial_Tool_SerThread, self).__init__(parent)
        self.UseGlobalVal = GlobalVal
        self.Function = Function
        self.setDaemon(True)

    def __del__(self):
        # 线程状态改变与线程终止
        self.wait()

    def run(self):
        while System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'Serial_Open_Flag'):
            self.Function(self.Signal)
            self.sleep(2)

class Serial_Tool_Ser(Serial):
    def __init__(self, portx, buand, bytesize, stopbits, parity, timeout, Log, GlobalVal):
        self.Open_Ret = False
        self.Strglo = " "
        self.UseLog = Log
        self.UseGlobalVal = GlobalVal
        self.UseSer = serial.Serial(portx, buand, timeout=timeout)
        self.Send_Count = 0
        if self.UseSer.isOpen:
            self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level3, bytesize, stopbits, parity)
            self.UseSer.BYTESIZES = bytesize
            self.UseSer.STOPBITS = stopbits
            self.UseSer.PARITIES = parity
            self.UseSer._reconfigure_port()
            self.Open_Ret = True
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'Serial_Open_Flag', True)
            try:
                self.SerThread = Serial_Tool_SerThread(self.SerialReadData, self.UseGlobalVal)
                self.SerThread.setDaemon(True)
            except Exception as e:
                self.UseLog.ErrorLog_Output("Serial_Tool_Ser 创建线程异常：", e)

    # 显示接收串口数据
    def SerialReadData(self, Signal):
        # 循环接收数据，此为死循环，可用线程实现
        try:
            if self.UseSer.isOpen:
                self.Strglo = time.strftime("[%Y-%m-%d %H:%M:%S (R)]", time.localtime())
                if self.UseSer.in_waiting:
                    # print("in_waiting", self.UseSer.in_waiting)
                    ReadSource = self.UseSer.read(self.UseSer.in_waiting)
                    try :
                        ReadString =  ReadSource.decode('GBK')
                        self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level6, ReadSource, "--decode-->", ReadString)
                    except :
                        ReadString = binascii.b2a_hex(ReadSource)
                        ReadString = str(ReadString)
                        self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level6, ReadSource, "--b2a_hex-->", ReadString)

                    self.Strglo += ReadString
                    # print("Strglo :", self.Strglo, type(self.Strglo))
                    Signal.emit(self.Strglo)
                    if System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_Start_Flag'):
                        Wait_Count = 0
                        while System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'PaintWithAxis_UpdateData_Flag'):
                            time.sleep(1)
                            Wait_Count = Wait_Count + 1
                            if(Wait_Count > 10):
                                self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level3, "PaintWithAxis not use UpdateData")
                                break
                        System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_UpdateData', ReadString)
                        System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'PaintWithAxis_UpdateData_Flag', True)
            else:
                self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level6, "SerialReadData Serial not open!!!")
        except Exception as e:
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'Serial_Open_Flag', False)
            self.UseLog.ErrorLog_Output("SerialReadData Error:", e)

    # 关闭串口
    def SerialColsePort(self):
        if self.UseSer.isOpen() and System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'Serial_Open_Flag'):
            System.Serial_Tool_GlobalManager.Global_Set(self.UseGlobalVal, 'Serial_Open_Flag', False)
            self.Open_Ret = False
            self.UseSer.close()
        else:
            self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level6, "SerialColsePort Serial not open!!!")

    # 写数据
    def SerialWritePort(self, text, DexOrHex):
        if self.UseSer.isOpen and System.Serial_Tool_GlobalManager.Global_Get(self.UseGlobalVal, 'Serial_Open_Flag'):
            if DexOrHex == SerialWriteType.Hex:
                self.Send_Count = self.UseSer.write(text)  # 写数据
            else:
                self.Send_Count = self.UseSer.write(text.encode("gbk"))  # 写数据
        else:
            self.UseLog.NormalLog_Output(LogModule.SerModule, LogLevel.Level6, "SerialWritePort Serial not open!!!")

