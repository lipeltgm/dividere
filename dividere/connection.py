import logging
import zmq
import time
import threading
from zmq.utils.monitor import recv_monitor_message

class Connector:
  @staticmethod
  def socketEventMonitor(monitorSock):
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
    monitorSock = sock.get_monitor_socket()
    tid = threading.Thread(target=Connector.socketEventMonitor, args=(monitorSock,))
    tid.start()
    return tid;

  def __init__(self):
    self.ctx_=zmq.Context()
    self.socket_ = None
    self.tid_ = None

  def __del__(self):
    self.socket_.disable_monitor()
    if self.tid_: self.tid_.join() 
    self.socket_.close()
    self.ctx_.term()

class Publisher(Connector):
  def __init__(self, endPoint):
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.PUB)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    self.socket_.bind(endPoint)

  def send(self, msg):
    self.socket_.send(msg)

class Subscriber(Connector):
  def __init__(self, endPoint, topic=''):
    super(self.__class__,self).__init__()
    self.socket_=self.ctx_.socket(zmq.SUB)
    self.tid_=self.registerSocketMonitoring(self.socket_)
    self.socket_.connect(endPoint)
    self.subscribe(topic)

  def subscribe(self, topic):
    self.socket_.setsockopt_string(zmq.SUBSCRIBE, topic)

  def recv(self):
    S=self.socket_.recv()
    return S




