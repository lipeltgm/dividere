#!/usr/bin/python3
import unittest
import logging
import sys
import dividere
import time

class connectionTests(unittest.TestCase):
  def test00(self):
    logging.info("executing test")
    Port=5555
    pub=dividere.connection.Publisher('tcp://*:%d'%(Port))
    sub=dividere.connection.Subscriber('tcp://localhost:%d'%(Port))
    time.sleep(1); #--let subscribers get set up before sending initial msg

    N=10
    for i in range(0,N):
      msg=b"message-%03d"%(i)
      pub.send(msg)
      received=sub.recv()
      logging.debug("%s == %s"%(msg,received))
      self.assertTrue(msg==received)


  def test01(self):
    logging.info("executing test")
    self.assertTrue(True)


  def test02(self):
    logging.info("executing test")
    self.assertTrue(True)

  def test03(self):
    logging.info("executing test")
    self.assertTrue(True)

  def test04(self):
    logging.info("executing test")
    self.assertTrue(True)

  def test05(self):
    logging.info("executing test")
    self.assertTrue(True)

