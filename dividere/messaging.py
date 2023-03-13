import logging
import google.protobuf.symbol_database
import google.protobuf.descriptor_pool
import google.protobuf.message_factory
from google.protobuf.any_pb2 import Any
from dividere import MsgLib
from dividere import connection

#================================================================================
#-- Encoder/Decoder class; takes in protobuf message, encloses it in a envelope
#--  message for transport and allowd decoding from the received message
#--  primarily used in conjunction with transport classes in this package
#================================================================================
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

class Publisher:
  def __init__(self,endPoint):
    #--create pub component and encoder
    self.pub_=connection.Publisher(endPoint)
    self.encoder_=ProtoBuffEncoder()

  def __del__(self):
    self.pub_=None
    self.encoder_=None

  def send(self, msg):
    #--encode message into envelope container, then convert to
    #-- byte stream and send out wire
    env=self.encoder_.encode(msg)
    self.pub_.send(env.SerializeToString())

class Subscriber:
  @staticmethod
  def topicId(msg):
    #--translate a protobuf message into a topic name
    #--  (the beginning of the string coming across the 'wire')
    #--  used to subscribe to specific message(s)
    return '\n\x08%s'%(msg.__class__.__name__)

  def __init__(self,endPoint, msgSubList=[]):
    #--if message subscription list is empty, subscribe to all messages
    #-- otherwise subscribe to the specified messages exclusively
    # create subscriber object and decoder components
    if (len(msgSubList)==0):
      topic=''
    else:
      topic=self.topicId(msgSubList[0])
    self.sub_=connection.Subscriber(endPoint, topic)
    self.decoder_=ProtoBuffDecoder()
    for topicMsg in msgSubList[1:]:
      self.sub_.subscribe(self.topicId(topicMsg))

  def __del__(self):
    self.sub_=None
    self.decoder_=None

  def recv(self):
    #--retrieve byte stream from subscriber, parse byte stream into envelope
    #--  message, then decode and return the contained message
    S=self.sub_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)
