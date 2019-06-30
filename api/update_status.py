import time
import json
import urllib.request


url = "https://nyzo.co/meshUpdate?s=0"
balance_url = "https://www.nyzo.co/balanceListPlain/{}"
while True:
    try:
        data = urllib.request.urlopen(url).read().decode("utf-8")
        block_height = data.split(">Frozen edge: ")[1].split("<br>")[0]

        balance_data = urllib.request.urlopen(balance_url.format(block_height)).read().decode("utf-8")
        balance_data = balance_data.split("fee</p>")[1].split("</div><h2>")[0]
        balance_data = balance_data.split("</p>")[:-1]
        balances = {}
        for balance in balance_data:
            balance = balance.split("<p>")[1]
            while "  " in balance:
                balance = balance.replace("  ", " ")
            balance = balance.split(" ")
            short_id = balance[0][:4] + "." + balance[0][-4:]
            balances[short_id] = balance
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
            verifiers[a[0]] = [color_to_status[b[0]], c[0]]

        with open("status.json", "w") as f:
            json.dump(verifiers, f)
        time.sleep(30)
    except Exception as e:
        if Exception == KeyboardInterrupt:
            exit()
        print(e)
