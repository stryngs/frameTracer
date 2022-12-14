#!/usr/bin/python3

import argparse
import binascii
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
import packetEssentials as PE
import os
import sys
import time
from queue import Queue, Empty
from threading import Thread

class Threader(object):
    def __init__(self, args):
        self.args = args
        print('Running threaded!\n')

    def handler(self, q, m, pkt):
        """ Process and finish out the task """

        # Queue handling
        qS = q.qsize()
        if qS > 5:
            print('                                                            Current queue of {0}'.format(qS))
        if self.args.y is not None:
            if self.args.c is not None:
                PE.hd.mpTrafficThreaded(pkt, self.args.x.lower(), self.args.y.lower(), q = self.args.c, verbose = self.args.v)
            else:
                PE.hd.mpTrafficThreaded(pkt, self.args.x.lower(), self.args.y.lower(), verbose = self.args.v)

        ## Trace a single
        else:
            if self.args.c is not None:
                PE.hd.soloThreaded(pkt, self.args.x.lower(), q = self.args.c, verbose = self.args.v)
            else:
                PE.hd.soloThreaded(pkt, self.args.x.lower(), verbose = self.args.v)

        ## closeout
        q.task_done()

    def sniff(self, q):
        ##Target function for Queue (multithreading)
        sniff(iface = self.args.i, prn = lambda x: q.put(x), store = 0)

    def threaded_sniff(self):
        q = Queue()                                                             ### Troublesome with python2, odd.
        sniffer = Thread(target = self.sniff, args = (q,))
        sniffer.daemon = True
        sniffer.start()
        while True:
            try:
                pkt = q.get()
                self.handler(q, self.args.i, pkt)
            except Empty:
                pass

def main(args):

    global pkts
    ## Verbosity
    if args.v is True:
        PE.hd.verbose = True
        verbosity = True
    else:
        verbosity = False

    """
    Perhaps retool mpTrafficCap and soloCap to be split functions for speed?
    """

    if args.t is False:

        ## Trace a pair
        if args.y is not None:
            if args.c is not None:
                pHandler = PE.hd.mpTrafficCap(args.x.lower(), args.y.lower(), q = args.c, verbose = verbosity)
            else:
                pHandler = PE.hd.mpTrafficCap(args.x.lower(), args.y.lower(), verbose = verbosity)

        ## Trace a single
        else:
            if args.c is not None:
                pHandler = PE.hd.soloCap(args.x.lower(), q = args.c, verbose = verbosity)
            else:
                pHandler = PE.hd.soloCap(args.x.lower(), verbose = verbosity)

        ## Stream input
        if args.f is None:
            pkts = sniff(iface = args.i, prn = pHandler, store = 0)

        ## pcap input
        else:
            pkts = sniff(offline = args.f, prn = pHandler, store = 0) ## Need to PcapReader this
    else:

        ## Trace a pair
        thd = Threader(args)
        thd.threaded_sniff()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'frameTracer')
    parser.add_argument('--graph', action = 'store_true', help = 'Visualize the data via plotly')
    parser.add_argument('-c', metavar = 'frame count to capture', help = 'frame count to capture')
    parser.add_argument('-f', metavar = 'read from pcap', help = 'read from pcap') ## Not ideal for large pcaps, need PcapReader() instead
    parser.add_argument('-i', metavar = 'interface', help = 'interface', required = True)
    parser.add_argument('-t', help = 'thread it', action = 'store_true')
    parser.add_argument('-x', metavar = 'mac X', help = 'mac X', required = True)
    parser.add_argument('-y', metavar = 'mac Y', help = 'mac Y')
    parser.add_argument('-v', help = 'verbose', action = 'store_true')
    args = parser.parse_args()
    main(args)
