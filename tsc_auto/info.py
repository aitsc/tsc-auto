import os
import time

i = 0
while True:
    i += 1
    os.system('echo ' + '-'*20 + 'CPU' + '-'*20 + str(i))
    os.system('top -bn1|egrep "(%CPU)|([.].+:)"|grep -v root|grep -v " 0.0 "|head -11')
    os.system('~/anaconda3/envs/tf/bin/gpustat -cpu --color|grep :|head -11')
    os.system('/usr/bin/squeue|head -11')
    time.sleep(10)
    os.system('echo')