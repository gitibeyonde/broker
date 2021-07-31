#!/usr/bin/env python

''' IBEYONDE PROPRITORY '''
#

import sys,time,os
import signal
import socket
from select import select
from PIL import Image
import io
from path import path
import logging
import utils, peer
import traceback
import time, threading

BROKER_HOST = socket.gethostbyname('broker.ibeyonde.com');
BROKER_PORT = 5020
TIMEOUT=5
CAM_UUID="d97080b2"

sockfd=''
uuid=''

def ctrlc(signal, frame):
    broker = (BROKER_HOST, BROKER_PORT)
    sockfd.sendto("LEAVE:" + uuid + ":" + BROKER_HOST, broker);
    sockfd.close()
    sys.exit("Exiting")
    
                
def getCommandLine():
    print ">>"
    punchreq = sys.stdin.readline()
    # Format is 'uuid imagefile'
    punchreq = punchreq.strip()
    if not punchreq:
        return False, 1
    
    if punchreq == 'exit':
        sockfd.sendto("LEAVE:" + uuid + ":" + BROKER_HOST, broker);
        sockfd.close()
        sys.exit("Exiting")
    
    return True, punchreq


def main():
    global sockfd
    global uuid
    global broker
    
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    try:
        broker = (BROKER_HOST, BROKER_PORT)
        uuid = "T12345678"
    except (IndexError, ValueError):
        pass
    
    if uuid=='':
        raise Exception("UUID needs to be passed on command line")
    
    signal.signal(signal.SIGINT, ctrlc)
    
    thispeer = peer.Peer(uuid)
    sockfd = thispeer.register(broker)
    sockfd.settimeout(TIMEOUT)
    
    
    imgsiz=0
    imgbytes=''

    while True:
        try:
            rfds,_,_ = select( [0, sockfd], [], [])
            
            if 0 in rfds:
                success, peeruuid = getCommandLine()
                if not success:
                    continue
                print  " peeruuid=", peeruuid
                print  " CAM_UUID=", CAM_UUID
                
                ''' BROKER '''
                sockfd.sendto("BINI:" + CAM_UUID + ":", broker)
                logging.debug("BINI sent to broker for %s" % CAM_UUID)
                
            elif sockfd in rfds:
                cmd, data, addr = utils.recvCommand(sockfd)
                logging.debug("Receiving from %s:%d" % (addr))
                logging.debug("Received  %s %s" % ( cmd, data))
               
                if cmd == "RBINI": #ONE
                    if addr != broker:
                        logging.warn("Expecting data from broker %s:%d" % broker)
                    else:
                        #sender should be broker
                        if cmd == 'NOTONLINE':
                            logging.warn("The peer is not online %s" % CAM_UUID)
                        else:
                            peeraddr = utils.bytes2addr(data)
                            logging.debug("RBINI: received from broker %s peer is  %s" % (addr, utils.bytes2addr(data)))
                            sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            sockfd.setblocking(0)
                            sockfd.settimeout(TIMEOUT)
                            sockfd.bind(peeraddr)
                            sockfd.sendto("junk", peeraddr )
                            time.sleep(1)
                            continue
                
                elif cmd == "SIZE":
                    if addr != peeraddr:
                        logging.warn("Expecting data from peer %s:%d" % peeraddr)
                        reset()
                    else:
                        size = int(data)
                        logging.debug("Received size of the image %d", size)
                        fullimg = utils.recvAll(sockfd, size)
                        logging.debug("RECEIVED size of the image %d" % len(fullimg))
                        img = Image.open(io.BytesIO(str(bytearray(fullimg))))
                else:
                    logging.debug("Cmd received from %s:%d %s" % (addr, cmd))
                    if addr[0] == peeraddr[0]:
                        logging.debug("Peer connection messed up resetting state")
        except:
            sys.exit(0)
            
        
                  
if __name__ == "__main__":
    main()





