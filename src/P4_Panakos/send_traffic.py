import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, sendpfast
from scapy.all import Packet
from scapy.all import IntField
from scapy.all import Ether, IP, UDP, TCP

THRESHOLD = 18
COUNTMIN_T = 5
BITMAP_T = 2
verbose = 3
class MyFlow(Packet):
    name = "MyFlow"
    fields_desc=[ IntField("id",0) ]

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "ens3" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find ens3 interface")
        exit(1)
    return iface

def main():

    if len(sys.argv)<3:
        print('pass 2 arguments: <destination> "<testFile>"')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    # this sends traffic on iface ens3(Change according to your needs in get_if() function)
    iface = get_if()

    filename = sys.argv[2]
    f = open(filename, "r")

    pkts = []
    while(True):
        line = f.readline()
        if not line:
            break
        line = line.split()
        id = int(line[0])
        count = int(line[1])
        #for i in range(count + COUNTMIN_T + BITMAP_T):
        pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
        pkt = pkt /IP(dst=addr, proto=6) /MyFlow(id=id) /TCP(dport=1234, sport=random.randint(49152,65535)) / "hello"
        if verbose == 1:
            pkt.show()
        if verbose == 2:
            print(id)
        for i in range(count):
            pkts.append(pkt)
    print("sending")
    sendpfast(pkts, iface=iface, pps=1000, loop=1)
    print("sent")
    #sendp("stop", iface=iface, verbose=False)

main()
