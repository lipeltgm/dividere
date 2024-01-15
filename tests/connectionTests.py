#!/usr/bin/python3
import unittest
import logging
import sys
import dividere
import time
import os
import random
import threading
import zmq
import re

class connectionTests(unittest.TestCase):
  def _singleThreadPubSubTest(self, pubEndpt, subEndpt):
    pub=dividere.connection.Publisher(pubEndpt)
    sub=dividere.connection.Subscriber(subEndpt)
    time.sleep(1); #--let subscribers get set up before sending initial msg

    N=10
    for i in range(0,N):
      msg=b"message-%03d"%(i)
      pub.send(msg)
      received=sub.recv()
      logging.debug("%s == %s"%(msg,received))
      self.assertTrue(msg==received)

  #--test simple pub/sub functionality, create a publisher,
  #--  a subscriber using TCP with a well-defined port
  #--  on localhost, send a series of simple/unique messages
  #--  and confirm they are received in-order
  def test00(self):
    logging.info("executing test")
    Port=dividere.connection.PortManager.acquire()
    self._singleThreadPubSubTest('tcp://*:%d'%(Port),'tcp://localhost:%d'%(Port))


  #--test simple pub/sub using IPC
  def test01(self):
    logging.info("executing test")
    ipcTmpDir='/tmp/feeds'
    if not os.path.exists(ipcTmpDir):
      os.mkdir(ipcTmpDir) 
    endPt='ipc://%s/0'%(ipcTmpDir)
    self._singleThreadPubSubTest(endPt,endPt)

  def test02(self):
    #--test over a range of TCP ports, create a publisher, a subscriber,
    #-- publish a series of short/unique messages and confirm the
    #-- messages received are consistent with what was sent and received
    #-- in-order
    logging.info("executing test")
    NumPortsToTest=20
    portList=[random.randint(5000,9999) for i in range(1,NumPortsToTest)]
    for port in portList:
      pubEndpt='tcp://*:%d'%(port)
      subEndpt='tcp://localhost:%d'%(port)
      self._singleThreadPubSubTest(pubEndpt,subEndpt)

  def _singleThreadPubSubVaryMsgLenTest(self, pubEndpt, subEndpt):
    pub=dividere.connection.Publisher(pubEndpt)
    sub=dividere.connection.Subscriber(subEndpt)
    time.sleep(1); #--let subscribers get set up before sending initial msg

    MaxMsgLen=81920
    for i in range(1,MaxMsgLen):
      msg=b'X'*i
      pub.send(msg)
      received=sub.recv()
      self.assertTrue(msg==received)


  def test03(self):
    logging.info("executing test")
    Port=dividere.connection.PortManager.acquire()
    self._singleThreadPubSubVaryMsgLenTest('tcp://*:%d'%(Port),'tcp://localhost:%d'%(Port))

  def test04(self):
    logging.info("executing test")
    ipcTmpDir='/tmp/feeds'
    if not os.path.exists(ipcTmpDir):
      os.mkdir(ipcTmpDir) 
    endPt='ipc://%s/0'%(ipcTmpDir)
    self._singleThreadPubSubVaryMsgLenTest(endPt,endPt)

  def _singleThreadReqRepTest(self, reqEndpt, repEndpt):
    req=dividere.connection.Request(reqEndpt)
    rep=dividere.connection.Response(repEndpt)
    time.sleep(1); #--let subscribers get set up before sending initial msg

    N=10
    for i in range(0,N):
      msg=b"message-%03d"%(i)
      req.send(msg)
      received=rep.recv()
      logging.debug("%s == %s"%(msg,received))
      self.assertTrue(msg==received)

      rep.send(msg)
      received=req.recv()
      self.assertTrue(msg==received)

  def test05(self):   
    logging.info("executing test")
    Port=dividere.connection.PortManager.acquire()
    reqEndPt='tcp://localhost:%d'%(Port)
    repEndPt='tcp://*:%d'%(Port)
    self._singleThreadReqRepTest(reqEndPt, repEndPt)

  @staticmethod
  def _responseTestThread(endPoint):
    logging.debug("reply thread connecting to: %s"%(endPoint))
    rep=dividere.connection.Response(endPoint)
    msg=rep.recv()
    rep.send(msg)
    rep=None

  def _testReqRepCardinality(self, N):
    Port=dividere.connection.PortManager.acquire()
    portList=[i for i in range(Port,Port+N)]
    tidList=[]
    for port in portList:
      repEndPt='tcp://*:%d'%(port)
      tidList.append(threading.Thread(target=connectionTests._responseTestThread, args=(repEndPt,)))
    for tid in tidList:
      tid.start()

    endPointList=[]
    for port in portList:
      endPointList.append('tcp://localhost:%d'%(port))
    logging.debug("req thread connecting to: %s"%(str(endPointList)))
    req=dividere.connection.Request(endPointList)

    for i in range(0,N):
      msg=b'abcd'
      req.send(msg)
      reply=req.recv()
      self.assertTrue(reply==msg)
      time.sleep(1);

    req=None
  
  def test06(self):
    #--test a 1-1 req/rep pairing, send a message, bounce it back, confirm what you sent is what
    #-- you received
    logging.info("executing test")
    N=1
    self._testReqRepCardinality(N)

  def test07(self):
    #--test a simple 1-N req/rep pairing, send a message, bounce it back, confirm what you sent 
    #-- is what you received
    logging.info("executing test")
    N=2
    self._testReqRepCardinality(N)

  def test08(self):
    #--test a 1-N req/rep pairing, send a message, bounce it back, confirm what you sent is what
    #-- you received
    logging.info("executing test")
    for i in range(1,10):
      self._testReqRepCardinality(i)

  def test09(self):
     #--test broker component, req/rep connect to it and can exchange messaging
     logging.info("executing test")
     fPort=dividere.connection.PortManager.acquire()
     bPort=dividere.connection.PortManager.acquire()
     proxy=dividere.connection.Proxy(fPort,bPort)

     req=dividere.connection.Request("tcp://localhost:%d"%(fPort))
     rep=dividere.connection.Response("tcp://localhost:%d"%(bPort))

     for i in range(0,5000):
       s=b'message %4d'%(i)
       req.send(s)
       m = rep.recv()
       rep.send(m)
       m=req.recv()
       self.assertTrue(m==s, "%s == %s"%(s,m))
     proxy.stop()
     req=None
     rep=None


  class ClientTask:
    def __init__(self,endPt, obj):
      self.tid_=threading.Thread(target=self.run, args=(endPt,))
      self.tid_.start()
      self.obj_=obj

    def stop(self):
      self.tid_.join()
  
    def run(self, endPt):
      sock=dividere.connection.Dealer(endPt)
      tId=threading.get_native_id()
      for i in range(0,1000):
        msg=b'message %d.%d'%(tId,i)
        sock.send(msg)
        reply=sock.recv()
        logging.debug('client reply: %s %s'%(msg,reply))
        m1=re.match('message (.*)',msg.decode('utf-8'))
        m2=re.match('ack (.*)',reply.decode('utf-8'))
        self.obj_.assertTrue(m1.group(1)==m2.group(1))

  class WorkerTask:
    def __init__(self,endPt):
      self.done_=False
      self.tid_=threading.Thread(target=self.run, args=(endPt,))
      self.tid_.start()
  
    def stop(self):
      self.done_=True
  
    def run(self, endPt):
      sock=dividere.connection.Dealer(endPt)
      while(not self.done_):
        if sock.wait(1):
          msg=sock.recv()
          S=msg[1].decode('utf-8')
          m=re.match('message (.*)',S)
          n=str(m.group(1))
          reply=b'ack %s'%(n.encode('utf-8'))
          sock.send((msg[0],reply))
  
  def test10(self):
    #--test simple dealer <=> router/dealer <=> dealer configuration
    #== by sending asychronous messages, and confirming ack id matches
    #-- the msg id
    fePort=dividere.connection.PortManager.acquire()
    bePort=dividere.connection.PortManager.acquire()
    c=self.ClientTask('tcp://localhost:%d'%(fePort),self)
    w=self.WorkerTask('tcp://localhost:%d'%(bePort))
    p=dividere.connection.Proxy(fePort,bePort)
    time.sleep(1)
  
    c.stop()
    w.stop()
    p.stop()
  
  def _test11(self,numClients,numWorkers):
    #--test multi-threaded dealer <=> router/dealer <=> dealer configuration
    #== by sending asychronous messages, and confirming ack id matches
    #-- the msg id
    #-- this primarily confirms the response messages are properly routed
    #-- back to the original sender client (ie. route back design works)
    fePort=dividere.connection.PortManager.acquire()
    bePort=dividere.connection.PortManager.acquire()
    cList=[self.ClientTask('tcp://localhost:%d'%(fePort),self) for i in range(0,numClients)]
    wList=[self.WorkerTask('tcp://localhost:%d'%(bePort)) for i in range(0,numWorkers)]
    p=dividere.connection.Proxy(fePort,bePort)
    time.sleep(1)
  
    for c in cList:
      c.stop()
    for w in wList:
      w.stop()
    p.stop()

  def test11(self):
    #--test multi-threaded dealer <=> router/dealer <=> dealer configuration
    #== by sending asychronous messages, and confirming ack id matches
    #-- the msg id
    #-- this primarily confirms the response messages are properly routed
    #-- back to the original sender client (ie. route back design works)
    self._test11(1,1)
    self._test11(5,1)
    self._test11(10,1)
    self._test11(1,5)
    self._test11(5,5)
    self._test11(10,5)
    self._test11(50,20)
