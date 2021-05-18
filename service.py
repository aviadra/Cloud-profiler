import os
import subprocess
import time

import progressbar

if os.environ.get('CP_LoopInterval', False):
    CP_LoopInterval = os.environ['CP_LoopInterval']
    print(f"Clour Profiler Service - Found CP_LoopInterval set to: {CP_LoopInterval}, and using it as the refresh interval.")
    LoopInt = int(CP_LoopInterval)
else:
    LoopInt = 300 #Default value of 5 minutes

#Convert count to minutes
LoopInt = LoopInt

if os.environ.get('CP_Service', False):
    os.environ['HOME'] = '/home/appuser'
    print(f"Cloud_Profiler Service - Running in Service mode.")
    while True:
        print("Clour Profiler Service - Start of loop")
        exec(open("update-cloud-hosts.py").read())
        print(f"Cloud_Profiler Service - Will now rest for {LoopInt} seconds, until the next refresh.")
        for i in progressbar.progressbar(range(LoopInt)):
            time.sleep(1)
            if os.path.exists("cut.tmp"):
                os.remove("cut.tmp")
                print("Clour Profiler Service - Found the reset counter file, so exiting the rest loop.")
                break
        print("\n")
else:
    exec(open("update-cloud-hosts.py").read())


