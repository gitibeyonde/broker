#!/usr/bin/python2

import socket
import struct
import sys
import os
import signal
import time
import logging
import time
import traceback
import codecs

CHUNKSIZE=64
BROKER_PORT = 5020
publicMap = {}
privateMap = {}
uuidMap = {}
timeMap = {}
sockfd=None
fileCmds = set(['GINI','LINI', 'HINI', 'MINI', 'SINI', 'TINI', 'BINI', 
                'VA', 'VB', 'VC', 'VD', 'VE', 'VF', 'VG', 'VH', 'VI', 'VJ', 'VK', 'VL', 'VM', 'VN', 'VO', 'VP'])

log_level = logging.WARN

def ctrlc(signal, frame):
    global sockfd
    for key, value in publicMap.iteritems():
        #print value
        sockfd.sendto(b"EXIT:", value)
        time.sleep(0.1)
    sockfd.close()
    sys.exit("Exiting")
    
    
def bytes2addr( bytes ):
    """Convert a hash to an address pair."""
    if len(bytes) != 6:
        return 0,0
    host = socket.inet_ntoa( bytes[:4] )
    port, = struct.unpack( "H", bytes[-2:] )
    return host, port

def addr2bytes( addr ):
    """Convert an address pair to a hash."""
    host, port = addr
    try:
        host = socket.gethostbyname( host )
    except (socket.gaierror, socket.error):
        raise ValueError
    try:
        port = int(port)
    except ValueError:
        raise ValueError
    bytes  = socket.inet_aton( host )
    bytes += struct.pack( "H", port )
    return bytes

