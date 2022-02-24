::create 2/15/2022

set New_Name=Serial_Tool

echo New_Name is %New_Name%

pyinstaller -D -w .\main.py -n %New_Name%
@REM pyinstaller -D .\main.py -n %New_Name%

md .\dist\%New_Name%\Logo_Picture\

copy .\Logo_Picture\* .\dist\%New_Name%\Logo_Picture\

