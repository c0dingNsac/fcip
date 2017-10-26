import datetime, time, base64, urllib2, json, getpass, csv

cats = 'Y2hyaXN0aW5hZm9uY3JlZUB5YWhvby5jb20='  
dogs = 'Um9zYW5hMDczMA=='

def convert_coords(lat, longitude):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s" % (lat, longitude)
    headers = {
        'Content-Type': 'application/json',
    }
    request = urllib2.Request(url, None, headers)
    response = None
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        if e.code != 200:
            return "HTTP Error: %s" % e.code
        else:
            print e
            raise urllib2.HTTPError
    formatted_address = json.loads(response.read())["results"][0]["formatted_address"]
    return formatted_address.encode('ascii', 'ignore')

def play_sound(dev_id, token, dev_msg='Find My Device alert'):
    dsid = base64.b64decode(token).split(':')[0]
    try:
        int(dsid)
        auth_type = 'Forever'
    except ValueError:
        auth_type = 'UserIDGuest'

    url = 'https://fmipmobile.icloud.com/fmipservice/device/%s/playSound' % dsid
    headers = {
    'Accept':'*/*',
    'Authorization':'Basic %s' % token,
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'en-us',
    'Content-Type':'application/json; charset=utf-8',
    'X-Apple-AuthScheme':auth_type,
    }

    data = { 
        'device': dev_id, 
        'subject': dev_msg,
    }

    json_data = json.dumps(data)
    request = urllib2.Request(url, json_data, headers)
    request.get_method = lambda: "POST"

    response = urllib2.urlopen(request)
    response_content = response.read()
    if response_content:
        return True
    return False

def FMIP(username, password):
    i = 0
    try: #if we are given a FMIP token, change auth Type 
        int(username)
        auth_type = "Forever"
    except ValueError: #else apple id use useridguest
        auth_type = "UserIDGuest" 
    while True:
        i +=1
        if i == 2:
            print 'Reprocessing iCloud response...'
        url = 'https://fmipmobile.icloud.com/fmipservice/device/%s/initClient' % username
        headers = {
            'X-Apple-Realm-Support': '1.0',
            'Authorization': 'Basic %s' % base64.b64encode("%s:%s" % (username, password)),
            'X-Apple-Find-API-Ver': '3.0',
            'X-Apple-AuthScheme': '%s' % auth_type,
            'User-Agent': 'FindMyiPhone/500 CFNetwork/758.4.3 Darwin/15.5.0',
        }
        request = urllib2.Request(url, None, headers)
        request.get_method = lambda: "POST"
        try:
            response = urllib2.urlopen(request)
            z = json.loads(response.read())
        except urllib2.HTTPError as e:
            if e.code == 401:
                return "Authorization Error 401. Try credentials again."
            if e.code == 403:
                pass #can ignore
            raise e
        if i == 2: #loop twice / send request twice
            break
        print '\033[93mSuccessfully\033[0m authenticated'
        print 'Sent \033[92mlocation\033[0m beacon to \033[91m[%s]\033[0m devices' % len(z["content"])
        print 'Awaiting response from iCloud...'
        #okay, FMD request has been sent, now lets wait a bit for iCloud to get results, and then do again, and then break
        time.sleep(5)
    return_string = ''
    return_string += '\033[94m(%s %s | %s)\033[0m -> \033[92mFound %s Devices\033[0m\n-------\n' % (z["userInfo"]["firstName"], z["userInfo"]["lastName"], username, len(z["content"]))
    i = 1
    device_dict = {}
    for y in z["content"]:
        try:
            return_string += "Device [%s]\n" % i
            i += 1
            return_string += "\033[94mModel\033[0m: %s\n" % y["deviceDisplayName"]
            return_string += "\033[94mName\033[0m: %s\n" % y["name"]
            device_id = y["id"]
            device_dict[i - 1] = ['%s | %s' % (y["name"], y["deviceDisplayName"]) , y["id"]]
            time_stamp = y["location"]["timeStamp"] / 1000
            time_now = time.time()
            time_delta = time_now - time_stamp #time difference in seconds
            minutes, seconds = divmod(time_delta, 60) #great function, saves annoying maths
            hours, minutes = divmod(minutes, 60)
            time_stamp = datetime.datetime.fromtimestamp(time_stamp).strftime("%A, %B %d at %I:%M:%S")
            if hours > 0:
                time_stamp = "%s (%sh %sm %ss ago)" % (time_stamp, str(hours).split(".")[0], str(minutes).split(".")[0], str(seconds).split(".")[0])
            else:
                time_stamp = "%s (%sm %ss ago)" % (time_stamp, str(minutes).split(".")[0], str(seconds).split(".")[0])
            return_string += "\033[91mLatitude, Longitude\033[0m: <%s,%s>\n" % (y["location"]["latitude"], y["location"]["longitude"])
            street_address = convert_coords(y["location"]["latitude"], y["location"]["longitude"])
            return_string += "\033[91mStreet Address\033[0m: %s\n" % street_address
            return_string += "\033[93mBattery\033[0m: %s%% & %s\n" % (str(float(y["batteryLevel"]) * 100).split('.')[0], y["batteryStatus"])
            return_string += "\033[92mLocated at: %s\033[0m\n" % time_stamp
            return_string += "-------\n"
            if y["deviceDisplayName"] == "iPhone SE" :
                csv_write = ''
                csv_time_stamp = datetime.datetime.fromtimestamp(time_stamp).strftime("%x %X")  #("%B %d %I:%M:%S")
                csv_write = "%s;%s;%s;%s;%s;%s;%s%%;%s" % (i-1, time.strftime("%x %X", time.localtime(time.time())), csv_time_stamp, street_address, y["location"]["latitude"], y["location"]["longitude"], str(float(y["batteryLevel"]) * 100).split('.')[0], y["batteryStatus"])
        except TypeError,e :
            return_string += "\033[92mCould not get GPS lock!\033[0m\n-------\n"
    return return_string, device_dict, base64.b64encode("%s:%s" % (username, password)),csv_write

username = base64.b64decode(cats)
password = base64.b64decode(dogs)
response = FMIP(username, password)
if len(response) != 4:
    print response
    exit()
located_devices = response[0]
device_dict = response[1]
token = response[2]
csv_entry = response[3]
with open('fcip.csv', 'ab') as csvfile:
    # headers = ['id', 'time', 'dtg', 'lat', 'long', 'bat', 'batstat']
    # reader = csv.reader(csvfile, fieldnames=fieldnames)
    writer = csv.writer(csvfile, delimiter=';',lineterminator='\n')
    writer.writerow([str(csv_entry)])
    print located_devices
    print token
    print device_dict
