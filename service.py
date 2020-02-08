import os
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
    print(f"Cloud Profiler Service - Running in Service mode.")
    while True:
        print("moo")
        exec(open("update-cloud-hosts.py").read())
        print(f"Cloud Profiler Service - Will now rest for {LoopInt} seconds, until the next refresh.")
        for i in progressbar.progressbar(range(LoopInt)):
            time.sleep(1)
        print("\n")
else:
    exec(open("update-cloud-hosts.py").read())


