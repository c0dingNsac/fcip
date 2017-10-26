play_sound_ask = raw_input('Would you like to play a sound? (Y/n): ')
if play_sound_ask.lower() != 'y':
    print 'Sound not requested. Exiting'
    exit()

print '-------'
for dev in device_dict:
    print "\033[94mDevice\033[0m [%s] - [\033[92m%s\033[0m]" % (dev, device_dict[dev][0])
print '-------'

print 'Which above device would you like to play a \033[93msound\033[0m for?\n\033[91mWARNING\033[0m, this will send the \033[94miCloud\033[0m user an \033[91memail\033[0m.'
dev_sound = input('Enter a device number [1-%s]: ' % len(device_dict))
dev_msg = raw_input('Enter a message to be displayed: ')
device_id = device_dict[dev_sound][1]
if play_sound(device_id, token, dev_msg):
    print 'Successfully played a sound on [%s]' % device_dict[dev_sound][0]
else:
    print 'Error playing sound on [%s]' % device_dict[dev_sound][0]
    
    Skip to content
Features
Business
Explore
Marketplace
Pricing
This repository
Search
Sign in or Sign up
 Watch 17  Star 45  Fork 26 albeebe/PHP-FindMyiPhone
 Code  Issues 10  Pull requests 2  Projects 0  Insights
Branch: master Find file Copy pathPHP-FindMyiPhone/class.findmyiphone.php
17cba71  on Jan 12
@beinnlora beinnlora Removed unused variables
2 contributors @beinnlora @albeebe
RawBlameHistory     
320 lines (297 sloc)  11.6 KB
<?PHP
/*
 Copyright (C) Alan Beebe (alan.beebe@gmail.com).
 
 Licensed under the Apache License, Version 2.0 (the "License");
 
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
 http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
  v1.0 - January 2, 2015
  
*/
 
class FindMyiPhone {
	private $client = array(
						"app-version" => "4.0",
						"user-agent" => "FindMyiPhone/472.1 CFNetwork/711.1.12 Darwin/14.0.0",
						"headers" => array(
							"X-Apple-Realm-Support" => "1.0",
							"X-Apple-Find-API-Ver" => "3.0",
							"X-Apple-AuthScheme" => "UserIdGuest"
						)
					  );
	private $debug;
	private $username;
	private $password;
	public $devices = array();
	
	/**
     * This is where you initialize FindMyiPhone with your iCloud credentials
     * Example: $fmi = new FindMyiPhone("you@example.com", "MyPassWord123");
     *
     * @param username	iCloud username
     * @param password	iCloud password
     * @param debug		(Optional) Set to TRUE and all the API requests and responses will be printed out
     * @return          FindMyiPhone instance 
     */
	public function __construct($username, $password, $debug = false) {
		$this->username = $username;
		$this->password = $password;
		$this->debug = $debug;
		$this->authenticate();
	}
	
	/**
     * This method attempts to get the most current location of a device
     * Example: $fmi->locate("dCsaBcqBOdnNop4wvy2VfIk8+HlQ/DRuqrmiwpsLdLTuiCORQDJ9eHYVQSUzmWV", 30);
     *
     * @param deviceID	ID of the device you want to locate
     * @param timeout	(Optional) Maximum number of seconds to spend trying to locate the device
     * @return          FindMyiPhoneLocation object 
     */
	public function locate($deviceID, $timeout = 60) {
		$startTime = time();
		$initialTimestamp = $this->devices[$deviceID]->location->timestamp;
		while ($initialTimestamp == $this->devices[$deviceID]->location->timestamp) {
			if ((time() - $startTime) > $timeout) break;
			
			
			
			$this->refreshDevices($deviceID);
			sleep(5);
		}
		return $this->devices[$deviceID]->location;
	}
	
	/**
     * Play a sound and display a message on a device
     * Example: $fmi->playSound("dCsaBcqBOdnNop4wvy2VfIk8+HlQ/DRuqrmiwpsLdLTuiCORQDJ9eHYVQSUzmWV", "Whats up?");
     *
     * @param deviceID	ID of the device you want to play a sound
     * @param message	Message you want displayed on the device
     */
	public function playSound($deviceID, $message) {
		$url = "https://fmipmobile.icloud.com/fmipservice/device/".$this->username."/playSound";
		$body = json_encode(array("device"=>$deviceID, "subject"=>$message)); 
		list($headers, $body) = $this->curlPOST($url, $body, $this->username.":".$this->password);
	}
	
