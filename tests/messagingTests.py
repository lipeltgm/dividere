import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
import random
import uuid
import time

class messagingEncoderTests(unittest.TestCase):
  @staticmethod
  def testMsg01Creator():
    retVal=TestMsg.testMsg01()
    retVal.field1=str(uuid.uuid4())
    retVal.field2=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg01Creator():
    retVal=TestMsg.testDtMsg01()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg02Creator():
    retVal=TestMsg.testDtMsg02()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg03Creator():
    retVal=TestMsg.testDtMsg03()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg04Creator():
    retVal=TestMsg.testDtMsg04()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg05Creator():
    retVal=TestMsg.testDtMsg05()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg06Creator():
    retVal=TestMsg.testDtMsg06()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg07Creator():
    retVal=TestMsg.testDtMsg07()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg08Creator():
    retVal=TestMsg.testDtMsg08()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg09Creator():
    retVal=TestMsg.testDtMsg09()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg10Creator():
    retVal=TestMsg.testDtMsg10()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg11Creator():
    retVal=TestMsg.testDtMsg11()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg12Creator():
    retVal=TestMsg.testDtMsg12()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg13Creator():
    retVal=TestMsg.testDtMsg13()
    retVal.field1=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg14Creator():
    retVal=TestMsg.testDtMsg14()
    retVal.field1='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return retVal

  @staticmethod
  def testDtMsg15Creator():
    retVal=TestMsg.testDtMsg15()
    retVal.field1=b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return retVal

  @staticmethod
  def testNestedMsg01Creator():
    retVal=TestMsg.testNestedMsg01()
    retVal.field1.CopyFrom(messagingEncoderTests.testDtMsg01Creator())
    return retVal

  @staticmethod
  def testNestedMsg02Creator():
    retVal=TestMsg.testNestedMsg02()
    retVal.field1.CopyFrom(messagingEncoderTests.testNestedMsg01Creator())
    return retVal

  @staticmethod
  def msgFactory(msg):
    #--use the incoming message to call the appropriate
    #-- message field population
    fx='messagingEncoderTests.%sCreator()'%(msg.__class__.__name__)
    return eval(fx)

  def test00(self):
    #--encode/decode a simple message and confirm the decoded
    #-- message is identical to the original
    logging.info("executing test")
    self.assertTrue(True)
    encoder=dividere.messaging.ProtoBuffEncoder()
    decoder=dividere.messaging.ProtoBuffDecoder()

    msg=TestMsg.testMsg01()
    msg=self.msgFactory(TestMsg.testMsg01())
    envMsg=encoder.encode(msg)
    msg2=decoder.decode(envMsg)
    self.assertTrue(msg==msg2)

  def test01(self):
    #--encode/decode a series of messages each with a different
    #-- datatype and confirm the decoded message is identical
    #-- to the original
    logging.info("executing test")
    encoder=dividere.messaging.ProtoBuffEncoder()
    decoder=dividere.messaging.ProtoBuffDecoder()

    for msgTemplate in [TestMsg.testDtMsg01(), TestMsg.testDtMsg02(), 
                        TestMsg.testDtMsg03(), TestMsg.testDtMsg04(), 
                        TestMsg.testDtMsg05(), TestMsg.testDtMsg06(), 
                        TestMsg.testDtMsg07(), TestMsg.testDtMsg08(), 
                        TestMsg.testDtMsg09(), TestMsg.testDtMsg10(), 
                        TestMsg.testDtMsg11(), TestMsg.testDtMsg12(), 
                        TestMsg.testDtMsg13(), TestMsg.testDtMsg14(), 
                        TestMsg.testDtMsg15(), TestMsg.testNestedMsg01()]:
      for i in range(0,1000):
        msg=self.msgFactory(msgTemplate)
        envMsg=encoder.encode(msg)
        msg2=decoder.decode(envMsg)
        self.assertTrue(msg==msg2)

  def test01(self):
    logging.info("executing test")
    encoder=dividere.messaging.ProtoBuffEncoder()
    decoder=dividere.messaging.ProtoBuffDecoder()
    for msgTemplate in [TestMsg.testNestedMsg01(), TestMsg.testNestedMsg02()]:
      msg=self.msgFactory(msgTemplate)
      envMsg=encoder.encode(msg)
      msg2=decoder.decode(envMsg)
      self.assertTrue(msg==msg2)

  
