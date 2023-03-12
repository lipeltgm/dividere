#!/usr/bin/python3
import unittest
import logging
import sys
import dividere
import time
import os
import random

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

