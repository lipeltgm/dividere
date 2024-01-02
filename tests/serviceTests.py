import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
#import random
#import uuid
#import time
#from dividere import MsgLib
#import socket


class MyClass(dividere.service.Service):
  def handleMyClassReq(self,msg):
    logging.debug("got request, processing")
    reply=TestMsg.MyClassRep()
    self.sock_.send(reply)

class serviceTests(unittest.TestCase):
  def test00(self):
    logging.info("executing test")
    nsServer=dividere.registry.ServiceRegistry.Server(dividere.registry.ServiceRegistry.Server.port)

    obj=MyClass()

    nsClient=dividere.registry.ServiceRegistry.Client('localhost',dividere.registry.ServiceRegistry.Server.port)
    m=nsClient.lookupService(obj.name_)
    logging.debug("m: %s"%(str(m)))
    endPt="tcp://%s:%s"%('localhost', m.port)
    logging.debug("endPt:",endPt)
    sock=dividere.messaging.Request(endPt)
    msg=TestMsg.MyClassReq()
    sock.send(msg)
    reply=sock.recv()

    obj.stop()
    nsServer.stop()