	/**
     * Put a device into lost mode. The device will immediately lock until the user enters the correct passcode
     * Example: $fmi->lostMode("dCsaBcqBOdnNop4wvy2VfIk8+HlQ/DRuqrmiwpsLdLTuiCORQDJ9eHYVQSUzmWV", "You got locked out", "555-555-5555");
     *
     * @param deviceID		ID of the device you want to lock
     * @param message		Message you want displayed on the device
     * @param phoneNumber	(Optional) Phone number you want displayed on the lock screen
     */
	public function lostMode($deviceID, $message, $phoneNumber = "") {
		$url = "https://fmipmobile.icloud.com/fmipservice/device/".$this->username."/lostDevice";
		$body = json_encode(array("device"=>$deviceID, "ownerNbr"=>$phoneNumber, "text"=>$message, "lostModeEnabled"=>true)); 
		list($headers, $body) = $this->curlPOST($url, $body, $this->username.":".$this->password);
	}
	
	/**
     * Print all the available information for every device on the users account.
     * This is really useful when you want to get the ID for a device.
     * Example: $fmi->printDevices();
     */
	public function printDevices() {
		if (sizeof($this->devices) == 0) $this->getDevices();
		print <<<TABLEHEADER
        		<PRE>
        		<TABLE BORDER="1" CELLPADDING="3">
        			<TR>
        				<TD VALIGN="top"><B>ID</B></TD>
        				<TD VALIGN="top"><B>name</B></TD>
        				<TD VALIGN="top"><B>displayName</B></TD>
        				<TD VALIGN="top"><B>location</B></TD>
        				<TD VALIGN="top"><B>class</B></TD>
        				<TD VALIGN="top"><B>model</B></TD>
        				<TD VALIGN="top"><B>modelDisplayName</B></TD>
        				<TD VALIGN="top"><B>batteryLevel</B></TD>
        				<TD VALIGN="top"><B>batteryStatus</B></TD>
        			</TR>
TABLEHEADER;
		foreach ($this->devices as $device) {
			$location = <<<LOCATION
			<TABLE BORDER="1">
				<TR>
					<TD VALIGN="top">timestamp</TD>
					<TD VALIGN="top">{$device->location->timestamp}</TD>
				</TR>
				<TR>
					<TD VALIGN="top">horizontalAccuracy</TD>
					<TD VALIGN="top">{$device->location->horizontalAccuracy}</TD>
				</TR>
				<TR>
					<TD VALIGN="top">positionType</TD>
					<TD VALIGN="top">{$device->location->positionType}</TD>
				</TR>
				<TR>
					<TD VALIGN="top">longitude</TD>
					<TD VALIGN="top">{$device->location->longitude}</TD>
				</TR>
				<TR>
					<TD VALIGN="top">latitude</TD>
					<TD VALIGN="top">{$device->location->latitude}</TD>
				</TR>
			</TABLE>
LOCATION;
			print <<<DEVICE
					<TR>
        				<TD VALIGN="top">{$device->ID}</TD>
        				<TD VALIGN="top">{$device->name}</TD>
        				<TD VALIGN="top">{$device->displayName}</TD>
        				<TD VALIGN="top">$location</TD>
        				<TD VALIGN="top">{$device->class}</TD>
        				<TD VALIGN="top">{$device->model}</TD>
        				<TD VALIGN="top">{$device->modelDisplayName}</TD>
        				<TD VALIGN="top">{$device->batteryLevel}</TD>
        				<TD VALIGN="top">{$device->batteryStatus}</TD>
        			</TR>
DEVICE;
		}
		print <<<TABLEFOOTER
        		</TABLE>
        		</PRE>
TABLEFOOTER;
	}
	
	/**
	 *  This is where the users credentials are authenticated.
	 *  The Apple_MMe_Host and Apple_MMe_Scope values are saved and used to generate the URL for all subsequent API calls
	 */
	private function authenticate() {
		$url = "https://fmipmobile.icloud.com/fmipservice/device/".$this->username."/initClient";
		list($headers, $body) = $this->curlPOST($url, "", $this->username.":".$this->password);
		
		if ($headers["http_code"] == 401) {
			throw new Exception('Your iCloud username and/or password are invalid');
		}
	}
	
	/**
     * This is where all the devices are downloaded and processed
     * Example: print_r($fmi->devices)
     */
	private function getDevices() {
		$url = "https://fmipmobile.icloud.com/fmipservice/device/".$this->username."/initClient";
		list($headers, $body) = $this->curlPOST($url, "", $this->username.":".$this->password);
		$this->devices = array();
		for ($x = 0; $x < sizeof($body["content"]); $x++) {
			$device = $this->generateDevice($body["content"][$x]);
			$this->devices[$device->ID] = $device;
		}
	}
	
