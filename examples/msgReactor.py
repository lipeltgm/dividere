#!/usr/bin/python3
import dividere
import clientMsgs_pb2 as clientMsgs
import time

class MyMsgReactor(dividere.messaging.MsgReactor):
  def handleMsg01(self, obj, msg):
    print("got msg01 msg: %s"%(str(msg)))
    msg.field1=msg.field1[::-1]
    obj.send(msg)

  def handleMsg02(self, obj, msg):
    print("got msg02 msg: %s"%(str(msg)))

#-----main-----
mh=MyMsgReactor([dividere.messaging.Response('tcp://*:5555'),
                 dividere.messaging.Subscriber('tcp://localhost:5655')])

req=dividere.messaging.Request('tcp://localhost:5555')
msg=clientMsgs.Msg01()
msg.field1='hello'
req.send(msg)

pub=dividere.messaging.Publisher('tcp://*:5655')

msg2=clientMsgs.Msg02()
msg2.field1='some published event'
time.sleep(1); #--accomodate late joiner
pub.send(msg2)

reply=req.recv()
assert(reply.field1==msg.field1[::-1])
print(reply)
mh.stop()
  
req=None
pub=None
mh=None

