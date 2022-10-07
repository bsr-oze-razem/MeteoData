import requests, time as t, base64, json, numpy as np, struct
from datetime import datetime, timedelta
from colorama import Fore, init
init()



def get_token(login, password):
    auth = str(base64.b64encode(f"{login}:{password}".encode("utf-8")))[1:]
    headers = {"Authorization":f"Basic {auth}"}
    r = requests.get("https://login.meteomatics.com/api/v1/token", headers=headers)
    token = json.loads(r.text)["access_token"]
    return token


def get_data(time, units, latitude, longitude, token):
    url = f'https://api.meteomatics.com/{time_now}/{units}/{latitude},{longitude}/json?access_token={token}'
    r = requests.get(url)
    if r.text[:12] == "Unauthorized":
        return "Unauthorized"
    else:
        value = r.text
        value = value.split("value")[1][2:].split("}")[0]
        return float(value)
        

# def create_record(login, password, data_names, data, time, latitude, longitude, ip, port):
#     token = get_token(login, password)
#     for units in data_names:
#         value = get_data(time, units, latitude, longitude, token)
#         data[name.split(":")[0]] = value
#     r = requests.post(f"http://{ip}:{port}/weather", data=json.dumps(data))
#     return r, data

def create_record(settings, time_now):
    token = get_token(settings["login"], settings["password"])
    delta_x = abs(settings["coordinates"]["longitude"]["start"] - settings["coordinates"]["longitude"]["end"]) / settings["array"]["x"]
    delta_y = abs(settings["coordinates"]["latitude"]["start"] - settings["coordinates"]["latitude"]["end"]) / settings["array"]["y"]
    array = np.zeros([settings["array"]["y"], settings["array"]["x"], 3], dtype=float)
    for y in range(settings["array"]["y"]):
        for x in range(settings["array"]["x"]):
            value = get_data(time_now, settings["data_names"][0], settings["coordinates"]["latitude"]["start"] + delta_y*y, settings["coordinates"]["longitude"]["start"] + delta_x*x, token)
            array[y][x][0] = settings["coordinates"]["latitude"]["start"] + delta_y*y
            array[y][x][1] = settings["coordinates"]["longitude"]["start"] + delta_x*x
            array[y][x][2] = value
            
    ip = settings["ip"]
    port = settings["port"]
    data = json.dumps({"array": array.tolist()})
    r = requests.post(f"http://{ip}:{port}/weather", data=data)
    return r, array



with open("settings.json", "r") as f:
    settings = json.loads(f.read())


while True:
    time = (datetime.now() + timedelta(seconds=settings["time_offset"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_start = t.time()
    
    try:
        r, array = create_record(settings, time_now)
        # r = requests.get("https://google.com/")
    except:
        elapsed = round(t.time()-time_start, 2)
        time_stamp =datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{Fore.LIGHTBLACK_EX}{time_stamp}{Fore.RESET} Response:", f"{Fore.RED}Error!{Fore.RESET}  Elapsed: {Fore.BLUE}{elapsed}{Fore.RESET}")
    
        with open("log.log", "a") as f:
            f.write(f"{time_stamp} Response: Error!  Elapsed: {elapsed}\n")
        t.sleep(settings["delay_s"])
        continue
    
    elapsed = round(t.time()-time_start, 2)
    time_stamp =datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{Fore.LIGHTBLACK_EX}{time_stamp}{Fore.RESET} Response:", f"{Fore.GREEN if r.status_code >= 200 and r.status_code <= 299 else Fore.RED}{r.status_code}{Fore.RESET}  Elapsed: {Fore.BLUE}{elapsed}{Fore.RESET}")
    
    with open("log.log", "a") as f:
        f.write(f"{time_stamp} Response: {r.status_code}  Elapsed: {elapsed}\n")
    
    t.sleep(settings["delay_s"])