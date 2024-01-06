import logging
from dividere import messaging
from dividere import registry
import threading
import time

class Service:
  '''
    Abstract base class for services, registers service name with name
    registry and establishes a req/rep socket for incoming messaging.
    Derived classes are intended to provide 'def handleXXX(self, msg)' 
    methods for expected incoming requests.
  '''
  def __init__(self):
    '''
      Find an available port within port range [5100,6000], create
      incoming socket with the port, register the service (e.g. derived class name)
      and port with the name service, then begin waiting for an processing inbound
      messages in an active thread.
    '''
    self.name_="%s.%s"%(self.__module__,self.__class__.__name__)
    logging.debug("service name: %s"%(self.name_))
    self.setupSocket()
    self.done_=False
    self.tid_=threading.Thread(target=self.run, args=())
    self.tid_.start()
    self.tid1_=threading.Thread(target=self.reregisterThread, args=())
    self.tid1_.start()

  def __del__(self):
    '''
      Force stopping threads if the object is terminated
    '''
    self.stop()

  def stop(self):
    '''
      Signal thread to halt.
    '''
    self.done_=True

  def send(self, msg):
    '''
      Send message through socket
    '''
    self.sock_.send(msg)

  def wait(self, timeOutMs):
    '''
      Wait for an inbound message within the specified timeout, return bool
      indicating message was received
    '''
    return self.sock_.wait(timeOutMs)

  def recv(self):
    '''
      Get the next message from the socket, blocks indefnitely, use wait()
      to avoid blocking.
    '''
    return self.sock_.recv()

  def run(self):
    '''
      Loop waiting for message, call associated message handler (which is responsible
      for sending response message).  Periodically check for signal to terminate
      the thread.
    '''
    while not self.done_:
      time.sleep(1)
      if self.sock_.wait(1000):
        msg=self.sock_.recv()
        msgName=msg.__class__.__name__
        S='; '.join(str(msg).split("\n"))
        logging.debug("received %s: %s"%(msgName,S))
        fx='self.handle%s(msg)'%(msgName)
        eval(fx)

  def reregisterThread(self):
    '''
      This thread supports reregistration in the case that
      a name service abruptly terminates, is restarted, and
      notifies services to re-register
    '''
    addr='localhost'
    port=registry.ServiceRegistry.Server.subPort
    subPort=messaging.Subscriber('tcp://%s:%d'%(addr,port))
    while(not self.done_):
      if subPort.wait(1000):
        msg=subPort.recv()
        serverPort=registry.ServiceRegistry.Server.port
        serviceRegistry=registry.ServiceRegistry.Client('localhost',serverPort)
        serviceRegistry.registerService(self.name_, self.port_)


  def setupSocket(self):
    '''
      Loop thru the port range looking for an available port, once
      finding one register the service and port.  Throw exception
      if you fail to find an available port
    '''
    done=False
    portRange=range(5100,6000)
    i=portRange[0]
    while (not done and i in portRange):
      i += 1
      endPt='tcp://*:%d'%(i)
      try:
        self.sock_=messaging.Response(endPt)
        self.port_=i
        logging.info("%s using %s"%(self.name_,endPt))
        serverPort=registry.ServiceRegistry.Server.port
        serviceRegistry=registry.ServiceRegistry.Client('localhost',serverPort)
        serviceRegistry.registerService(self.name_, self.port_)
        done=True
      except Exception as ex:
        if 'Address already in use' in str(ex):
          logging.debug('caught expected exception searching for available port; %s'%(str(ex)))
        else:
          raise(ex)

    if not done:
      raise Exception("Unable to find available port")

