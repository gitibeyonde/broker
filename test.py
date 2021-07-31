#!/usr/bin/python

import struct
import codecs
import socket

msg = b'REGISTER:4d6711e1:\xc0\xa8d\x1c\xd7l'

print(msg)

port = msg[-6:]

print(port)

msg = msg[:-7]
print (msg)
msg = codecs.decode(msg, 'ascii', 'ignore')


print (msg)

ig, uuid = msg.split(":", 1)


print(uuid)


host = socket.inet_ntoa( port[:4] )
port, = struct.unpack( "H", port[-2:] )


print(host)
print(port)

