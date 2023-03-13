import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
import random
import uuid

class messagingEncoderTests(unittest.TestCase):
  @staticmethod
  def testMsg01Creator():
    retVal=TestMsg.testMsg01()
    retVal.field1=str(uuid.uuid4())
    retVal.field2=random.randint(0,32767)
    return retVal

  @staticmethod
  def testDtMsg01Creator():
    retVal=TestMsg.testDtMsg02()
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
                        TestMsg.testDtMsg15()]:
      for i in range(0,1000):
        msg=self.msgFactory(msgTemplate)
        envMsg=encoder.encode(msg)
        msg2=decoder.decode(envMsg)
        self.assertTrue(msg==msg2)
  
class messagingTests(unittest.TestCase):
  def test00(self):
    self.assertTrue(True)

