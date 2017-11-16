FMD
==
'fmd' is a tool for tracking user's on a Cisco Wireless Network. Displaying the user's
RF signal, SSID and he WAP they are associated too. Optionally 'fmd' has the capability 
to light up the LED on the user's assocated WAP and or neighboring WAPs the user is 
associated too. This is why I named it Follow Me Disco 'fmd'.

This tool can be used for site surveying, user tracking and having a bit of fun lighting
up WAP or neighboring WAPs a user roams around the wireless network.

FMD features
-----------------

* Tracks a user as they roam the wireless network
* Logs user's association details to console window
* Reports SSID, WAP Name, SNR, time/date, 
* Tracks multiple MAC addresses simultaneously
* Create and read MAC address profiles in JSON format
* Enables assocated WAP's flashing LED
* Enables assocated WAP's neighboring WAP's LEDs
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
fmd [-h] [-p [PROFILE]] [-wlc {ip address xx.xx.xx.xx}]
    [-f {5, 10, 15, 20, 25, 30}]
    [-m {1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 720}] [-mw {2..10}]
    [-dm | -sm] [-cv] [-l] [-t] [-d] [--version]
    [{MAC Address xx:xx:xx:xx:xx:xx} [{MAC Address xx:xx:xx:xx:xx:xx} ...]]
`