	/**
	 * This method takes the raw device details from the API and converts it to a FindMyiPhoneDevice object
	 */
	private function generateDevice($deviceDetails) {
		$device = new FindMyiPhoneDevice();	
		$device->API = $deviceDetails;
		$device->ID = $device->API["id"];
		$device->batteryLevel = $device->API["batteryLevel"];
		$device->batteryStatus = $device->API["batteryStatus"];
		$device->class = $device->API["deviceClass"];
		$device->displayName = $device->API["deviceDisplayName"];
		$device->location = new FindMyiPhoneLocation();
		$device->location->timestamp = $device->API["location"]["timeStamp"];
		$device->location->horizontalAccuracy = $device->API["location"]["horizontalAccuracy"];
		$device->location->positionType = $device->API["location"]["positionType"];
		$device->location->longitude = $device->API["location"]["longitude"];
		$device->location->latitude = $device->API["location"]["latitude"];
		$device->model = $device->API["rawDeviceModel"];
		$device->modelDisplayName = $device->API["modelDisplayName"];
		$device->name = $device->API["name"];
		return $device;
	}
	
	/**
	 * This method refreshes the list of devices on the users iCloud account
	 */
	private function refreshDevices($deviceID = "") {
		$url = "https://fmipmobile.icloud.com/fmipservice/device/".$this->username."/refreshClient";
		if (strlen($deviceID) > 0) {
			$body = json_encode(array("clientContext"=>array("appVersion"=>$this->client["app-version"], "shouldLocate"=>true, "selectedDevice"=>$deviceID, "fmly"=>true)));
		}
		list($headers, $body) = $this->curlPOST($url, $body, $this->username.":".$this->password);
		$this->devices = array();
		for ($x = 0; $x < sizeof($body["content"]); $x++) {
			$device = $this->generateDevice($body["content"][$x]);
			$this->devices[$device->ID] = $device;
		}
	}
	
	/**
	 * Helper method for making POST requests
	 */
	private function curlPOST($url, $body, $authentication = "") {
		$ch = curl_init($url);                                                                      
		curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");                                                                     
		curl_setopt($ch, CURLOPT_POSTFIELDS, $body);                                                                  
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
		curl_setopt($ch, CURLOPT_VERBOSE, 1);
		curl_setopt($ch, CURLOPT_HEADER, 1);
		curl_setopt($ch, CURLOPT_USERAGENT, $this->client["user-agent"]);
		if (strlen($authentication) > 0) {
			curl_setopt($ch, CURLOPT_USERPWD, $authentication);  
		}
		$arrHeaders = array();
		$arrHeaders["Content-Length"] = strlen($request);
		foreach ($this->client["headers"] as $key=>$value) {
			array_push($arrHeaders, $key.": ".$value);
		}
		curl_setopt($ch, CURLOPT_HTTPHEADER, $arrHeaders);
		$response = curl_exec($ch);
		$info = curl_getinfo($ch);
		$header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
		$responseBody = substr($response, $header_size);
		$headers = array();
		foreach (explode("\r\n", substr($response, 0, $header_size)) as $i => $line) {
			if ($i === 0)
            	$headers['http_code'] = $info["http_code"];
			else {
            	list ($key, $value) = explode(': ', $line);
            	if (strlen($key) > 0)
	            	$headers[$key] = $value;
			}
        }
        if ($this->debug) {
        	$debugURL = htmlentities($url);
        	$debugRequestBody = htmlentities(print_r(json_decode($body, true), true));
        	$debugHeaders = htmlentities(print_r($headers, true));
        	$debugResponseBody = htmlentities(print_r(json_decode($responseBody, true), true));
        	print <<<HTML
        		<PRE>
        		<TABLE BORDER="1" CELLPADDING="3">
        			<TR>
        				<TD VALIGN="top"><B>URL</B></TD>
        				<TD VALIGN="top">$debugURL</TD>
        			</TR>
        			<TR>
        				<TD VALIGN="top"><B>Request Body</B></TD>
        				<TD VALIGN="top"><PRE>$debugRequestBody</PRE></TD>
        			</TR>
        			<TR>
        				<TD VALIGN="top"><B>Response Headers</B></TD>
        				<TD VALIGN="top"><PRE>$debugHeaders</PRE></TD>
        			</TR>
        			<TR>
        				<TD VALIGN="top"><B>Response Body</B></TD>
        				<TD VALIGN="top"><PRE>$debugResponseBody</PRE></TD>
        			</TR>
        		</TABLE>
        		</PRE>
HTML;
        }
		return array($headers, json_decode($responseBody, true));
	}
}
class FindMyiPhoneDevice {
	public $ID;
	public $batteryLevel;
	public $batteryStatus;
	public $class;
	public $displayName;
	public $location;
	public $model;
	public $modelDisplayName;
	public $name;
	public $API;
}
class FindMyiPhoneLocation {
	public $timestamp;
	public $horizontalAccuracy;
	public $positionType;
	public $longitude;
	public $latitude;
}
© 2017 GitHub, Inc.
Terms
Privacy
Security
Status
Help
Contact GitHub
API
Training
Shop
Blog
About





