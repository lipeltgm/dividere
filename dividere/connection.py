import logging
import zmq
import time
import threading
from zmq.utils.monitor import recv_monitor_message
from collections import namedtuple
import socket
from threading import Lock
#from collections import OrderedDict
import collections
import datetime
import uuid
import zmq


class PortManager:
  '''
    Singleton supports acquiring an available port for service
    and communications objects.
  '''
  @staticmethod
  def acquire():
    '''
      Find next available port, as per the os, by creating a  
      temporary socket which is assigned an available port
      number, then close the socket and return the port for 
      use.
      Note, port acquisition should support multi-threaded
      clients.
    '''
    mutex=Lock()
    with mutex:
      sock=socket.socket()
      sock.bind(('',0))
      retVal=sock.getsockname()[1]
      sock.close()
    return retVal

class Connector:
  '''
     This abstract class defines the interfaces and structures
     for ZMQ socket-based derived classes.  This class provides
     the ZMQ context and socket event monitoring useful for
     debugging socket state changes.
     The socket monitoring is conducted by an independent thread,
     which is terminated/joined at object termination.
  '''
  @staticmethod
  def socketEventMonitor(monitorSock):
    '''
      Background threading callback, supports monitoring the
      specified socket via a background thread and logs state
      changes of the socket for debugging purposes.
      Monitors the socket until monitoring is terminated
      via object destructor (e.g. obj = None)
      Note: Used internally to class(es), not intended for external usage
    '''
    EVENT_MAP = {}
    for name in dir(zmq):
      if name.startswith('EVENT_'):
        value = getattr(zmq, name)
        EVENT_MAP[value] = name

    while monitorSock.poll():
      evt: Dict[str, Any] = {}
      mon_evt = recv_monitor_message(monitorSock)
      evt.update(mon_evt)
      evt['description'] = EVENT_MAP[evt['event']]
      logging.debug(f"Event: {evt}")
      if evt['event'] == zmq.EVENT_MONITOR_STOPPED:
        break

    monitorSock.close()

  @staticmethod
  def registerSocketMonitoring(sock):
    '''
    Creates a monitoring thread for the specified socket,
    starts the thread and returns the thread id to the caller
    which allows joining on the thread post stopping monitoring
    Note: Used internally to class(es), not intended for external usage
    '''
    monitorSock = sock.get_monitor_socket()
    tid = threading.Thread(target=Connector.socketEventMonitor, args=(monitorSock,))
    tid.start()
    return tid;

  def __init__(self):
    '''
      Creates resources used in base classes and defines expected
      structure to be used in derived classes. 
    '''
    self.ctx_=zmq.Context()
    self.socket_ = None
    self.tid_ = None

  def __del__(self):
    '''
    Performs cleanup for all allocated resources;
    disable monitoring, wait for monitoring thread completes,
    close the socket and close the context
    '''
    self.socket_.setsockopt(zmq.LINGER, 0)
    self.socket_.disable_monitor()
    if self.tid_: self.tid_.join() 
    self.socket_.close()
    self.ctx_.term()

#================================================================================
#  Pub/Sub Connection Pair
#================================================================================
class Publisher(Connector):
  '''
     This class creates a publisher socket at the specified endpoint.
     This is the pub in the Pub/Sub pattern.
  '''
  def __init__(self, endPoint):
    '''
       Allocate base class resources, create PUB socket, start
       socket debug monitoring and connect the socket to the
       specified endpoint (e.g. 'tcp://*:5555')
       Refer to ZMQ documentation for details on available transport
       and syntax of endpoint.
    '''
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.PUB)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    self.socket_.bind(endPoint)

  def send(self, msg):
    '''
      Publish the specified message (expected sequence of bytes)
    '''
    self.socket_.send(msg)

class Subscriber(Connector):
  '''
     This class creates a subscriber socket at the specified endpoint.
     This is the sub in the Pub/Sub pattern.  By default, a subscriber
     object will listen for all messages, but can be filtered by specifying
     a topic(s); either by specifying a topic during the initializer or
     calling subscribe() after object creation
  '''
  def __init__(self, endPoint, topic=''):
    '''
       Allocate base class resources, create SUB socket, start
       socket debug monitoring and connect the socket to the
       specified endpoint (e.g. 'tcp://localhost:5555')
       Subscribes to the specified topic, by default the object
       will receive all messages.
       Refer to ZMQ documentation for details on available transport
       and syntax of endpoint.
    '''
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.SUB)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    self.socket_.connect(endPoint)
    self.subscribe(topic)
    self.poller_=zmq.Poller()
    self.poller_.register(self.socket_,zmq.POLLIN)

  def subscribe(self, topic):
    '''
      Allows subscribing to additional topics (beyond the one
      specified in the constructor)
    '''
    self.socket_.setsockopt_string(zmq.SUBSCRIBE, topic)

  def recv(self):
    '''
      Wait for next message to arrive and return it to the
      caller.
    '''
    S=self.socket_.recv()
    return S

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    ev=self.poller_.poll(timeOutMs)
    gotMsg=self.socket_ in dict(ev)
    return gotMsg

