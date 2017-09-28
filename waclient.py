#!/usr/bin/env python
# coding=utf-8

import sys
from stack import TranceiverStack
import time


class WhatsappClient:
    def __init__(self, conf, func=print):
        """
        Whatsapp Client Constructor
        :param conf: path to configuration file
        :param number: Receiver number
        :param initmessage: Initialization message to be send
        :param func: function to be called in case of incomming message (TO DO)
        """
        self.configuration = self.parseconfig(conf)  # Load configuration
        self.receivefunctioncall = func
        self.credentials = self.configuration["phone"], self.configuration["password"]
        try:
            # Initialise Yowsup stack
            self.stack = TranceiverStack(self.credentials, [([self.configuration["receiver"], self.configuration["initmessage"]])], out=self.receivefunctioncall)
            self.stack.start()
        except KeyboardInterrupt:
            return
        return

    @staticmethod
    def parseconfig(file):
        """
        :param file: path to config file
        :return:
        """
        config = {}
        try:
            # Read each file line
            with open(file) as f:
                for line in f:  # If line is not empty and is not a line comment
                    if len(line) and line[0] not in ('#', ';'):
                        (var, value) = line.split("=", 1)  # Split line after first "="
                        config[var] = value.strip()  # Remove Whitespace
            return config
        except IOError:
            print("Invalid Configuration")
            sys.exit(1)

    def send(self, message, number=None):
        """
        Call stacks sending function
        :param number: target number
        :param message:  message to be send as string
        :return:
        """
        if number is None:
            number = self.configuration["receiver"]
        self.stack.send_messages(number, message)

    def receive(self, number, message):
        """
        Pass received message to function call specified in constructor
        :param number: originator
        :param message:  received message
        :return:
        """
        self.receivefunctioncall(message, number)
        return


if __name__ == "__main__":  # testing
    sender = WhatsappClient("client.config")
    time.sleep(3)
    sender.send("TestB")
    time.sleep(1)
    print("send Message")


"""
if __name__ == "__main__":  # testing
    sender = WhatsappClient("client.config")
    time.sleep(3)
    sender.stack.send_messages("TestB")
    time.sleep(1)
    print("send Message")
"""