import logging
import google.protobuf.symbol_database
import google.protobuf.descriptor_pool
import google.protobuf.message_factory
#from google.protobuf.any_pb2 import Any
from dividere import MsgLib
from dividere import connection

#================================================================================
#-- Encoder/Decoder class; takes in protobuf message, encloses it in a envelope
#--  message for transport and allowd decoding from the received message
#--  primarily used in conjunction with transport classes in this package
#================================================================================
class ProtoBuffEncoder:
  '''
    This class suports taking in a user protobuf message and encode/pack
    into a container message for transport.  This is one end of a encode/decode
    sequence used when sending a user message through a socket while allowing
    a variety of messages to be sent thru a shared socket channel.
    This is one end of the encode/decode sequence; encoding done at the sending
    end, decoding at the receiving end.
  '''
  def __init__(self):
    '''
      Initialize object resources
    '''
    pass

  def encode(self, msg):
    '''
      Encapsulate the specified message into a container message for
      transport and return it to the caller
    '''
    env=MsgLib.msgEnvelope()
    env.msgName=msg.__class__.__name__
    env.msg.Pack(msg)
    return env

class ProtoBuffDecoder:
  '''
    This class suports taking in a user protobuf message and encode/pack
    into a container message for transport.  This is one end of a encode/decode
    sequence used when sending a user message through a socket while allowing
    a variety of messages to be sent thru a shared socket channel.
    This is one end of the encode/decode sequence; encoding done at the sending
    end, decoding at the receiving end.
  '''
  def __init__(self):
    pass

  def decode(self, msgEnv):
    '''
      Extract the user message from the specified container message
      and return it to the caller.
    '''
    msgDesc=google.protobuf.descriptor_pool.Default().FindMessageTypeByName(msgEnv.msgName)
    factory=google.protobuf.message_factory.MessageFactory()
    msgClass=factory.GetPrototype(msgDesc)
    c=msgClass()
    msgEnv.msg.Unpack(c)
    return c

class Publisher:
  '''
    Similar functionality to the Publish/Subscriber pairing in the connection
    module, differing in the expected user message being sent.  The messaging
    module specializes in sending/receiving protobuf-based messages.
  '''
  def __init__(self,endPoint):
    '''
      Create a publisher connection and encoder
    '''
    #--create pub component and encoder
    self.pub_=connection.Publisher(endPoint)
    self.encoder_=ProtoBuffEncoder()

  def __del__(self):
    '''
      Free allocated object resources
    '''
    self.pub_=None
    self.encoder_=None

  def send(self, msg):
    '''
      Encode message into envelope container, convert it to
      a byte stream and send out wire via the connector
    '''
    env=self.encoder_.encode(msg)
    self.pub_.send(env.SerializeToString())

class Subscriber:
  '''
    Similar functionality to the Publish/Subscriber pairing in the connection
    module, differing in the expected user message being sent.  The messaging
    module specializes in sending/receiving protobuf-based messages.
  '''
  @staticmethod
  def topicId(msg):
    '''
      Translate a protobuf message into a topic name
      (the beginning of the string coming across the 'wire')
      used to subscribe to specific message(s)
      Note: expected usage is internal to the module, not
      intended for external use
    '''
    return '\n\x08%s'%(msg.__class__.__name__)

  def __init__(self,endPoint, msgSubList=[]):
    '''
       Allocate all necessary resources, subscribe to messages.
       If message subscription list is empty, subscribe to all messages
       otherwise subscribe to the specified messages exclusively
       create subscriber object and decoder components
    '''
    if (len(msgSubList)==0):
      topic=''
    else:
      topic=self.topicId(msgSubList[0])
    self.sub_=connection.Subscriber(endPoint, topic)
    self.decoder_=ProtoBuffDecoder()
    for topicMsg in msgSubList[1:]:
      self.sub_.subscribe(self.topicId(topicMsg))

  def __del__(self):
    '''
      Free all allocated object resources
    '''
    self.sub_=None
    self.decoder_=None

  def recv(self):
    '''
      Retrieve byte stream from subscriber, parse byte stream into envelope
       message, then decode and return the contained user message
    '''
    S=self.sub_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)

class Request:
  '''
    Similar functionality to the Request/Response pairing in the connection
    module, differing in the expected user message being sent.  The messaging
    module specializes in sending/receiving protobuf-based messages.
  '''
  def __init__(self,endPoint):
    '''
      Create a request connection and encoder
    '''
    #--create req component and encoder
    self.sock_=connection.Request(endPoint)
    self.encoder_=ProtoBuffEncoder()
    self.decoder_=ProtoBuffDecoder()

  def __del__(self):
    '''
      Free allocated object resources
    '''
    self.sock_=None
    self.encoder_=None

  def send(self, msg):
    '''
      Encode message into envelope container, convert it to
      a byte stream and send out wire via the connector
    '''
    env=self.encoder_.encode(msg)
    self.sock_.send(env.SerializeToString())

  def recv(self):
    '''
      Retrieve byte stream from repscriber, parse byte stream into envelope
       message, then decode and return the contained user message
    '''
    S=self.sock_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)

class Response:
  '''
    Similar functionality to the Request/Response pairing in the connection
    module, differing in the expected user message being sent.  The messaging
    module specializes in sending/receiving protobuf-based messages.
  '''

  def __init__(self,endPoint):
    '''
       Allocate all necessary resources, repscribe to messages.
       If message repscription list is empty, repscribe to all messages
       otherwise repscribe to the specified messages exclusively
       create repscriber object and decoder components
    '''
    self.sock_=connection.Response(endPoint)
    self.decoder_=ProtoBuffDecoder()
    self.encoder_=ProtoBuffEncoder()

  def __del__(self):
    '''
      Free all allocated object resources
    '''
    self.sock_=None
    self.decoder_=None

  def recv(self):
    '''
      Retrieve byte stream from repscriber, parse byte stream into envelope
       message, then decode and return the contained user message
    '''
    S=self.sock_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)

  def send(self, msg):
    '''
      Encode message into envelope container, convert it to
      a byte stream and send out wire via the connector
    '''
    env=self.encoder_.encode(msg)
    self.sock_.send(env.SerializeToString())

