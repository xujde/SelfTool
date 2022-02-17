::create 2/15/2022

set New_Name=Serial_Tool
::编译输出到文件夹，加速exe文件启动速度
pyinstaller -D -w .\main.py -n %New_Name%
::pyinstaller -D .\main.py -n %New_Name%

::生成exe文件，运行期间无命令行窗口
::pyinstaller -F -w .\main.py -n %New_Name%

echo New_Name is %New_Name%

::创建文件夹
md .\dist\%New_Name%\Logo_Picture\
::复制文件夹下所有文件
copy .\Logo_Picture\* .\dist\%New_Name%\Logo_Picture\