{u'serverContext': {
    u'authToken': u'AQAAAABZ6xZ0JGsEMRSPRJq8NIsdoRaAHFUUE54~', 
    u'maxLocatingTime': 90000, 
    u'deviceLoadStatus': u'200', 
    u'imageBaseUrl': u'https://statici.icloud.com', 
    u'minTrackLocThresholdInMts': 100, 
    u'lastSessionExtensionTime': None, 
    u'clientId': u'ZGV2aWNlXzEwODM4OTc5NjhfMTUwODU3ODkzMjQyMA==', 
    u'enable2FAFamilyRemove': False, 
    u'minCallbackIntervalInMS': 5000, 
    u'timezone': {
        u'previousOffset': -28800000, 
        u'currentOffset': -25200000, 
        u'previousTransition': 1489312799999, 
        u'tzCurrentName': u'-07:00', 
        u'tzName': u'America/Los_Angeles'
        }, 
    u'serverTimestamp': 1508578932433, 
    u'macCount': 0, 
    u'validRegion': True, 
    u'sessionLifespan': 900000, 
    u'preferredLanguage': u'en-us', 
    u'maxDeviceLoadTime': 60000, 
    u'cloudUser': True, 
    u'classicUser': False, 
    u'prefsUpdateTime': 1411588837619, 
    u'prsId': 1083897968, 
    u'showSllNow': False, 
    u'useAuthWidget': True, 
    u'enableMapStats': True, 
    u'trackInfoCacheDurationInSecs': 86400, 
    u'enable2FAErase': False, 
    u'info': u'S0l+fL7w2GBkSP5Fvnst7L+ltRENiXJb00aHsUbAfkp8BVeG6DOlVpMxnEQaeY8/', 
    u'enable2FAFamilyActions': False, 
    u'isHSA': True, 
    u'maxCallbackIntervalInMS': 60000, 
    u'callbackIntervalInMS': 2000
    }, 
u'alert': None, 
u'content': [
    {
        u'features': {
            u'LOC': True, 
            u'LKL': False, 
            u'LKM': False, 
            u'REM': False, 
            u'MSG': True, 
            u'PIN': False, 
            u'LST': True, 
            u'SPN': False, 
            u'LLC': False, 
            u'TEU': True, 
            u'XRM': False, 
            u'CLK': False, 
            u'CWP': False, 
            u'KPD': False, 
            u'CLT': False, 
            u'WMG': True, 
            u'SVP': False, 
            u'SND': True, 
            u'KEY': False, 
            u'WIP': True, 
            u'MCS': False, 
            u'LCK': True, 
            u'LMG': False
            }, 
        u'maxMsgChar': 160, 
        u'darkWake': False, 
        u'fmlyShare': False, 
        u'deviceStatus': u'200', 
        u'remoteLock': None, 
        u'activationLocked': True, 
        u'audioChannels': [], 
        u'deviceClass': u'iPhone', 
        u'id': u'ENsh1KUVIZkLm9E3gxUK5VSL+PTenGzJHsycUA+5wf/9aT996S6V++HYVNSUzmWV', 
        u'deviceModel': u'iphoneSE-c8caca-e5bdb5', 
        u'rawDeviceModel': u'iPhone8,4', 
        u'passcodeLength': 6, 
        u'canWipeAfterLock': True, 
        u'trackingInfo': None, 
        u'location': {
            u'locationType': u'', 
            u'altitude': 0.0, 
            u'locationFinished': True, 
            u'longitude': -121.27066028315691, 
            u'positionType': u'GPS', 
            u'floorLevel': 0, 
            u'timeStamp': 1508578905304, 
            u'latitude': 38.65434609357142, 
            u'isOld': False, 
            u'isInaccurate': False, 
            u'verticalAccuracy': 0.0, 
            u'horizontalAccuracy': 10.0
            }, 
        u'msg': {
            u'userText': True, 
            u'vibrate': False, 
            u'createTimestamp': 1480978954415, 
            u'strobe': False, 
            u'playSound': False, 
            u'statusCode': u'200'
            }, 
        u'batteryLevel': 0.30000001192092896, 
        u'remoteWipe': None, 
        u'thisDevice': False, 
        u'snd': None, 
        u'prsId': None, 
        u'wipeInProgress': False, 
        u'lowPowerMode': False, 
        u'lostModeEnabled': False, 
        u'isLocating': True, 
        u'lostModeCapable': True, 
        u'mesg': {
            u'createTimestamp': 1480978954415, 
            u'statusCode': u'200'
            }, 
        u'name': u' iPhone', 
        u'batteryStatus': u'NotCharging', 
        u'lockedTimestamp': None, 
        u'lostTimestamp': u'', 
        u'locationCapable': True, 
        u'deviceDisplayName': u'iPhone SE', 
        u'lostDevice': None, 
        u'deviceColor': u'c8caca-e5bdb5', 
        u'wipedTimestamp': None, 
        u'modelDisplayName': u'iPhone', 
        u'locationEnabled': True, 
        u'isMac': False, 
        u'locFoundEnabled': False
        }, 

    {
        u'features': {
            u'LOC': True, 
            u'LKL': False, 
            u'LKM': False, 
            u'REM': True, 
            u'MSG': True, 
            u'PIN': False, 
            u'LST': True, 
            u'SPN': False, 
            u'LLC': False, 
            u'TEU': True, 
            u'XRM': False, 
            u'CLK': False, 
            u'CWP': False, 
            u'KPD': False, 
            u'CLT': False, 
            u'WMG': True, 
            u'SVP': False, 
            u'SND': True, 
            u'KEY': False, 
            u'WIP': True, 
            u'MCS': False, 
            u'LCK': True, 
            u'LMG': False
            }, 
        u'maxMsgChar': 160, 
        u'darkWake': False, 
        u'fmlyShare': False, 
        u'deviceStatus': u'201', 
        u'remoteLock': None, 
        u'activationLocked': True, 
        u'audioChannels': [], 
        u'deviceClass': u'iPad', 
        u'id': u'S100NJn54mbeOQ6pET729fIHhL/LHZY9OSaKQbdmKiv6duLe88kpAuHYVNSUzmWV', 
        u'deviceModel': u'SecondGen', 
        u'rawDeviceModel': u'iPad2,1', 
        u'passcodeLength': 6, 
        u'canWipeAfterLock': True, 
        u'trackingInfo': None, 
        u'location': {
            u'locationType': None, 
            u'altitude': 0.0, 
            u'locationFinished': False, 
            u'longitude': -121.5017065770831, 
            u'positionType': u'Wifi', 
            u'floorLevel': 0, 
            u'timeStamp': 1508578647364, 
            u'latitude': 38.63067441197841, 
            u'isOld': False, 
            u'isInaccurate': False, 
            u'verticalAccuracy': 0.0, 
            u'horizontalAccuracy': 65.0
            }, 
        u'msg': None, 
        u'batteryLevel': 0.83, 
        u'remoteWipe': None, 
        u'thisDevice': False, 
        u'snd': None, 
        u'prsId': None, 
        u'wipeInProgress': False, 
        u'lowPowerMode': False, 
        u'lostModeEnabled': False, 
        u'isLocating': True, 
        u'lostModeCapable': True, 
        u'mesg': None, 
        u'name': u'cfoncree\u2019s iPad', 
        u'batteryStatus': u'NotCharging', 
        u'lockedTimestamp': None, 
        u'lostTimestamp': u'', 
        u'locationCapable': True, 
        u'deviceDisplayName': u'iPad 2', 
        u'lostDevice': None, 
        u'deviceColor': None, 
        u'wipedTimestamp': None, 
        u'modelDisplayName': u'iPad', 
        u'locationEnabled': True, 
        u'isMac': False, 
        u'locFoundEnabled': False
        }
    ], 

u'userInfo': {
    u'accountFormatter': 0, 
    u'hasMembers': False, 
    u'membersInfo': None, 
    u'firstName': u'Christina', 
    u'lastName': u'Foncree'
    }, 
u'userPreferences': {
    u'touchPrefs': {}
    }, 
u'statusCode': u'200'   
}