#================================================================================
#  Request/Response Connection Pair
#================================================================================
class Request(Connector):
  '''
    First part of a Request/Response connection pair.  Request object
    initiates all messages, response object sends message response.
    Failure to adhere to this sender protocol will result in exception
    being thrown.
    Note: this pairing allows for 1-N cardinality, one request connection
          object sending to N-response objects.  When configured like this
          the recipient of any message is routed in a round-robin fashion
          to one response object
  '''
  def __init__(self, endPointList):
    '''
      Allocate all resources to support the object;         
      create a socket, register it for monitoring, and connect
      it to the specified endpoint
    '''
    if not isinstance(endPointList, list):
      endPointList=[endPointList]
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.REQ)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    for endPt in endPointList:
      logging.debug("binding to %s"%(endPt))
      self.socket_.connect(endPt)
    self.poller_=zmq.Poller()
    self.poller_.register(self.socket_,zmq.POLLIN)

  def send(self, msg):
    '''
      Send the specified message out the socket channel.  
      Message consists of a stream of bytes.
    '''
    S=self.socket_.send(msg)

  def recv(self):
    '''
      Wait for and return the incoming message.
    '''
    S=self.socket_.recv()
    return S

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    ev=self.poller_.poll(timeOutMs)
    gotMsg=self.socket_ in dict(ev)
    return gotMsg

class Response(Connector):
  '''
    Second part of a Request/Response connection pair.  Request object
    initiates all messages, response object sends message response.
    Failure to adhere to this sender protocol will result in exception
    being thrown.
  '''
  def __init__(self, endPoint):
    '''
      Allocate all resources to support the object;         
      create a socket, register it for monitoring, and connect
      it to the specified endpoint
    '''
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.REP)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    logging.debug("binding to %s"%(endPoint))
    #--rep sockets can be 'bound' to ports or connected to ports
    #-- binding generally used for 1-1 connections, connecting 
    #-- used with router/dealer intermediary components, allow
    #-- both by distinguishing between a preferred bind (e.g. tcp://*:5000)
    #-- vs connect (e.g. tcp://localhost:5000)
    if "*:" in endPoint:
      self.socket_.bind(endPoint)
    else:
      self.socket_.connect(endPoint)
    self.poller_=zmq.Poller()
    self.poller_.register(self.socket_,zmq.POLLIN)

  def send(self, msg):
    '''
      Send the specified message out the socket channel
      Message consists of a stream of bytes.
    '''
    S=self.socket_.send(msg)

  def recv(self):
    '''
      Wait for and return the incoming message.
    '''
    S=self.socket_.recv()
    return S

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    ev=self.poller_.poll(timeOutMs)
    gotMsg=self.socket_ in dict(ev)
    return gotMsg

class Proxy(Connector):
  '''
  Proxy abstraction defines a router/dealer pairing to allow
  async req/rep client connections.
  '''
  def __init__(self, fePort, bePort):
    '''
      Front-end utilizes the base class socket_ attribute, adds a backend
      socket.  Binds to two known ports
    '''
    super(self.__class__,self).__init__()
    self.socket_ = self.ctx_.socket(zmq.ROUTER)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    self.backend = self.ctx_.socket(zmq.DEALER)
    self.tid1_=self.registerSocketMonitoring(self.backend)
    self.socket_.bind("tcp://*:%d"%(fePort))
    self.backend.bind("tcp://*:%d"%(bePort))

    # Initialize poll set
    self.poller = zmq.Poller()
    self.poller.register(self.socket_, zmq.POLLIN)
    self.poller.register(self.backend, zmq.POLLIN)
    self.done_=False
    self.mtid_ = threading.Thread(target=self.run, args=())
    self.mtid_.start()

  def stop(self):
    '''
      Signal the active thread it should terminate, wait for
      the thread to halt and close out derived class resources
    '''
    self.done_=True
    self.mtid_.join()
    self.backend.close()
    self.tid1_.join()

  def run(self):
    '''
      Loop until signaled to stop, wait for an event
      for a specified time-out, to prevent blocking calls,
      then route inbound messages from one to the other socket
    '''
    while not self.done_:
      socks = dict(self.poller.poll(1000))

      if socks.get(self.socket_) == zmq.POLLIN:
          message = self.socket_.recv_multipart()
          self.backend.send_multipart(message)
  
      if socks.get(self.backend) == zmq.POLLIN:
          message = self.backend.recv_multipart()
          self.socket_.send_multipart(message)
    logging.debug("terminating thread")

