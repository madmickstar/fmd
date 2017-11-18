FMD
==
'fmd' is a tool for tracking user's on a Cisco Wireless Network. Displaying the user's
RF signal, SSID and the WAP they are associated too. Optionally 'fmd' has the capability 
to light up the LED on the assocated WAP and or neighboring WAPs. This is why the program
is called Follow Me Disco ('FMD').

This tool can be used for site surveying, user tracking and having a bit of fun lighting
up WAPs and/or neighboring WAPs as a user roams around the wireless network.

FMD features
-----------------

* Tracks a user as they roam the wireless network
* Logs user's association details to console window
* Reports SSID, WAP Name, SNR, time/date, 
* Tracks multiple MAC addresses simultaneously
* Profiling, create and read MAC address profiles from JSON file
* Enables assocated WAP's disco LED
* Enables neighboring WAP's disco LEDs
* All features are all accessible from the convenience of a one liner
* Py2exe setup script provided with source code

Create Win32 EXE from source using py2exe
-----------------------------------------
1. Install python dependencies for fmd program
2. Change into source dir 
3. Create exe file using supplied py2exe script
   See [py2exe website for tutorial](http://www.py2exe.org/index.cgi/Tutorial)
4. Copy dist\fmd.exe and tcl DIR to location in window's system path


```
pip install -r requirements.txt
cd fmd
python setup_fmd_py2exe.py py2exe
cp dist\fmd.exe <windows\system\path>
xcopy dist\tcl <windows\system\path>\tcl /E /I
```


Usage
-----
`
fmd {-wlc xx.xx.xx.xx} ({xx:xx:xx:xx:xx:xx ...} | -p {PROFILE}) [ ( -sm | -dm ) | -mw {2..10} | -f {5, 10, 15, 20, 25, 30} | -m {1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 720} | -cv | -l | -t | -d | -h | --version ]
    
`

Argument  | Type   | Format               | Default           | Description
----------|--------|----------------------|-------------------|--------------------
-wlc {IP} | string | -wlc {xx.xx.xx.xx} | No default value | Wireless LAN Controller management IP
mac address | string | 12 hexadecimal characters in any MAC address format | No default value | Client MAC address to monitor, accepts multiple
-p [profile] | switch | -p [profile name] | disabled | Use profile from JSON file, if switch enabled with no profile set, default profile used from JSON file
-sm | switch | -dm | disabled | Enable site survey mode
-dm | switch | -dm | disabled | Enable disco mode
-mw {int} | switch | -mw {2..10} | 2 | Maximum WAPs to enable flashing LEDs, disco mode only
-f {secs} | switch | -f {5,10,15,20,25,30} | 5 | Frequency to update client location and details in seconds
-m {mins} | switch | -m {5,10,30,60,120,180,240,300,360,720} | 1 | Duration of monitoring client in minutes 
-cv | switch | -cv | disabled | Enable verbose console mode for SSH session
-l | switch | -h | disabled | Prints help to console
-t | switch | -h | disabled | Prints help to console
-d | switch | -d | disabled | Enables debug output to console
-h | switch | -h | disabled | Prints help to console   
--version | switch | --version | disabled | Displays version