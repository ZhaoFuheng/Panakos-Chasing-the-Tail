#!/usr/bin/env python
import sys
import struct
import os

from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr
from scapy.all import Packet, IPOption
from scapy.all import ShortField, IntField, LongField, BitField, FieldListField, FieldLenField
from scapy.all import Ether, IP, TCP, UDP, Raw
from scapy.layers.inet import _IPOption_HDR
# import crcmod

V = 2
COCOSKETCHSIZE = 65536
BITMAPSIZE = 65536
COUNTMIN = 65536 
T = 16

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "ens4" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find ens4 interface")
        exit(1)
    return iface
class MyFlow(Packet):
    name = "MyFlow"
    fields_desc=[ IntField("id",0) ]

class UpdateData(Packet):
    name = "UpdateData"
    fields_desc=[ 
        BitField("type", 0, 8),
        BitField("key", 0, 32),
        BitField("bitmapCount", 0, 8),
        BitField("countmin1", 0, 8),
        BitField("countmin2", 0, 8),
        IntField("cocoCount1",0),
        IntField("cocoCount2",0),
        IntField("id",0),           
        IntField("id2",0),           
        BitField("delta", 0, 8),
        BitField("bitmapHash", 0, 17),
        BitField("countminHash1", 0, 15),
        BitField("countminHash2", 0, 15),
        BitField("padding", 0, 1),

        ]

pnum = 0
bitmap = {}
countmin1 = {}
countmin2 = {}
cocoSketch = {}



def handle_pkt(pkt):
    if len(pkt) == 94: # or Ether in pkt and pkt[Ether].src == '00:00:ff:ff:ff:ff':
        print("got a packet")
        print(len(pkt))
        global pnum
        global cocoSketch
        global bitmap
        global countmin1
        global countmin2
        parsed_pkt = UpdateData(_pkt=bytes(pkt)) 
        if V == 1:
            print("got a packet: ", pnum)
            
        if V == 2:
            parsed_pkt2 = Ether(_pkt=bytes(parsed_pkt[1])) 
            parsed_pkt.show2()
            parsed_pkt3 = MyFlow(_pkt=bytes(parsed_pkt2[2])) 
            parsed_pkt2.show2()
            parsed_pkt3.show2()
        pnum += 1

        if(parsed_pkt[UpdateData].type == 1):
            h1 = parsed_pkt[UpdateData].bitmapHash
            bitmap[h1] = parsed_pkt[UpdateData].bitmapCount #if parsed_pkt[UpdateData].bitmapCount < 3 else 2
            pass
        elif(parsed_pkt[UpdateData].type == 2):
            h2 = parsed_pkt[UpdateData].countminHash1
            h3 = parsed_pkt[UpdateData].countminHash2
            countmin1[h2] = parsed_pkt[UpdateData].countmin1 if parsed_pkt[UpdateData].countmin1 <= T else T
            countmin2[h3] = parsed_pkt[UpdateData].countmin2 if parsed_pkt[UpdateData].countmin2 <= T else T

            pass
        elif(parsed_pkt[UpdateData].type == 3):
            h1 = parsed_pkt[UpdateData].bitmapHash
            h2 = parsed_pkt[UpdateData].countminHash1
            h3 = parsed_pkt[UpdateData].countminHash2
            if h1 in bitmap:
                del bitmap[h1]
            if h2 in countmin1:
                del countmin1[h2]
            if h3 in countmin2:
                del countmin2[h3]
            id = parsed_pkt[UpdateData].id 

            count = int((parsed_pkt[UpdateData].cocoCount1 + parsed_pkt[UpdateData].cocoCount2)/2)
            cocoSketch[id] = int(count)




        sys.stdout.flush()

def main():
    if len(sys.argv)<5:
        print('pass 4 arguments: <outpuFile> <outpuFile> <outpuFile> <outpuFile>')
        exit(1)
    global pnum
    global cocoSketch
    global bitmap
    global countmin1
    global countmin2
    # this recieves traffic on iface ens4(Change according to your needs)
    iface = 'ens4'
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    """
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

    """    
    sniff(iface = iface,
        prn = lambda x: handle_pkt(x))
    print("stopped")
    print("Writing cocoSketch entries in file ")
    filename = sys.argv[1]
    f = open(filename, "w")
    for k in cocoSketch:
        f.write(str(k) + " " + str(cocoSketch[k]) + "\n")
    f.close()
    print("Writen")
    print("Writing bitmap entries in file ")
    filename = sys.argv[2]
    f = open(filename, "w")
    for k in bitmap:
        f.write(str(bitmap[k]) + "\n")
    f.close()
    print("Writen")
    print("Writing countmin table 1 entries in file ")
    filename = sys.argv[3]
    f = open(filename, "w")
    for k in countmin1:
        f.write(str(countmin1[k]) + "\n")
    print("Writen")
    print("Writing countmin table 2 entries in file ")
    filename = sys.argv[4]
    f = open(filename, "w")
    for k in countmin2:
        f.write(str(countmin2[k]) + "\n")
    print("Writen")
    exit()


if __name__ == '__main__':
    main()
