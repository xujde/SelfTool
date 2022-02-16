::create 2/15/2022

set New_Name=SelfTool
::编译输出到文件夹，加速exe文件启动速度
pyinstaller -D -w .\main.py -n %New_Name%

::生成exe文件，运行期间无命令行窗口
::pyinstaller -F -w .\main.py -n %New_Name%

