NAVSTAT
=======

NAVSTAT is being constructed as a simple yet effective navigation station for marine applications.
It is important to realize that it is not being made to replace a full chartplotter, but rather 
provides a set of tools that will enable easy access and visualization of important navigational 
information. Full NMEA0183 sentence/device compatibility is one of the goals.This project is still
in its infancy and as such, has a limited feature set at the moment.

REQUIREMENTS
------------
NAVSTAT requires the following:
- PyGame - http://www.pygame.org
- PySerial - http://pyserial.sourceforge.net/
- Serial or USB/Serial GPS device

These libraries can be installed from their websites or with the following command: 
sudo apt-get install python-serial python-pygame

HOW TO USE
----------
The GPS connection requires a serial connection. Ensure your device opens this connection.

Run NAVSTAT by opening the NAVSTAT.py file with your favourite python editor. Run the script.

Important hotkey info:
SPACE - changes NAVSTAT from Night Mode to default colors (Night mode is on by default right now).
TAB - Switches between fullscreen and Mini Mode (Mini mode is on by default right now).
T - Toggles tracking on and off (Tracking is on by default right now).
ESCAPE - Quits NAVSTAT