class Dealer(Connector):
  '''
   Dealer 'generally' is a replacement for Request/Response objects without
   the strict send/receive protocol.  Use of dealer objects allow asynchronous
   messaging, like sending N messages rather than the strict send/recv protocol.
  '''
  def __init__(self, endPointList):
    '''
      Allocate all resources to support the object;         
      create a socket, register it for monitoring, and connect
      it to the specified endpoint
    '''
    if not isinstance(endPointList, list):
      endPointList=[endPointList]
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.DEALER)
    self.socket_.setsockopt_string(zmq.IDENTITY, str(uuid.uuid4()))
    self.tid_=self.registerSocketMonitoring(self.socket_)
    for endPt in endPointList:
      if '*' in endPt:
        logging.debug("binding to %s"%(endPt))
        self.socket_.bind(endPt)
      else:
        logging.debug("connecting to %s"%(endPt))
        self.socket_.connect(endPt)
    self.poller_=zmq.Poller()
    self.poller_.register(self.socket_,zmq.POLLIN)

  def recv(self):
    '''
      Inbound message could be routed, or unrouted, if routed return
      the identifier vector and message content.  The final frame
      will be the message content, the preceeding frames will be 
      routing identifiers (maybe multiples if message routed thru multiple
      router sockets).
      Returned value will _either_ be message payload, or tuple with routing id 
      vector + message payload
    '''
    frames=self.socket_.recv_multipart()
    if len(frames) > 1:
      retVal=(frames[0:-1],frames[-1])
    else:
      retVal=frames[0]
    
    return retVal

  def send(self, msg):
    '''
      Dealer socket must be capable of sending routed or unrouted messages,
      for example; client-side messages to anonymous workers may be unrouted,
      and worker responses may be routed.  All depending on the communications
    '''
    if isinstance(msg,tuple):
      self.socket_.send_multipart(msg[0], zmq.SNDMORE)
      self.socket_.send_multipart([msg[1]])
    else:
      self.socket_.send(msg)
    

  def wait(self, timeOutMs):
    '''
      Wait for a message to arrive within the specified timeout, return
      true/false representing whether a message is available
    '''
    ev=self.poller_.poll(timeOutMs)
    gotMsg=self.socket_ in dict(ev)
    return gotMsg

class LoadBalancingBroker:
  def __init__(self, feSockType, feSockPort, beSockType, beSockPort):
    self.done_ = False
    self.frontEnd_={"sockType":feSockType, "endPt":"tcp://*:%d"%(feSockPort)}
    self.backEnd_={"sockType":beSockType, "endPt":"tcp://*:%d"%(beSockPort)}
    self.tid_ = threading.Thread(target=self.run, args=())
    self.tid_.start()

  def stop(self):
    self.done_=True
    self.tid_.join()

# def parseMessage(self, msgPayload):
#   B=b''.join(msgPayload)
#   env=MsgLib.msgEnvelope()
#   env.ParseFromString(B)
#   retVal=self.decoder.decode(env)
#   return retVal

  @classmethod
  def updateServerQueue(cls, queue,id):
    HbRateSecs=15
    queue[id]=datetime.datetime.now()+datetime.timedelta(seconds=HbRateSecs)
    logging.debug("adding/updating server %s"%(id))

  @classmethod
  def nextAvailServer(cls, queue):
    cls.groomServerQueue(queue)
    toId, worker = queue.popitem(False)
    queue[toId]=worker
    return toId

  @classmethod
  def groomServerQueue(cls, queue):
    HbRateSecs=15
    currentTs=datetime.datetime.now()
    for id,ts in queue.items():
      if currentTs > ts:
        logging.debug("removing dormant server %s"%(id))
        queue.pop(id)

  def run(self):
    #  run ~/zmqReliableRR/foo.py + this test
    context = zmq.Context(1)
    frontend = context.socket(self.frontEnd_['sockType']) 
    frontend.bind(self.frontEnd_['endPt'])
    backend = context.socket(self.backEnd_['sockType'])  
    backend.bind(self.backEnd_['endPt'])
