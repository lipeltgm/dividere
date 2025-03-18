import logging
import google.protobuf.symbol_database
import google.protobuf.descriptor_pool
import google.protobuf.message_factory
import collections
from dividere import MsgLib
from dividere import connection
from dividere import messaging
import datetime
import os
import threading
import time
import multiprocessing
import sys
import zmq
import uuid

logger=logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

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
    msgClass=google.protobuf.message_factory.GetMessageClass(msgDesc)
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
    self.endPoint_=endPoint
    self.pub_=connection.Publisher(self.endPoint_)
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
    self.endPoint_=endPoint
    self.sub_=connection.Subscriber(self.endPoint_, topic)
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
    self.endPoint_=endPoint
    self.sock_=connection.Request(self.endPoint_)
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
    self.endPoint_=endPoint
    self.sock_=connection.Response(self.endPoint_)
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
    self.endPoint_=endPoint
    self.sock_=connection.Dealer(self.endPoint_)
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

  def sendWithEmptyFrame(self, msg):
    '''
      Send message but with preceeding empty identity frame, used to emulate
      request message protocol (e.g. Dealer-Response connections)
    '''
    env=self.encoder_.encode(msg)
    self.sock_.sendWithEmptyFrame(env.SerializeToString())

class MtMsgReactor:
  '''
    Multi-Threaded Msg Reactor
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

    self.ipcName_='ipc:///tmp/ipc-%s'%(uuid.uuid4())
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

  def idle(self):
    '''
      Method called between processing messages, meant to be extended by child classes
      when necessary
    '''
    pass

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
    try:
      while not self.done_:
        for el in self.objList_:
          gotMsg=el.wait(1)
          if gotMsg:
            msg=el.recv()
            if isinstance(msg, tuple):
              fx='self.handle%s(el,msg[0],msg[1])'%(msg[1].__class__.__name__)
              logger.debug("calling %s() callback"%(fx))
              eval(fx)
            else:
              msgName=msg.__class__.__name__
              fx='self.handle%s(el,msg)'%(msgName)
              logger.debug("calling %s() callback"%(fx))
              eval(fx)
        self.idle(); #--@TODO; runs way too fast
      logger.debug("...done %s"%(self.__class__.__name__))
    except Exception as e:
      logger.error("caught exception %s"%(str(e)))

  def handleShutdownEvent(self,obj,msg):
    '''
      Set the done flag, this is done from the thread to avoid need for necessary guards
    '''
    self.done_=True;


class MpMsgReactor:
  '''
    Multi-Process Msg Reactor
    Multi-process (MP) abstraction, rather than multi-threaded, to take full advantage of 
    processor cores.  Note, the constructor provides a string list of messaging components
    rather than an actual list of objects because they must be created in the background process
    different than threaded usage.  
    Derived classes are intended to specialize initialization method that is invoked within the 
    background process to initialize resources (e.g. def initThread(self))
  '''
  def __init__(self, obj):
    '''
      Initialize necessary components, shutdown pub/sub uses tcp endpoints to support multi-process
      communications.  
    '''
    if isinstance(obj, list):
      objList=obj
    else:
      objList=[obj]
    shutdownPort=connection.PortManager.acquire()
    self.shutdownPub_=Publisher('tcp://*:%d'%(shutdownPort))
    time.sleep(1); #--give time for late joiner
    self.tid_=multiprocessing.Process(target=self.msgHandler,args=(objList,'tcp://localhost:%d'%(shutdownPort)))
    self.tid_.start()

  def __del__(self):
    '''
      Free resources created by client process
    '''
    self.shutdownPub_=None

  def stop(self):
    '''
      Signal termination and await process completion.
    '''
    self.shutdownPub_.send(MsgLib.ShutdownEvent())
    self.tid_.join()

  def msgHandler(self,objList,shutdownEndPt):
    '''
      Background process callback, iterates over specified message object list
      looking for available messages, then invokes the associated callback
      based on message name specialized by the derived class.  Inbound shutdown
      event is handled by this class, which flags completion of the task.
    '''
    objList_=[]
    for e in objList:
      logger.debug("calling %s() callback"%(e))
      objList_.append(eval(e))
    objList_.append(Subscriber(shutdownEndPt))

    self.initThread()

    self.done_ = False
    while not self.done_:
      for el in objList_:
        gotMsg=el.wait(1)
        if gotMsg:
          msg=el.recv()
          if isinstance(msg, tuple):
            fx='self.handle%s(el,msg[0],msg[1])'%(msg[1].__class__.__name__)
            logger.debug("calling %s() callback"%(fx))
            eval(fx)
          else:
            msgName=msg.__class__.__name__
            fx='self.handle%s(el,msg)'%(msgName)
            logger.debug("calling %s() callback"%(fx))
            eval(fx)
    for e in objList_:
      e=None
    objList_=None

  def handleShutdownEvent(self,obj,msg):
    '''
      Set the done flag, this is done from the thread to avoid need for necessary guards
    '''
    self.done_=True;
    
class LoadBalancingPattern:
  '''
  General pattern; client(s), broker, server(s).  Clients send requests to broker, broker 
  determines available server, forwards requests and routes response back to original
  server.
  '''
  class Broker:
    '''
      Broker acts as the intermediatry between clients and servers,
      requests coming in from clients are routed to available servers.
      The broker is also responsible for managing 'active' servers, meaning
      keeping track of servers that are responsive and available for inbound
      requests.
    '''
    HeartbeatRate=3.0
    def __init__(self, fePort, bePort):
      '''
        Allocate necessary resources; front-end and back-end sockets, encoder/decoder
        and background thread for processing.
      '''
      self.context_=zmq.Context(1)
      self.feSock_=self.context_.socket(zmq.ROUTER)
      self.feSock_.bind('tcp://*:%d'%(fePort))
      self.beSock_=self.context_.socket(zmq.ROUTER)
      self.beSock_.bind('tcp://*:%d'%(bePort))
      self.decoder_=messaging.ProtoBuffDecoder()
      self.encoder_=messaging.ProtoBuffEncoder()
      self.queue_=collections.OrderedDict()
      self.done_ = False
      self.tid_=threading.Thread(target=self.run,args=())
      self.tid_.start()

    def stop(self):
      '''
       Stop the reactor.
      '''
      self.done_=True

    def __del__(self):
      '''
        Release allocated resources, close sockets and context
      '''
      self.feSock_.close()
      self.beSock_.close()
      self.context_.term()

    def heartbeatServers(self):
      '''
         Iterate thru existing server table, if we haven't received a message
         from a server send a heartbeat to it.  The server will ping-pong the
         message back resulting in a refreshed table entry.  Application messages
         should also update the server table in leu of a heartbeat message
         (reducing the need for heartbeats messages)
       '''
      tooLate=datetime.datetime.now()-datetime.timedelta(seconds=LoadBalancingPattern.Broker.HeartbeatRate*2)
      deadServers=[]
      for id,ts in self.queue_.items():
        if ts < tooLate:
          logger.debug("dead server: %s"%(id))
          deadServers.append(id)
      for e in deadServers:
        self.queue_.pop(e, None)

      now=datetime.datetime.now()
      for id,ts in self.queue_.items():
        if ts < now:
          hb=[id,MsgLib.Heartbeat]
          logger.debug("broker sending hb %s"%(datetime.datetime.now()))
          hbMsg=MsgLib.Heartbeat()
          hbMsg.id=id
          env=self.encoder_.encode(hbMsg)
          S=env.SerializeToString()
          self.beSock_.send_multipart((id,S))
          logger.debug("broker done sending hb %s"%(datetime.datetime.now()))

    def run(self):
      '''
        Active thread should run 'til stopped by main process.  Poll front/back
        sockets, processing/routing messages as they come in.  Messages from
        backend servers should be treated as heartbeats (meaning that
        inbound messages indicate an 'active' server).  Servers that haven't
        sent a message for some time should be sent a heartbeat message and
        expected to respond.  Servers that fail to send a heartbeat, or any message,
        for a time-out period should be removed from the available server list.
      '''
      poller=zmq.Poller()
      poller.register(self.feSock_,zmq.POLLIN)
      poller.register(self.beSock_,zmq.POLLIN)
      while not self.done_:
        socks = dict(poller.poll(int(self.HeartbeatRate*1000)))
        if socks.get(self.feSock_) == zmq.POLLIN:
          logger.debug("fe hit")
          id,val = self.queue_.popitem(False)
          m=self.feSock_.recv_multipart()
          m.insert(0,id)
          self.beSock_.send_multipart(m)

        if socks.get(self.beSock_) == zmq.POLLIN:
          frames=self.beSock_.recv_multipart()
          self.queue_[frames[0]] = datetime.datetime.now() + datetime.timedelta(seconds=LoadBalancingPattern.Broker.HeartbeatRate)

          env=MsgLib.msgEnvelope()
          S=b''.join(frames[1:])
          logger.debug("forwarding to fe: %s"%(str(frames)))
          self.feSock_.send_multipart(frames[1:])
        self.heartbeatServers()

  class Server:
   '''
   Server abstraction, connects and HB's with broker.
   '''
   class ServerMsgReactor(messaging.MtMsgReactor):
      '''
        Message reactor for server component, manages heartbeat and shutdown messages
        as part of the abstraction, all other messages to be handled by derived class.
      '''
      def __init__(self, objList):
        '''
          Initialize resources, then notify broker the server is available
          for requests via HB msg
        '''
        super().__init__(objList)
        self.sendHeartbeat()

      def resetHbTimer(self):
        '''
          Heartbeat policy between broker and server is initiated by the broker for 
          active servers.  This will detect a server failing while waiting for a
          request.  Servers that fail during the servicing of a request are deemed
          'inactive', removed from the active server list from the broker immediately
          before forwarding the request.  Those servers require a server-initiated
          heartbeat to be re-added to the active server list in the broker.  This
          heartbeat timer indicates when a HB should be initiated, and sent, to the 
          broker.  Note, the HB timer is a bit longer than the policy HB rate to
          avoid the broker and server(s) initiating HB messages nearing the same time
          (e.g. duplicating initiating HBs)
        '''
        #--set the hb timer a bit long to prevent server & broker initiating a HB at the same time
        self.hbExpireTime_=datetime.datetime.now()+datetime.timedelta(seconds=LoadBalancingPattern.Broker.HeartbeatRate*1.5)

      def sendHeartbeat(self):
        '''
          Send a heartbeat message
        '''
        sock=self.objList_[0]
        id=sock.sock_.socket_.getsockopt(zmq.IDENTITY)
        msg=MsgLib.Heartbeat()
        msg.id=id
        sock.send(msg)
        self.resetHbTimer()

      def handleHeartbeat(self, obj, msg):
        '''
           Inbound HB message implies broker wants to know if server is still
            alive, send it a hb msg
        '''
        logger.debug("%s got HB msg %s"%(self.__class__.__name__,str(msg)))
        self.sendHeartbeat()


      def idle(self):
        '''
          The idle callback is called by the message handler abstraction
          to allow non-message-event behaviors (e.g. initiating message)
        '''
        if (datetime.datetime.now() > self.hbExpireTime_):
          self.sendHeartbeat()

   def __init__(self,endPt, mh=None):
     '''
       Start the message handler
     '''
     if mh:
       self.msgHandler_=mh
     else:
       self.msgHandler_=self.ServerMsgReactor([messaging.Dealer(endPt)])

   def stop(self):
     '''
       Stop the message handler
     '''
     self.msgHandler_.stop()

  class Client:
    '''
      Lazy-Pirate Reliable Request/Response; tracks last message sent
      and if response isn't received within a time-out, message is resent
      using a max retry policy.
    '''
    def __init__(self, endPt, maxRetries=5, retryTimeOutMs=5000):
      '''
       Initialize needed resources.
      '''
      self.maxRetries_=maxRetries
      self.retryTimeOutMs_=retryTimeOutMs
      self.lastMsg_=None
      self.retryCount_=0
      self.sock_=messaging.Dealer(endPt)

    def send(self, msg):
      '''
        Send the message, retain it in case of need for retrying
      '''
      self.lastMsg_=msg
      self.sock_.send(self.lastMsg_)

    def recv(self):
      '''
      Extend the recv() protocol to wait for a message to
       be returned within the retry time-out, if no message
       has been received, resend the last message (with max retry count)
       the intent is to detect/recover from a non-responsive server,
       network preventing transfer,... (refer to LazyPirate Reliable Req/Rep pattern)
      '''
      gotMsg=self.sock_.wait(self.retryTimeOutMs_)
      while (not gotMsg and self.retryCount_ < self.maxRetries_):
        self.retryCount_+=1
        logger.debug("failed to get a response, retry(%d) send of last message(%s): %s"%(self.retryCount_,type(self.lastMsg_),self.lastMsg_))
        self.sock_.send(self.lastMsg_)
        gotMsg=self.sock_.wait(self.retryTimeOutMs_)
      reply=None
      if gotMsg:
        reply=self.sock_.recv()
        self.retryCount_=0
      else:
        logger.debug("failed to get a response, terminating retry")
  
      return reply

