::create 2/16/2022

set New_Name=Servers

pyinstaller -D -w .\main.py -n %New_Name%

md .\dist\%New_Name%\Logo_Picture\

copy .\Logo_Picture\* .\dist\%New_Name%\Logo_Picture\