#   self.decoder=messaging.ProtoBuffDecoder()
    queue=collections.OrderedDict()

    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)
    while not self.done_:
      socks = dict(poller.poll(1000))

      if socks.get(backend) == zmq.POLLIN:
        frames = backend.recv_multipart()
        fromId=frames[0]
        self.updateServerQueue(queue,fromId)
        msgPayload=frames[1:]
#       logging.debug("server %s sent %s"%(fromId, self.parseMessage(msgPayload)))
        frontend.send_multipart(msgPayload)
        self.updateServerQueue(queue, fromId)

      if socks.get(frontend) == zmq.POLLIN:
        frames = frontend.recv_multipart()
        fromId=frames[0]
        msgPayload=frames[1:]
        serverId=self.nextAvailServer(queue)
#       logging.debug("client sent %s, routing to %s"%(self.parseMessage(msgPayload), serverId))
        msgPayload.insert(0,serverId)
        backend.send_multipart(msgPayload)

    frontend.close()
    backend.close()
    context.term()


class LoadBalancingBroker2:
  HEARTBEAT_LIVENESS = 30     # 3..5 is reasonable
  HEARTBEAT_INTERVAL = 1.0   # Seconds
  PPP_READY = b"\x01"      # Signals worker is ready
  PPP_HEARTBEAT = b"\x02"  # Signals worker heartbeat
  class Worker(object):
      def __init__(self, address):
          self.address = address
          self.expiry = time.time() + HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS
  
  class WorkerQueue(object):
      def __init__(self):
          self.queue = collections.OrderedDict()
  
      def ready(self, worker):
          self.queue.pop(worker.address, None)
          self.queue[worker.address] = worker
  
      def purge(self):
          """Look for & kill expired workers."""
          t = time.time()
          expired = []
          for address, worker in self.queue.items():
              if t > worker.expiry:  # Worker expired
                  expired.append(address)
          for address in expired:
              print("W: Idle worker expired: %s" % address)
              self.queue.pop(address, None)
  
      def next(self):
          address, worker = self.queue.popitem(False)
          return address
   
  def __init__(self, feSockType, feSockPort, beSockType, beSockPort):
    self.done_ = False
    self.frontEnd_={"sockType":feSockType, "endPt":"tcp://*:%d"%(feSockPort)}
    self.tid_ = threading.Thread(target=self.run, args=())
    self.tid_.start()

  def stop(self):
    self.done_=True
    self.tid_.join()

  def run(self):
    #  Paranoid Pirate Protocol constants

    context = zmq.Context(1)
    frontend = context.socket(zmq.ROUTER) # ROUTER
    backend = context.socket(zmq.ROUTER)  # ROUTER
    frontend.bind("tcp://*:5555") # For clients
    backend.bind("tcp://*:5556")  # For workers

    poll_workers = zmq.Poller()
    poll_workers.register(backend, zmq.POLLIN)
    
    poll_both = zmq.Poller()
    poll_both.register(frontend, zmq.POLLIN)
    poll_both.register(backend, zmq.POLLIN)
    
    workers = self.WorkerQueue()
    heartbeat_at = time.time() + self.HEARTBEAT_INTERVAL

    while not self.done_:
      logging.debug("running")
      time.sleep(1)
      if len(workers.queue) > 0:
          poller = poll_both
      else:
          poller = poll_workers
      socks = dict(poller.poll(self.HEARTBEAT_INTERVAL * 1000))
  
      if socks.get(backend) == zmq.POLLIN:
          # Use worker address for LRU routing
          frames = backend.recv_multipart()
          print('backend got: %s'%(str(frames)))
          if not frames:
              break
  
          address = frames[0]
          workers.ready(self.Worker(address))
  
          # Validate control message, or return reply to client
          msg = frames[1:]
          if len(msg) == 1:
              if msg[0] not in (self.PPP_READY, self.PPP_HEARTBEAT):
                  print("E: Invalid message from worker: %s" % msg)
          else:
              print('sending to fe: %s'%(msg))
              frontend.send_multipart(msg)
  
          # Send heartbeats to idle workers if it's time
      if socks.get(frontend) == zmq.POLLIN:
          frames = frontend.recv_multipart()
          print('frontend got: %s'%(str(frames)))
  
          frames.insert(0, workers.next())
          print('sending to be: %s'%(frames))
          backend.send_multipart(frames)
  
  
      workers.purge()

    backend.close()
    frontend.close()
    context.term()

    
#   
#   while True:
#   
