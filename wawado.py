#!/usr/bin/env python3
#  coding=utf-8

"""Whatsapp Watch-Dog

WaWaDo uses multiple threads to monitor your network and forward any events to your phone number using Whatsapp.

$ python wawado.py -dash -isalive

programm call argments decide, which service to be started.

Todo:
    * Add simultanious receiving functionality
    * Check portability on Raspberry Pi
    * Add Movement detection using OpenCV
    * Dropping Root privileges

"""

from argparse import ArgumentParser
from waclient import WhatsappClient
from networking import NetworkThread, MacScanner, Dashbutton
import time
import sys
import os

__author__ = "Pius Ganter, Jeremy Brauer"
__version__ = "1.0.0"
__status__ = "Production"


def sendmessage(m):
    """
    :param m: Message to be send
    :return: None
    """
    print("send Message: ", m)
    client.send(m)
    time.sleep(3)


def gotmessage(m, s, console=False):
    """
    On incomming messages check, if function shall be called and call it
    :param m: Received Message
    :param s: Sender
    :param console: Enable debugging
    :return None:
    """
    if console:
        print("gotMessage", m, s)
    if m.lower() in functions:
        functions[m]()  # Function is as value in dictionary for message as key


def do_something():
    print("Ich mache jetzt irgendwas")  # Dummy function
    return


if __name__ == "__main__":

    functions = {"start": lambda: thread1.resume(),
                 "pause": lambda: thread1.pause(),
                 "stop": lambda: thread1.shutdown()}

    # Parse command line arguments to decide, which service has to be started
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-dash', dest='dashbutton', action='store_true', default=False,
                        help="Watch Different Amazon-Dash Buttons using ARP scanning. Notice, you have to be root to run this service")
    parser.add_argument('-isalive', dest='ipscan', action='store_true', default=False,
                        help="Watching different devices, which are configured in hostlist file")
    args = parser.parse_args()

    threads = []  # List of all started threads to manage running threads
    client = WhatsappClient("client.config", func=gotmessage)  # Initiate WA-Client

    # Start different services based on command line arguments
    if args.ipscan:
        thread1 = NetworkThread("network-watchdog", hostfile="hostfile", frequency=120, checktime=10,
                                functioncall=sendmessage)  # Start IP-Monitoring
        thread1.setDaemon(True)
        thread1.start()
        threads.append(thread1)

    if args.dashbutton:
        if os.getuid() == 0:  # Checking for root privileges
            thread2 = MacScanner(dashdict={}, debug=False, functioncall=sendmessage)
            # Create known Dash-Buttons and pass them to the Scanning Class
            thread2.adddashbutton(Dashbutton("18:74:2e:fc:8b:b9", "Afri", do_something, "Afri gedrückt"))
            thread2.adddashbutton(Dashbutton("fc:a6:67:54:4c:a6", "Energy", do_something, "Energy gedrückt"))
            thread2.setDaemon(True)
            thread2.start()
            threads.append(thread2)
        else:
            print("You need root permissions for arp scanning!")
            sys.exit(1)

    while True:
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("Exit programm\n")
            sys.exit(0)
