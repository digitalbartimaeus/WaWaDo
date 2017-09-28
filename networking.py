# coding=utf-8+
# !/usr/bin/env python3

import threading
from scapy.all import sniff, ARP
import time
import os
import logging
import traceback
import subprocess


class NetworkScanner:
    def __init__(self, file):
        """
        Constructor for Network SCanner
        :param file: Path to configuration file (absolute or relative path possible)
        """
        self.hostfile = ""
        self.sethostfile(file)
        self.iplist = [[ip, 0] for ip in self.__getipfromhostfile()]  # Get IPs, which shall be monitored
        return

    @staticmethod
    def ping(ip, timeout=1):
        """
        Ping one single IP address
        :param ip: address to be pinged
        :param timeout: timeout given in seconds
        :return: 1 if device is online, 0 if it is not
        """
        if os.name == 'nt':  # check if programm is running on Windows system
            return not os.system('ping {0} -n 1'.format(ip))
        elif os.name == 'posix':  # programm is running on linux
            try:
                subprocess.run(["ping", "-c 1", ip], timeout=timeout, check=True, stdout=subprocess.DEVNULL)
                return 1
            except subprocess.TimeoutExpired:  # host did not respond to ICMP ping request
                return 0

    def __getipfromhostfile(self):
        """
        load ip addresses given in configuration file
        :return: list ost ip addresses
        """
        with open(self.hostfile) as f:
            hosts = f.readlines()
        return [x.strip() for x in hosts]  # removing white space from line and store in list

    def pinghostlist(self, timeout=1):
        """
        Ping all hosts given in configuration file
        :param timeout: timeout given in seconds
        :return: list of unreachable hosts
        """
        error = []
        for host in self.iplist:
            host[1] = self.ping(host[0], timeout)
            if host[1] == 0:  # store hosts, which did not respond
                error.append(host[0])
        return error

    def sethostfile(self, filename):
        """
        Set configuration file and validate its path
        :param filename: File to load
        :raises FileNotFoundError if file path is invalid
        """
        directory = os.path.dirname(__file__)
        fullpath = os.path.join(directory, filename)  # Create absolute path
        if os.path.isfile(fullpath):  # Check absolute path
            self.hostfile = fullpath
        elif os.path.isfile(filename):  # Check again, if full path were passed as argument
            self.hostfile = filename
        else:
            raise FileNotFoundError('hostfile not found')


class Dashbutton:
    def __init__(self, mac, name, event, message):
        """
        Constructor for Dashbutton class
        :param mac: MAC address of button
        :param name: name of button
        :param event: event to trigger, if button is pressed
        :param message: message to print, if button is pressed
        """
        self.mac = mac
        self.name = name
        self.function = event
        self.message = message


