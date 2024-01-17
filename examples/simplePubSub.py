#!/usr/bin/python3
import dividere
import clientMsgs_pb2 as clientMsgs
import time

Port=dividere.connection.PortManager.acquire()
pub=dividere.messaging.Publisher('tcp://*:%d'%(Port))
sub=dividere.messaging.Subscriber('tcp://localhost:%d'%(Port))
time.sleep(2); #--delay to address 'late joiner'

msg=clientMsgs.Msg01()
msg.field1='abcd'
pub.send(msg)
reply=sub.recv()
print("reply: %s"%(reply))
assert(reply==msg)

#--destroy pub/sub objects to free resources and terminate threads
pub=None
sub=None