def main():
    global sockfd
    global publicMap
    global privateMap
    global uuidMap
    global timeMap
    
    logging.basicConfig(format='%(levelname)s:%(message)s', level=log_level)
    
    sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    sockfd.bind( ("", BROKER_PORT) )

    signal.signal(signal.SIGINT, ctrlc)
    
    req_addr = ''
    while True: 
        try:
            msg, req_addr = sockfd.recvfrom(CHUNKSIZE)

            logging.debug(">>>>>>>>>Listening on *:%d (udp) Connection from %s Got message %s" % (BROKER_PORT, req_addr, msg))
            
            if len(msg) < 2:
                action = "NONE"
            else:
                action, uuid, priv_addr_bytes = msg.split(':', 2)

            logging.debug(">>>>>>>>>parsed action=%s, uuid=%s, priv_byte_addr=%s" % (action, uuid, priv_addr_bytes))
            
            if action == 'LEAVE':
                if uuid in publicMap:
                    if req_addr in uuidMap:
                        del uuidMap[req_addr]
                    if uuid in publicMap:
                        del publicMap[uuid]
                    if uuid in privateMap:
                        del privateMap[uuid]
                    if uuid in privateMap:
                        del timeMap[uuid]
                        
                    logging.debug("Removed uuid="+ uuid);
            elif action == 'PADDR':
                senders_pub_ip, senders_pub_port = req_addr
                if uuid in publicMap:
                    rcver_pub_addr, rcver_pub_ip = publicMap[uuid]
                    sockfd.sendto(b"RPADDR:" + addr2bytes(publicMap[uuid]), req_addr)
                    logging.debug("RPADDR:Sent peer addrs of device %s to %s" % (publicMap[uuid], req_addr))
                    sockfd.sendto(b"RPADDR:" + addr2bytes(req_addr), publicMap[uuid])
                    logging.debug("RPADDR:Sent Net peer %s to %s" % (req_addr, publicMap[uuid]))
                else:
                    #there uuid is not registered
                    sockfd.sendto(b"NOTONLINE:", req_addr)
                    logging.debug("NOTONLINE: Sent NOTONLINE of %s to %s " % (uuid,req_addr))
            elif action == 'TIME':
                if uuid in timeMap:
                    logging.debug("Last ping time delta " +  str(int(time.time()) - timeMap[uuid]))
                    sockfd.sendto(b"RTIME:" +  str(int(time.time()) - timeMap[uuid]).decode('utf-8'), req_addr)  
                else:
                    sockfd.sendto(b"RTIME:-1", req_addr) 
                    logging.debug("Last ping time delta -1" ) 
            elif action in fileCmds:
                senders_pub_ip, senders_pub_port = req_addr
                #check if public ips are same then in that case communication can proceed on priavte ip
                responce = 'R' + action
                if uuid in publicMap:
                    rcver_pub_addr, rcver_pub_ip = publicMap[uuid]
                    if senders_pub_ip == rcver_pub_addr:
                        # the two are on same public ip use private addresses
                        logging.debug("%s: Same public ip %s" % (action, rcver_pub_addr))
                        if uuid in privateMap and req_addr in uuidMap:
                            req_uuid = uuidMap[req_addr]
                            sockfd.sendto(responce + ":" + addr2bytes(privateMap[uuid]), req_addr)
                            logging.debug(responce + ": Sent private addr %s of %s to %s" % (privateMap[uuid], uuid, req_addr))
                            
                            sockfd.sendto(responce + ":" + addr2bytes(privateMap[req_uuid]), publicMap[uuid])
                            logging.debug(responce + ": Sent private addr %s of %s to %s" % (privateMap[req_uuid], req_uuid, publicMap[uuid]))
                        else:
                            sockfd.sendto(responce + ":" + addr2bytes(publicMap[uuid]), req_addr)
                            logging.debug(responce + ":Same Net Sent public addr of %s to %s" % (uuid, req_addr))
                            sockfd.sendto(responce + ":" + addr2bytes(req_addr), publicMap[uuid])
                            logging.debug(responce + ":Same Net Sent %s to %s" % (req_addr, publicMap[uuid]))
                    else:
                        sockfd.sendto(responce + ":" + addr2bytes(publicMap[uuid]), req_addr)
                        logging.debug(responce + ": Sent public addr of %s to %s" % (uuid,req_addr))
                        sockfd.sendto(responce + ":" + addr2bytes(req_addr), publicMap[uuid])
                        logging.debug(responce + ": Sent %s to %s" % (req_addr, publicMap[uuid]))
                else:
                    #there uuid is not registered
                    logging.debug("NOTONLINE: Sent NOTONLINE of %s to %s " % (uuid,req_addr))
                    sockfd.sendto(b"NOTONLINE:", req_addr)
            elif action == 'REFRESH':
                #sockfd.sendto(b"RREF:" + addr2bytes(req_addr), req_addr )
                logging.debug("REFRESH: Send public address in payload TO %s:%d" % req_addr)
                publicMap[uuid] = req_addr
                privateMap[uuid] = bytes2addr(priv_addr_bytes)
                uuidMap[req_addr] = uuid
                timeMap[uuid] = int(time.time())
                logging.debug("REFRESH: Re-Send public address in payload TO %s:%d" % bytes2addr(priv_addr_bytes))
            elif action == 'REGISTER':
                sockfd.sendto(b"RREG:" + addr2bytes(req_addr), req_addr )
                logging.debug("REGISTER: Send public address in payload TO %s:%d" % req_addr)
                publicMap[uuid] = req_addr
                privateMap[uuid] = bytes2addr(priv_addr_bytes)
                uuidMap[req_addr] = uuid
                timeMap[uuid] = int(time.time())
                logging.debug("REGISTER: Adding PUNCH mapping of pub %s and priv %s to uuid %s" % (req_addr, bytes2addr(priv_addr_bytes), uuid))
            elif action == 'ACTION':
                senders_pub_ip, senders_pub_port = req_addr
                #check if public ips are same then in that case communication can proceed on priavte ip
                responce = action
                data = priv_addr_bytes
                if uuid in publicMap:
                    rcver_pub_addr, rcver_pub_ip = publicMap[uuid]
                    if senders_pub_ip == rcver_pub_addr:
                        # the two are on same public ip use private addresses
                        logging.debug("ACTION- %s: Same public ip %s" % (action, rcver_pub_addr))
                        if uuid in privateMap and req_addr in uuidMap:
                            sockfd.sendto(responce + ":" + data, publicMap[uuid])
                            logging.debug("ACTION-" + responce + ": Sent private addr %s to %s" % (privateMap[req_uuid], publicMap[uuid]))
                        else:
                            sockfd.sendto(responce + ":" + data, publicMap[uuid])
                            logging.debug("ACTION-" + responce + ":Same Net Sent %s to %s" % (data, publicMap[uuid]))
                    else:
                        sockfd.sendto(responce + ":" + data, publicMap[uuid])
                        logging.debug("ACTION-" + responce + ": Sent %s to %s" % (data, publicMap[uuid]))
                
            else:
                # gobble data
                    logging.debug("JUNK RECEIVED")
                    continue
        except :
                if (log_level == logging.DEBUG):
                    traceback.print_exc()
                logging.debug("Spurious connection ignored from ", req_addr)
                continue

if __name__ == "__main__":
   
    try:
        pid = os.fork()
        if pid > 0:
            print('PID: %d' %pid)
            os._exit(0)
    except OSError:
        print('Unable to fork. Error: %d (%s)' % (error.errno, error.strerror))
        GPIO.cleanup()
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            print('PID: %d' %pid)
            os._exit(0)
    except OSError:
        print('Unable to fork. Error: %d (%s)' % (error.errno, error.strerror))
        GPIO.cleanup()
        sys.exit(1)

    main()


