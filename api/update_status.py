import time
import json
import urllib.request


url = "https://nyzo.co/meshUpdate?s=0"
while True:
    try:

        data = urllib.request.urlopen(url).read().decode("utf-8")

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
