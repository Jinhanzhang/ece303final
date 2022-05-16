# Written by S. Mevawala, modified by D. Gitzel

import logging

import channelsimulator
import utils
import sys
import socket
import hashlib
class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoReceiver(Receiver):
    ACK_DATA = bytes(123)

    def __init__(self):
        super(BogoReceiver, self).__init__()

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        while True:
            try:
                 data = self.simulator.u_receive()  # receive data
                 self.logger.info("Got data from socket: {}".format(
                     data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
	         sys.stdout.write(data)
                 self.simulator.u_send(BogoReceiver.ACK_DATA)  # send ACK
            except socket.timeout:
                sys.exit()

class MyReceiver(BogoReceiver):

    def __init__(self, n=10, timeout=10):
        super(MyReceiver, self).__init__()
        self.n = n
        self.timeout = timeout
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)


    def receive(self):
        self.logger.info(
            "Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        seq_p = -1
        ack_p = bytearray([2])
        ack_p = self.get_checksum(ack_p)+ack_p
        while True:
            try:
                data = self.simulator.u_receive()
                
                if self.get_checksum(data[32:]) == data[0:32]:
                    seq = data[32]
                    # self.logger.info("receive seq: {}".format(seq))
                    if data[32] == (seq_p+1)%self.n:
                        sys.stdout.write(data[33:])
                        sys.stdout.flush()
                        seq_p = seq
                        ack = bytearray([seq])
                        packet = self.get_checksum(ack) + ack
                        ack_p = packet
                        self.simulator.u_send(packet)
                else:
                    self.simulator.u_send(ack_p)
            except socket.timeout:
                print("didn't receive anything")
                sys.exit()
                    
    def get_checksum(self, data):
        checksum = hashlib.md5(data).hexdigest()
        return checksum


if __name__ == "__main__":
    rcvr = MyReceiver()
    rcvr.receive()
