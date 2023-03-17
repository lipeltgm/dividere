import logging
import zmq
import time
import threading
from zmq.utils.monitor import recv_monitor_message

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
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.REQ)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    for endPt in endPointList:
      logging.debug("binding to %s"%(endPt))
      self.socket_.connect(endPt)

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

class Response(Connector):
  '''
    First part of a Request/Response connection pair.  Request object
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
    self.socket_.bind(endPoint)

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

