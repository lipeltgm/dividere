import logging
import google.protobuf.symbol_database
import google.protobuf.descriptor_pool
import google.protobuf.message_factory
#from google.protobuf.any_pb2 import Any
from dividere import MsgLib
from dividere import connection
import os
import threading
import time

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

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    return self.sub_.wait(timeOutMs)

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
      Retrieve byte stream from response, parse byte stream into envelope
       message, then decode and return the contained user message
    '''
    S=self.sock_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    return self.sock_.wait(timeOutMs)

class Response:
  '''
    Similar functionality to the Request/Response pairing in the connection
    module, differing in the expected user message being sent.  The messaging
    module specializes in sending/receiving protobuf-based messages.
  '''

  def __init__(self,endPoint):
    '''
       Allocate all necessary resources, socket and encoder/decoder pair.
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
    self.encoder_=None

  def recv(self):
    '''
      Retrieve byte stream from requester, parse byte stream into envelope
       message, then decode and return the contained user message
    '''
    S=self.sock_.recv()
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)
    return self.decoder_.decode(env)

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    return self.sock_.wait(timeOutMs)

  def send(self, msg):
    '''
      Encode message into envelope container, convert it to
      a byte stream and send out wire via the connector
    '''
    env=self.encoder_.encode(msg)
    self.sock_.send(env.SerializeToString())

class Dealer:
  '''
    General replacement for Request/Response components, but relaxes
    the strict send/receive protocol.  This component support more
    asynchronous messaging by allowing multiple send/recv functionality.
  '''

  def __init__(self,endPoint):
    '''
       Allocate all necessary resources, including socket and encoder/decoder
       pair.  All transported communications will be done in the form of a
       message envelope
    '''
    self.sock_=connection.Dealer(endPoint)
    self.decoder_=ProtoBuffDecoder()
    self.encoder_=ProtoBuffEncoder()

  def __del__(self):
    '''
      Free all allocated object resources
    '''
    self.sock_=None
    self.decoder_=None
    self.encoder_=None

  def recv(self):
    '''
      Return value _may_ be a single message, or a tuple (id,msg)
      depending on usage.  Routed messages (e.g. one thru a router, 
      may include the 'identity' (route) of the message so it can be
      routed back to the originating sender.  
    '''
    P=self.sock_.recv()
    if isinstance(P,tuple):
      id=P[0]
      S=P[1]
    else:
      S=P
    env=MsgLib.msgEnvelope()
    env.ParseFromString(S)

    if isinstance(P,tuple):
      return (id, self.decoder_.decode(env))
    else:
      return self.decoder_.decode(env)

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    return self.sock_.wait(timeOutMs)

  def send(self, msg):
    '''
      Encode message into envelope container, convert it to
      a byte stream and send out wire via the connector
    '''
    if isinstance(msg,tuple):
      id=msg[0]
      env=self.encoder_.encode(msg[1])
      self.sock_.send((id,env.SerializeToString()))
    else:
      env=self.encoder_.encode(msg)
      self.sock_.send(env.SerializeToString())


class MsgReactor:
  '''
    Abstraction to support active-thread which listens to a vector of a
    varying consumer messaging objects (e.g. Sub, Response, ...), decoding
    the incoming message and calling a specialized hander method (provided mostly
    by derived classes).
  '''
  def __init__(self, obj):
    '''
      Spawn an independent thread which monitors the specified consumer message
      objects, also append an additional object to support multi-threaded signalling
      to support halting the thread when no longer needed.
      (ipc pub/sub is used to signal thread termination)
    '''
    self.done_=False
    if isinstance(obj, list):
      self.objList_=obj
    else:
      self.objList_=[obj]

    self.ipcName_='ipc:///tmp/ipc-%d'%(os.getpid())
    self.objList_.append(Subscriber(self.ipcName_))
    self.tid_=threading.Thread(target=self.msgHandler,args=())
    self.tid_.start()

  def __del__(self):
    '''
      Deallocate all messaging objects, which in-turn terminates the zmq contexts
    '''
    for e in self.objList_:
      e=None
    self.objList_=None

  def stop(self):
    '''
      Signal thread to complete, wait for it to complete
    '''
    pub=Publisher(self.ipcName_)
    shutdownMsg=MsgLib.ShutdownEvent()
    time.sleep(1); #--accomodate late joiner
    pub.send(shutdownMsg)
    self.tid_.join()

  def msgHandler(self):
    '''
      This method encapsulates the 'active object' logic, while 'not done'
      poll/wait for an inbound message from any messaging object in the list
      if a message exists, grab it and call a specialized message handler function
      (based on message name), provide the messaging object it arrived on
      to allow handler to choose to send reply (for compliant messaging objects like Req/Rep)
    '''
    while not self.done_:
      for el in self.objList_:
        gotMsg=el.wait(1)
        if gotMsg:
          msg=el.recv()
          msgName=msg.__class__.__name__
          fx='self.handle%s(el,msg)'%(msgName)
          eval(fx)

  def handleShutdownEvent(self,obj,msg):
    '''
      Set the done flag, this is done from the thread to avoid need for necessary guards
    '''
    self.done_=True;


