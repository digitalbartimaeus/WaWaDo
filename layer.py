#  coding=utf-8

from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.common.tools import Jid
import threading
import logging

logger = logging.getLogger(__name__)


class TranceiverLayer(YowInterfaceLayer):
    # Class variables. Will be assigned seperately
    PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue"
    PROP_OUTPUT = print

    def __init__(self):
        super(TranceiverLayer, self).__init__()
        self.ackQueue = []
        self.lock = threading.Condition()

    # call back function when there is a successful connection to whatsapp server
    # noinspection PyUnusedLocal
    @ProtocolEntityCallback("success")
    def onSuccess(self, successProtocolEntity):
        self.lock.acquire()
        for target in self.getProp(self.__class__.PROP_MESSAGES, []):
            # getProp() is trying to retreive the list of (jid, message) tuples, if none exist, use the default []
            phone, message = target
            messageEntity = TextMessageProtocolEntity(message, to=Jid.normalize(phone))
            # append the id of message to ackQueue list
            # which the id of message will be deleted when ack is received.
            self.ackQueue.append(messageEntity.getId())
            self.toLower(messageEntity)
        self.lock.release()

    # after receiving the message from the target number, target number will send a ack to sender(us)
    @ProtocolEntityCallback("ack")
    def onAck(self, entity):
        self.lock.acquire()
        # if the id match the id in ackQueue, then pop the id of the message out
        if entity.getId() in self.ackQueue:
            self.ackQueue.pop(self.ackQueue.index(entity.getId()))

        if not len(self.ackQueue):
            self.lock.release()
            logger.info("Message sent")
            raise KeyboardInterrupt()
        self.lock.release()

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getType() == 'text':
            TranceiverLayer.PROP_OUTPUT(messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False))
        self.toLower(messageProtocolEntity.forward(messageProtocolEntity.getFrom()))
        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    def onEvent(self, yowLayerEvent):
        """
        Processsing Event, which is called. Necessary to send multiple messages to one Yowsup stack
        :param yowLayerEvent:
        :return:
        """
        if yowLayerEvent.getName() == 'send_message':
            message = yowLayerEvent.getArg('message')
            phone = Jid.normalize(yowLayerEvent.getArg('phone'))
            messageEntity = TextMessageProtocolEntity(message, to=phone)  # create message object
            self.ackQueue.append(messageEntity.getId())  # Waiting for receiver ack
            self.toLower(messageEntity)  # pass message to lower layer
