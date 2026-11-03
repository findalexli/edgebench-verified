calib start8
cpus 4; cat /sys/devices/system/cpu/online >>$O/summary.txt; cat $O/hotplug.err >>$O/summary.txt 2>/dev/null; calib start4
ev hot4 1 old fast 15
ev hot4 1 new fast 15
ev hot4 1 old st 200
ev q4 1 old fast 15
