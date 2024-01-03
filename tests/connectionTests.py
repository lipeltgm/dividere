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
    Port=5555
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
    Port=5555
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
    Port=5555
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
    Port=5555
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
     fPort=5559
     bPort=5560
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

