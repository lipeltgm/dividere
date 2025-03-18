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
    portList=[dividere.connection.PortManager.acquire() for i in range(0,NumPortsToTest)]
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
    portList=[dividere.connection.PortManager.acquire() for i in range(0,N)]

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
    logging.info("executing test")
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
    logging.info("executing test")
    self._test11(1,1)
    self._test11(5,1)
    self._test11(10,1)
    self._test11(1,5)
    self._test11(5,5)
    self._test11(10,5)
    self._test11(50,20)

  def test12(self):
    #--Perform simple test using load balancing pattern routing via sockets,
    #-- create client request socket, server dealer socket, register the dealer
    #-- and then send client request, have server bounce back the received message
    #-- which allows testing round-trip routing; client-server-client
    logging.info("executing test")
    fePort=dividere.connection.PortManager.acquire()
    bePort=dividere.connection.PortManager.acquire()
#   fePort=5555
#   bePort=5556
    p=dividere.connection.LoadBalancingPattern.Broker(zmq.ROUTER, fePort, zmq.ROUTER, bePort)
    s=dividere.connection.Dealer('tcp://localhost:%d'%(bePort))
    s.send(dividere.connection.LoadBalancingPattern.Broker.ServerRegisterMsg)

    time.sleep(2)
    c=dividere.connection.Request('tcp://localhost:%d'%(fePort))
    testMsg=b'some test message'
    c.send(testMsg)

    #--emulate server ping-ponging received msgs
    while s.wait(1000):
      msg=s.recv()
      logging.debug('server got %s'%(str(msg)))
      s.send(msg)

    self.assertTrue(c.wait(2000))
    self.assertTrue(c.recv() == testMsg)

    p.stop()

  def test13(self):
    #--manual/debugging test, connect worker and broker, let them hb each other for a bit
    #-- then stop worker and confirm the broker detects the dead worker
    logging.info("executing test")
    fePort=dividere.connection.PortManager.acquire()
    bePort=dividere.connection.PortManager.acquire()

    p=dividere.connection.LoadBalancingPattern.Broker(zmq.ROUTER, fePort, zmq.ROUTER, bePort)
    w=dividere.connection.LoadBalancingPattern.Worker('tcp://localhost:%d'%(bePort))
    time.sleep(dividere.connection.LoadBalancingPattern.Broker.HeartbeatRate*3)
    w.stop()
    time.sleep(dividere.connection.LoadBalancingPattern.Broker.HeartbeatRate*3)
    p.stop()

  def test14(self):
    fePort=5555
    c=dividere.connection.LoadBalancingPattern.Client('tcp://localhost:%d'%(fePort))
    testMsg=b'some test message'
    c.send(testMsg)
    timeOutMs=3000
    m=c.recv(timeOutMs)
    self.assertTrue(m==None)


  def _test15(self, cSock, sSock):
    #--test synchronous round-trip using socket pair
    #-- Note:
    #--   Dealer/Response pairs are valid, _but_ sent messages must be preceeded by an empty
    #--    index frame to emulate the req socket protocol
    isDealerResponsePair=type(cSock)==dividere.connection.Dealer and type(sSock)==dividere.connection.Response
  
    msg=b'foo to you'
    if isDealerResponsePair:
      cSock.sendWithEmptyFrame(msg)
    else:
      cSock.send(msg)
    m1=sSock.recv()
    logging.debug('server got %s'%(m1))
    self.assertTrue(m1==msg)
    sSock.send(m1)
    m2=cSock.recv()
    logging.debug('client got %s'%(m1))
    if isDealerResponsePair:
      self.assertTrue(m2[1]==msg)
    else:
      self.assertTrue(m2==msg)
    cSock=None
    sSock=None
  
  def test15(self):
    #--test valid peer-to-peer direct connections for communications module objects; req/rep, dealer/rep, dealer/dealer
    port=dividere.connection.PortManager.acquire()
    self._test15(dividere.connection.Request("tcp://localhost:%d"%(port)), dividere.connection.Response("tcp://*:%d"%(port)))
    self._test15(dividere.connection.Dealer("tcp://localhost:%d"%(port)), dividere.connection.Response("tcp://*:%d"%(port)))
    self._test15(dividere.connection.Dealer("tcp://localhost:%d"%(port)), dividere.connection.Dealer("tcp://*:%d"%(port)))
  
  
  def _test16(self, cSock, sSock):
    #--test valid peer-to-peer direct connections to a router service socket for connection sockets
    msg=b'foo to you'
    cSock.send(msg)
    m1 = sSock.recv_multipart()
    logging.debug(m1)
    self.assertTrue(m1[-1]==msg); # note: m1=[client id, identity frame (for cSock sock), payload]
    sSock.send_multipart(m1)
    m2=cSock.recv()
    self.assertTrue(msg==m2)

  def test16(self):
      #--test router connections with compliant connection sockets
     port=dividere.connection.PortManager.acquire()
     ctx=zmq.Context()
     feSock=ctx.socket(zmq.ROUTER)
     feSock.bind('tcp://*:%d'%(port))
  
     self._test16(dividere.connection.Request("tcp://localhost:%d"%(port)),feSock)
     self._test16(dividere.connection.Dealer("tcp://localhost:%d"%(port)),feSock)
  
     feSock.close()
     ctx.term()
  
  def _test17(self, cSock, sSock):
    fePort=int(cSock.socket_.last_endpoint.decode('utf-8').split(':')[2])
    bePort=int(sSock.socket_.last_endpoint.decode('utf-8').split(':')[2])
    b=dividere.connection.LoadBalancingPattern.Broker(zmq.ROUTER, fePort, zmq.ROUTER, bePort)
  
    sSock.send(dividere.connection.LoadBalancingPattern.Broker.ServerRegisterMsg)
  
    time.sleep(1)
    msg=b'some test message'
    cSock.send(msg)
  
    sSock.send(sSock.recv()); #--server echo back
    reply=cSock.recv()
    logging.debug("client received: %s"%(reply))
    self.assertTrue(reply==msg)
  
    b.stop()
    cSock=None
    sSock=None
  
  def _test17(self, cSock, sSock):
    fePort=int(cSock.socket_.last_endpoint.decode('utf-8').split(':')[2])
    bePort=int(sSock.socket_.last_endpoint.decode('utf-8').split(':')[2])
    b=dividere.connection.LoadBalancingPattern.Broker(zmq.ROUTER, fePort, zmq.ROUTER, bePort)

    sSock.send(dividere.connection.LoadBalancingPattern.Broker.ServerRegisterMsg)

    time.sleep(1)
    msg=b'some test message'
    cSock.send(msg)

    sSock.send(sSock.recv()); #--server echo back
    reply=cSock.recv()
    logging.debug("client received: %s"%(reply))
    assert(reply==msg)

    b.stop()
    cSock=None
    sSock=None

  def test17(self):
    fePort=dividere.connection.PortManager.acquire()
    bePort=dividere.connection.PortManager.acquire()
    self._test17(dividere.connection.Dealer('tcp://localhost:%d'%(fePort)),dividere.connection.Dealer('tcp://localhost:%d'%(bePort)))
    self._test17(dividere.connection.Request('tcp://localhost:%d'%(fePort)),dividere.connection.Dealer('tcp://localhost:%d'%(bePort)))
  
  # @todo: needs design/framework work to connect request connection
  # self._test17(dividere.connection.Dealer('tcp://localhost:%d'%(fePort)),dividere.connection.Request('tcp://localhost:%d'%(bePort)))
  
  
