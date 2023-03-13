import unittest
import logging
import dividere 
import TestMsg_pb2 as TestMsg
import random

class messagingTests(unittest.TestCase):
  @staticmethod
  def msgFactory(msg):
    retVal=None
    if isinstance(msg, TestMsg.testMsg01):
      retVal=msg
      retVal.field1='foo to you'
      retVal.field2=2
    else:
      retVal=msg
      retVal.field1=0

    return retVal

  def test00(self):
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
    logging.info("executing test")
    encoder=dividere.messaging.ProtoBuffEncoder()
    decoder=dividere.messaging.ProtoBuffDecoder()
    for i in range(1,14):
      msg=eval('TestMsg.testDtMsg%02d()'%(i))
      msg.field1=random.randint(0,32767) 
      envMsg=encoder.encode(msg)
      msg2=decoder.decode(envMsg)
      self.assertTrue(msg==msg2)
 
    msg=TestMsg.testDtMsg14()
    msg.field1='abcdefg'
    envMsg=encoder.encode(msg)
    msg2=decoder.decode(envMsg)
    self.assertTrue(msg==msg2)

    msg=TestMsg.testDtMsg15()
    msg.field1=b'123456789'
    envMsg=encoder.encode(msg)
    msg2=decoder.decode(envMsg)
    self.assertTrue(msg==msg2)
  