class messagingTests(unittest.TestCase):
  def test00(self):
    logging.info("executing test")
    Port=5555
    pub=dividere.messaging.Publisher('tcp://*:%d'%(Port))
    sub=dividere.messaging.Subscriber('tcp://localhost:%d'%(Port))
    time.sleep(1); #--sleep for late joiner
    msg=messagingEncoderTests.msgFactory(TestMsg.testDtMsg01())
    pub.send(msg)
    received=sub.recv()
    self.assertTrue(msg==received)

  def test01(self):
    logging.info("executing test")
    Port=5555
    pub=dividere.messaging.Publisher('tcp://*:%d'%(Port))
    sub=dividere.messaging.Subscriber('tcp://localhost:%d'%(Port))
    time.sleep(1)

    for msgTemplate in [TestMsg.testDtMsg01(), TestMsg.testDtMsg02(), 
                        TestMsg.testDtMsg03(), TestMsg.testDtMsg04(), 
                        TestMsg.testDtMsg05(), TestMsg.testDtMsg06(), 
                        TestMsg.testDtMsg07(), TestMsg.testDtMsg08(), 
                        TestMsg.testDtMsg09(), TestMsg.testDtMsg10(), 
                        TestMsg.testDtMsg11(), TestMsg.testDtMsg12(), 
                        TestMsg.testDtMsg13(), TestMsg.testDtMsg14(), 
                        TestMsg.testDtMsg15(), TestMsg.testNestedMsg01(), 
                        TestMsg.testNestedMsg02()]:
      msg=messagingEncoderTests.msgFactory(msgTemplate)
      pub.send(msg)
      received=sub.recv()
      self.assertTrue(msg==received)

  def test02(self):
    #--simple single-threaded test, send a message, confirm it's received
    #-- as transmitted
    logging.info("executing test")
    Port=5555
    req=dividere.messaging.Request('tcp://localhost:%d'%(Port))
    rep=dividere.messaging.Response('tcp://*:%d'%(Port))

    msg=messagingEncoderTests.msgFactory(TestMsg.testDtMsg01())
    req.send(msg)
    m2=rep.recv()
    self.assertTrue(msg==m2)
    rep.send(m2)
    m3=req.recv()
    self.assertTrue(msg==m3)

    req=None
    rep=None

  def test03(self):
    #--test a simple req/rep single-threaded exchange over a variety
    #-- of messages
    logging.info("executing test")
    Port=5555
    req=dividere.messaging.Request('tcp://localhost:%d'%(Port))
    rep=dividere.messaging.Response('tcp://*:%d'%(Port))
    time.sleep(1)

    for msgTemplate in [TestMsg.testDtMsg01(), TestMsg.testDtMsg02(), 
                        TestMsg.testDtMsg03(), TestMsg.testDtMsg04(), 
                        TestMsg.testDtMsg05(), TestMsg.testDtMsg06(), 
                        TestMsg.testDtMsg07(), TestMsg.testDtMsg08(), 
                        TestMsg.testDtMsg09(), TestMsg.testDtMsg10(), 
                        TestMsg.testDtMsg11(), TestMsg.testDtMsg12(), 
                        TestMsg.testDtMsg13(), TestMsg.testDtMsg14(), 
                        TestMsg.testDtMsg15(), TestMsg.testNestedMsg01(), 
                        TestMsg.testNestedMsg02()]:
      for i in range(0,50):
        msg=messagingEncoderTests.msgFactory(msgTemplate)
        req.send(msg)
        m2=rep.recv()
        self.assertTrue(msg==m2)
        rep.send(m2)
        m3=req.recv()
        self.assertTrue(msg==m3)

  def test04(self):
    #--test the round-robin point-to-point delivery when specifying a
    #-- series of receivers
    logging.info("executing test")
    Port=5555
    N=3

    portList=[i for i in range(Port, Port+N)]
    repList=[dividere.messaging.Response('tcp://*:%d'%(p)) for p in portList]

    endPoints=['tcp://localhost:%d'%(p) for p in portList]
    req=dividere.messaging.Request(endPoints)

    msg=messagingEncoderTests.msgFactory(TestMsg.testDtMsg01())
    for rep in repList:
      req.send(msg)
      m2=rep.recv()
      self.assertTrue(msg==m2)
      rep.send(m2)
      m3=req.recv()
      self.assertTrue(msg==m3)

    for e in repList:
      e=None
    req=None
