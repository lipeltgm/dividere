import logging
import google.protobuf.symbol_database
import google.protobuf.descriptor_pool
import google.protobuf.message_factory
from google.protobuf.any_pb2 import Any
from dividere import MsgLib

class ProtoBuffEncoder:
  def __init__(self):
    pass

  def encode(self, msg):
    env=MsgLib.msgEnvelope()
    env.msgName=msg.__class__.__name__
    env.msg.Pack(msg)
    return env

class ProtoBuffDecoder:
  def __init__(self):
    pass

  def decode(self, msgEnv):
    msgDesc=google.protobuf.descriptor_pool.Default().FindMessageTypeByName(msgEnv.msgName)
    factory=google.protobuf.message_factory.MessageFactory()
    msgClass=factory.GetPrototype(msgDesc)
    c=msgClass()
    msgEnv.msg.Unpack(c)
    return c

