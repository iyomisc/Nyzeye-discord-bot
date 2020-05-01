import json
import urllib.request
import psutil
from os import getpid
import sys

import time

# Make sure no previous instance is stuck
try:
    procs = [p for p in psutil.process_iter() if 'python' in p.name() and "update_status_cron.py" in p.cmdline()]
    for proc in procs:
        if proc.pid != getpid():
            proc.kill()
except:
    pass

url = "https://nyzo.co/cycleUpdate"
queue_url = "https://nyzo.co/queueUpdate/20000"
balance_url = "https://www.nyzo.co/balanceListPlain/{}"
start_time = time.time()

try:
    data = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
    
    print(time.time() - start_time)
    
    block_height = data.split(">Frozen edge: ")[1].split("<br>")[0]

    balance_data = urllib.request.urlopen(balance_url.format(block_height), timeout=30).read().decode("utf-8")
    
    print(time.time() - start_time)
    
    balance_data = balance_data.split("fee</p>")[1].split("</div><h2>")[0]
    balance_data = balance_data.split("</p>")[:-1]
    balances = {}
    for balance in balance_data:
        balance = balance.split("<p>")[1]
        while "  " in balance:
            balance = balance.replace("  ", " ")
        balance = balance.split(" ")
        short_id = balance[0][:4] + "." + balance[0][-4:]
        balance[1] = float(balance[1][1:])
        balances[short_id] = balance
    if len(balances) > 10:
        with open("balances.json", "w") as f:
            json.dump(balances, f)

    data = data.split('class="cycle-container">')[1]
    data = data.split("</div>")[0]
    data = data.split("&rarr;")

    color_to_status = {"color: #f88;": 3, "color: #ff0;": 2, "color: #fa0;": 1, "": 0, "color: #aea;": 0}

    verifiers = {}
    for line in data:
        line = line.replace("font-weight: bold;", "")
        a = line.split("id=")[1].split('" target="_blank" style="')
        b = a[1].split('">')
        c = b[1].split("</a>")
        verifiers[a[0]] = [color_to_status[b[0]], c[0], 1]
    
    print(time.time() - start_time)
    
    data = urllib.request.urlopen(queue_url, timeout=40).read().decode("utf-8")
    
    print(time.time() - start_time)
    

    data = data.split('"queue-container">')[1]
    data = data.split("</div>")[0]
    data = data.split(", ")

    for line in data:
        line = line.replace("font-weight: bold;", "")
        if "id=" not in line:
            continue
        a = line.split("id=")[1].split('" target="_blank" style="')
        b = a[1].split('">')
        c = b[1].split("</a>")
        verifiers[a[0]] = [color_to_status[b[0]], c[0], 0]
        #print(verifiers[a[0]])
    if len(verifiers) > 10:
        with open("status.json", "w") as f:
            json.dump(verifiers, f)
    
    print(time.time() - start_time)
    

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