class MacScanner(threading.Thread):
    def __init__(self, dashdict, functioncall=print, debug=False):
        """
        Constructor of MacScanner Thread
        :param dashdict: Dictionary of dashbuttons to watch (format: {'MAC address':buttonobject})
        :param functioncall: passing the output function to the thread
        :param debug: printing all received ARP packages to stdout, default is False
        """
        threading.Thread.__init__(self)
        self.mac_accept = list(dashdict.keys())  # Store known MAC addresses
        self.dashbuttons = list(dashdict.values())  # Store known Dashbuttons
        self.dashdict = dashdict  # Store Dashdict to find button by given MAC without iterating self.dashbuttons
        self.mac_unknown = []
        self.current_mac = ""
        self.debug = debug
        self.func = functioncall

    def addmac(self, mac):
        """
        Adding MAC address to known MAC list
        :param mac: MAC to add
        :return:
        """
        self.mac_accept.append(mac)

    def adddashbutton(self, button):
        """
        Add Dashbutton and register its MAC Address
        :param button:
        :return:
        """
        self.mac_accept.append(button.mac)
        self.dashbuttons.append(button)
        self.dashdict.update({button.mac: button})

    def run(self):
        """
        Start sniffing the network for ARP packages. If any package is detected, call self.__arp_display
        """
        # noinspection PyArgumentEqualDefault
        sniff(prn=self.__arp_display, filter="arp", store=0, count=0)

    @staticmethod
    def checkMAC(x):
        """
        Check, if given string is valid MAC address. Will be used for adding devices via incomming WA messages
        :param x: string to be evaluated
        :return:
        """
        import re  # Regular Expression module
        if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", x.lower()):
            return 1  # valid MAC
        else:
            return 0  # invalid MAC

    def __arp_display(self, pkt):
        """
        Private function, which is called, if ARP package is detected
        :param pkt: detected package
        :return:
        """
        self.current_mac = str(pkt[ARP].hwsrc)  # Extract MAC adress from package
        if pkt[ARP].op == 1 and self.debug:
            print("ARP Probe from: " + pkt[ARP].hwsrc)

        # Check, if MAC address has not been seen before
        if self.current_mac not in self.mac_accept and self.current_mac not in self.mac_unknown:
            # Calling function passed in constructor, add device to unknown list and perform further actions
            self.func("Neues unbekanntes Gerät entdeckt:\n{0}".format(self.current_mac))
            self.mac_unknown.append(self.current_mac)
            self.unknownmacdetected(self.current_mac)

        # Check, if MAC address is known
        elif self.current_mac in self.mac_accept:
            # Get button device, and perform button defined actions
            button = self.dashdict[self.current_mac]
            self.func(button.message)
            button.function()
            time.sleep(1)

    # noinspection PyMethodMayBeStatic
    def unknownmacdetected(self, mac):
        """ TO DO
        message = eingehende Nachricht
        if checkMAC(message)
            mac_accept.append(message)
            mac_unknown.remove(message)

            if current_mac in mac_oskar:
                print("Das untererwünschte Gerät "+str(current_mac)+" hat sich eingeloggt")"""
        return


class NetworkThread(threading.Thread):
    def __init__(self, name, hostfile, frequency=60, checktime=3600, functioncall=print):
        """
        Constructor for Network Monitoring
        :param name: Thread name
        :param hostfile: path of configuration file
        :param frequency: Checking frequency if all devices are online
        :param checktime: Checking frequency if any devices is offline
        :param functioncall: Output function
        """
        threading.Thread.__init__(self)
        self.name = name
        self.freq = frequency
        self.func = functioncall
        self.recheck = checktime
        self.nesca = NetworkScanner(hostfile)
        self.exit = False
        self.scan = True

    def pause(self):
        """
        Pause scanning
        :return:
        """
        print("pause")
        self.scan = False

    def resume(self):
        """
        Resume Scanning
        :return:
        """
        print("resume")
        self.scan = True

    def shutdown(self):
        """
        Stop scanning and terminating thread
        :return:
        """
        print("Exiting Thread")
        self.exit = True

    def run(self):
        """
        Redefine threading.Thread.run function
        :return:
        """
        while not self.exit:  # Thread Loop
            offline = []
            # noinspection PyBroadException
            try:
                if self.scan:
                    offline = self.nesca.pinghostlist()  # Scan all devices
                if len(offline) > 0:  # if return value is not an empty list, some devices are offline
                    message = "Following devices seems to be offline:\n" + '\n'.join(offline)
                    self.func(message)
                    time.sleep(self.recheck)  # Wait until next check
                else:
                    print("All online")
                    time.sleep(self.freq)
            except:
                logging.error(traceback.format_exc())  # Track down error
                self.exit = True
        return


def do_something():
    """
    Dummy function to be called if script is running as main
    :return:
    """
    print("FOOO")
    return


if __name__ == "__main__":
    thread1 = MacScanner(dashdict={}, debug=False)
    thread1.adddashbutton(Dashbutton("78:e1:03:49:ad:c6", "Nivea", do_something, "Nivea gedrückt"))
    thread1.adddashbutton(Dashbutton("fc:a6:67:54:4c:a6", "Energy", do_something, "Energy gedrückt"))
    thread1.start()
    thread1.join()
