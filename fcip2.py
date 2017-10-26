import datetime, time, base64, urllib2, json, getpass, csv, webbrowser, sys, gmplot
# from geopy.geocoders import Nominatim

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
        # print '\033[93mSuccessfully\033[0m authenticated'
        # print 'Sent \033[92mlocation\033[0m beacon to \033[91m[%s]\033[0m devices' % len(z["content"])
        # print 'Awaiting response from iCloud...'
        #okay, FMD request has been sent, now lets wait a bit for iCloud to get results, and then do again, and then break
        time.sleep(5)
    return_string = ''
    # return_string += '\033[92mConfirmed %s Devices\033[0m\n-------\n' % (len(z["content"]))
    i = 1
    device_dict = {}
    global csv_newline, street_address, map_link, screen_output
    for y in z["content"]:
        try:
            # return_string += "Device [%s]\n" % i
            i += 1
            # return_string += "\033[94mModel\033[0m: %s\n" % y["deviceDisplayName"]
            # return_string += "\033[94mName\033[0m: %s\n" % y["name"]
            device_id = y["id"]
            device_dict[i - 1] = ['%s | %s' % (y["name"], y["deviceDisplayName"]) , y["id"]]
            time_stamp = y["location"]["timeStamp"] / 1000
            time_now = time.time()
            list_time = time.strftime("%H:%M", time.localtime(time.time()))
            time_delta = time_now - time_stamp #time difference in seconds
            minutes, seconds = divmod(time_delta, 60) #great function, saves annoying maths
            hours, minutes = divmod(minutes, 60)
            time_stamp = datetime.datetime.fromtimestamp(time_stamp).strftime("%x %X")  #("%B %d %I:%M:%S")
            maplat = y["location"]["latitude"]
            maplong = y["location"]["longitude"]
            street_address = "%s" % convert_coords(maplat,maplong)
            map_link = "https://www.google.com/maps/place/"+"%s,%s" % (maplat, maplong)
            # Check time difference (more than an hour use HH:MM:SS; less use MM:SS)
            # if hours > 0:
            #     time_stamp = "%s (%sh %sm %ss ago)" % (time_stamp, str(hours).split(".")[0], str(minutes).split(".")[0], str(seconds).split(".")[0])
            # else:
            #     time_stamp = "%s (%sm %ss ago)" % (time_stamp, str(minutes).split(".")[0], str(seconds).split(".")[0])
            if y["deviceDisplayName"] == "iPhone SE" :
                gmap = gmplot.GoogleMapPlotter(maplat,maplong, 16)
                gmap.plot(maplat,maplong, 'cornflowerblue', edge_width=10)
                # gmap.scatter(more_lats, more_lngs, '#3B0B39', size=40, marker=False)
                # gmap.scatter(marker_lats, marker_lngs, 'k', marker=True)
                # gmap.heatmap(heat_lats, heat_lngs)
                gmap.draw('map.html')
                screen_output = "%s  \033[91m%s\033[0m\t%s%%(%s) %s" % (time_stamp,street_address,str(float(y["batteryLevel"]) * 100).split('.')[0], y["batteryStatus"], map_link)
                return_string = "%s;%s;%s;%s;%s;%s;%s%%;%s" % (i-1, time.strftime("%x %X", time.localtime(time.time())), time_stamp, street_address, maplat, maplong, str(float(y["batteryLevel"]) * 100).split('.')[0], y["batteryStatus"])
                csv_newline = return_string
            else :
                return_string = "%s,%s,%s,0,0,0,0\n" % (i-1,time.strftime("%x %X", time.localtime(time.time())),time_stamp)
                screen_output = "%s %s %s%%(%s) %s" % (time_stamp,map_link,str(float(y["batteryLevel"]) * 100).split('.')[0], y["batteryStatus"])
        except TypeError,e :
            return_string += "\033[92mCould not get GPS lock!\033[0m"
    return return_string, screen_output, csv_newline, device_dict, base64.b64encode("%s:%s" % (username, password))
    # return return_string, gm_url, term_display, csv_newline, device_dict, base64.b64encode("%s:%s" % (username, password))

username = base64.b64decode(cats)
password = base64.b64decode(dogs)
numTimesToRepeat = int(raw_input("How many times should this run? "))
if numTimesToRepeat != 1:
    lengthToSleep = int(raw_input("How many seconds between each? "))
    timeRemaining = lengthToSleep
with open('fcip.csv', 'ab') as csvfile:
    # headers = ['id', 'time', 'dtg', 'lat', 'long', 'bat', 'batstat']
    # reader = csv.reader(csvfile, fieldnames=fieldnames)
    writer = csv.writer(csvfile, delimiter=';',lineterminator='\n')
    while True:
        response = FMIP(username, password)
        if len(response) != 5:
            print response
            exit()
        located_devices = response[0]
        terminal = response[1]
        csv_entry = response[2]
        device_dict = response[3]
        token = response[4]
        # print response
        # print located_devices
        # print device_dict
        # print token
        print terminal
        writer.writerow([str(csv_entry)])
        csvfile.close()
        # print csv_entry
        numTimesToRepeat -= 1         # repeat one less time because we just did it
        if numTimesToRepeat==0:       # do we repeat again?
            print "Finished\n========\n"
            csvfile.close()
            break                     #   no -> done!
        else:
            if numTimesToRepeat==1:    
                print "LAST LOOP"
                timeRemaining = lengthToSleep
            else:
                timeRemaining = lengthToSleep
                print "%s loops remaining." % numTimesToRepeat
            start_pause = datetime.datetime.now()
            while (datetime.datetime.now()-start_pause).seconds < lengthToSleep:
                timeRemaining -= 1
                b = " Time remaining: " + str(timeRemaining)
                time.sleep(1)
                sys.stdout.write(str(b)+'                 \r')
                sys.stdout.flush()
            # time.sleep(lengthToSleep) #   yes -> sleep before repeating