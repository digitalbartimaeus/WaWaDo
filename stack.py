#  coding=utf-8

from yowsup.stacks import YowStackBuilder
from layer import TranceiverLayer
from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers.network import YowNetworkLayer


class TranceiverStack(object):
    def __init__(self, credentials, messages, encryptionEnabled=True, out=print):

        stackBuilder = YowStackBuilder()

        self.stack = stackBuilder \
            .pushDefaultLayers(encryptionEnabled) \
            .push(TranceiverLayer) \
            .build()

        self.stack.setProp(TranceiverLayer.PROP_MESSAGES, messages)
        TranceiverLayer.PROP_OUTPUT = out
        self.stack.setProp(YowAuthenticationProtocolLayer.PROP_PASSIVE, False)
        self.stack.setCredentials(credentials)

    def start(self):
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.stack.loop()
        except AuthError:
            print("Authentication Error")

    def send_messages(self, phone, message):
        self.stack.broadcastEvent(YowLayerEvent('send_message', message=message, phone=phone))
