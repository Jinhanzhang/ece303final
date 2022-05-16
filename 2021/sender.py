# Written by S. Mevawala, modified by D. Gitzel

import logging
import socket

import channelsimulator
import utils
import sys
import hashlib
class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__()

    def send(self, data):
        self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        while True:
            try:
                self.simulator.u_send(data)  # send data
                ack = self.simulator.u_receive()  # receive ACK
                self.logger.info("Got ACK from socket: {}".format(
                    ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                break
            except socket.timeout:
                pass


class MySender(BogoSender):

    def __init__(self, m=512, n = 10, timeout=0.01):
        super(MySender, self).__init__()
        self.m = m # send m bytes of data each time
        self.n = n # seq no. from 0 to n-1
        self.timeout = timeout
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        print(len(data)/self.m)
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        idx = 0 #idx of data
        seq = 0 #seq no.
        flag = False # resend flag
        while idx<len(data):
            # self.logger.info("idx: {}".format(idx))
            try:
                if flag:
                    #send previous packet again
                    self.simulator.u_send(packet)
                else:
                    packet = bytearray([seq])
                    # self.logger.info("send seq: {}".format(seq))
                    packet = packet + data[idx:idx+self.m]
                    # self.logger.info("send seq: {}".format(packet[0]))
                    checksum = self.get_checksum(packet)
                    packet = checksum + packet
                    # self.logger.info("send seq: {}".format(packet[32]))
                    idx += self.m
                    seq = (seq + 1) % self.n
                    self.simulator.u_send(packet)

                ack = self.simulator.u_receive()
                # self.logger.info("ack length: {}".format(len(ack)))
                
                if self.get_checksum(ack[32:]) == ack[0:32]:
                    # self.logger.info("ack seq: {}".format(ack[32]))
                    if (ack[32]+1)%self.n == seq:
                        flag = False
                    else:
                        flag = True
                else:
                    flag = True
            except socket.timeout:
                flag = True
                
    def get_checksum(self, data):
        #print(data)
        checksum = hashlib.md5(data).hexdigest()
        #print(checksum)
        return checksum



if __name__ == "__main__":
    DATA = bytearray(sys.stdin.read())
    sndr = MySender()
    sndr.send(DATA)
