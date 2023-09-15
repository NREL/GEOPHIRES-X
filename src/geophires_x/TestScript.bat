del diff_report_all.txt, Example*V3_diff.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example1.txt D:\Work\GEOPHIRES3-master\Example1V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example1V3.txt D:\Work\GEOPHIRES3-master\Results\Example1V3.txt > D:\Work\GEOPHIRES3-master\Example1V3_diff.txt
copy D:\Work\GEOPHIRES3-master\Example1V3_diff.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example2.txt D:\Work\GEOPHIRES3-master\Example2V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example2V3.txt D:\Work\GEOPHIRES3-master\Results\Example2V3.txt > D:\Work\GEOPHIRES3-master\Example2V3_diff.txt
copy /A /Y Example2V3_diff.txt + diff_report_all.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example3.txt D:\Work\GEOPHIRES3-master\Example3V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example3V3.txt D:\Work\GEOPHIRES3-master\Results\Example3V3.txt > D:\Work\GEOPHIRES3-master\Example3V3_diff.txt
copy /A /Y Example3V3_diff.txt + diff_report_all.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example4.txt D:\Work\GEOPHIRES3-master\Example4V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example4V3.txt D:\Work\GEOPHIRES3-master\Results\Example4V3.txt > D:\Work\GEOPHIRES3-master\Example4V3_diff.txt
copy /A /Y Example4V3_diff.txt + diff_report_all.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example5.txt D:\Work\GEOPHIRES3-master\Example5V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example5V3.txt D:\Work\GEOPHIRES3-master\Results\Example5V3.txt > D:\Work\GEOPHIRES3-master\Example5V3_diff.txt
copy /A /Y Example5V3_diff.txt + diff_report_all.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example8.txt D:\Work\GEOPHIRES3-master\Example8V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example8V3.txt D:\Work\GEOPHIRES3-master\Results\Example8V3.txt > D:\Work\GEOPHIRES3-master\Example8V3_diff.txt
copy /A /Y Example8V3_diff.txt + diff_report_all.txt diff_report_all.txt
python GEOPHIRESv3.py D:\Work\GEOPHIRES3-master\Examples\example9.txt D:\Work\GEOPHIRES3-master\Example9V3.txt
fc.exe /L /N /W D:\Work\GEOPHIRES3-master\Example9V3.txt D:\Work\GEOPHIRES3-master\Results\Example9V3.txt > D:\Work\GEOPHIRES3-master\Example9V3_diff.txt
copy /A /Y Example9V3_diff.txt + diff_report_all.txt diff_report_all.txt
