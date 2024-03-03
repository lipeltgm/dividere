import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
import threading
import time


class MyService(dividere.service.Service):
  def handleMyServiceReq(self,msg):
    logging.debug("got request, processing")
    reply=TestMsg.MyServiceRep()
    self.sock_.send(reply)

class serviceTests(unittest.TestCase):
  def test00(self):
    logging.info("executing test")
    nsServer=dividere.registry.ServiceRegistry.Server()

    obj=MyService()

    nsClient=dividere.registry.ServiceRegistry.Client('localhost',dividere.registry.ServiceRegistry.Server.port)
    m=nsClient.lookupService(obj.name_)
    self.assertTrue(m.server != 'unavailable' and m.port != 0)
    logging.debug("m: %s"%(str(m)))
    endPt="tcp://%s:%s"%('localhost', m.port)
    logging.debug("endPt %s"%(endPt))
    sock=dividere.messaging.Request(endPt)
    msg=TestMsg.MyServiceReq()
    sock.send(msg)
    reply=sock.recv()

    obj.stop()
    nsServer.stop()

  def delayedNameService(self, sleepSecs, runForSecs):
    time.sleep(sleepSecs)
    logging.debug("ns starting")
    nsServer=dividere.registry.ServiceRegistry.Server()
    time.sleep(runForSecs)
    nsServer.stop()
    logging.debug("ns stopped")

  def test01(self):
    #--test service initialization for delayed available name service
    #-- the expectation is service will send registration message and wait
    #-- for response, unavailable name service will block service 'til it comes
    #-- on-line
    logging.info("executing test")
    tid=threading.Thread(target=self.delayedNameService, args=(10.0,10.0,))
    tid.start()

    obj=MyService()
    nsClient=dividere.registry.ServiceRegistry.Client('localhost',dividere.registry.ServiceRegistry.Server.port)
    m=nsClient.lookupService(obj.name_)
    logging.debug("m: %s"%(str(m)))
    self.assertTrue(m.server != 'unavailable' and m.port != 0)
    endPt="tcp://%s:%s"%('localhost', m.port)
    logging.debug("endPt %s"%(endPt))
    sock=dividere.messaging.Request(endPt)
    msg=TestMsg.MyServiceReq()
    sock.send(msg)
    reply=sock.recv()
    tid.join()
    obj.stop()
    assert(reply and TestMsg.MyServiceRep().__class__.__name__==reply.__class__.__name__)

  def test02(self):
    #--test service re-registration as a result of a terminated/restarted name service
    logging.info("executing test")
    tid1=threading.Thread(target=self.delayedNameService, args=(0,5.0,))
    tid1.start()
    obj=MyService()
    tid1.join()

    tid2=threading.Thread(target=self.delayedNameService, args=(5.0,5.0,))
    tid2.start()
    time.sleep(8.0)
    nsClient=dividere.registry.ServiceRegistry.Client('localhost',dividere.registry.ServiceRegistry.Server.port)
    m=nsClient.lookupService(obj.name_)
    logging.debug("m: %s"%(str(m)))
    self.assertTrue(m.server != 'unavailable' and m.port != 0)
    tid2.join()
    obj.stop()
