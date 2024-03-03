#!/usr/bin/python3
import dividere
import clientMsgs_pb2 as clientMsgs
import time

class MyMsgReactor(dividere.messaging.MtMsgReactor):
  def handleMsg01(self, obj, msg):
    print("got msg01 msg: %s"%(str(msg)))
    msg.field1=msg.field1[::-1]
    obj.send(msg)

  def handleMsg02(self, obj, msg):
    print("got msg02 msg: %s"%(str(msg)))

  def initThread(self):
    pass

class MyMsgReactor(dividere.messaging.MpMsgReactor):
  def handleMsg01(self, obj, msg):
    print("got msg01 msg: %s"%(str(msg)))
    msg.field1=msg.field1[::-1]
    obj.send(msg)
    print("sent response %s"%(msg))

  def handleMsg02(self, obj, msg):
    print("got msg02 msg: %s"%(str(msg)))

  def initThread(self):
    pass


def test00():
  fePort=dividere.connection.PortManager.acquire()
  bePort=dividere.connection.PortManager.acquire()
  mh=MyMsgReactor([dividere.messaging.Response('tcp://*:%d'%(fePort)),
                   dividere.messaging.Subscriber('tcp://localhost:%d'%(bePort))])
  
  req=dividere.messaging.Request('tcp://localhost:%d'%(fePort))
  msg=clientMsgs.Msg01()
  msg.field1='hello'
  req.send(msg)
  
  pub=dividere.messaging.Publisher('tcp://*:%d'%(bePort))
  
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

def test01():
  port1=dividere.connection.PortManager.acquire()
  port2=dividere.connection.PortManager.acquire()

  mh=MyMsgReactor(["Response('tcp://*:%d')"%(port1),
                   "Subscriber('tcp://localhost:%d')"%(port2)])

  req=dividere.messaging.Request('tcp://localhost:%d'%(port1))
  msg=clientMsgs.Msg01()
  msg.field1='hello'
  req.send(msg)
  
  reply=req.recv()
  assert(reply.field1==msg.field1[::-1])
  print(reply)

  pub=dividere.messaging.Publisher('tcp://*:%d'%(port2))
  msg2=clientMsgs.Msg02()
  msg2.field1='some published event'
  time.sleep(1); #--accomodate late joiner
  pub.send(msg2)
  
  mh.stop()
  req=None
  pub=None
  mh=None
#-----main-----
#test00()
test01()
