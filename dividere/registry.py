from dividere import MsgLib
from dividere import connection
from dividere import messaging
import socket
import logging
from urllib.request import urlopen
import re
import threading
import time
from collections import namedtuple

class ServiceRegistry:
  '''
    Primarily namespace, server-side class used for instantiating a
    nameservice, client-side for performing registration and service
    lookup.
  '''
  class Server:
    '''
      Server-side implementation; establish a well-defined port for
      incoming registration and lookup requests.  Open the incoming port
      and wait for incoming messages in an independent thread.
    '''
    port=5000
    subPort=5001
    def __init__(self):
      '''
        Instantiate an object, open the port, hand-off to background thread
        for processing.
      '''
      self.serviceMap=dict()
      self.reqSock_=messaging.Response('tcp://*:%d'%(self.port))
      self.pubSock_=messaging.Publisher('tcp://*:%d'%(self.subPort))
      self.done_=False
      self.tid_=threading.Thread(target=self.run, args=())
      self.tid_.start()

    def __del__(self):
      self.stop()
      self.reqSock_=None
      self.pubSock_=None

    def stop(self):
      '''
        Signal and wait for the thread to terminate
      '''
      self.done_=True
      self.tid_.join()

    def run(self):
      '''
        Wait for incoming message, determine the category of message
        that arrived and process it.  Incoming message is req/rep, so
        handing the message requires sending a response message to
        satisfy the socket protocol
      '''
      time.sleep(1); #--delay for late joiner
      logging.debug("publishing rediscovery request")
      self.pubSock_.send(MsgLib.RediscoverReq())
      while not self.done_:
        time.sleep(1)
        if self.reqSock_.wait(1000):
          msg=self.reqSock_.recv()
          msgName=msg.__class__.__name__
          S='; '.join(str(msg).split("\n"))
          logging.debug("received %s: %s"%(msgName,S))
          fx='self.handle%s(msg)'%(msgName)
          eval(fx)
      logging.debug("stopping thread")

    def handleRegisterService(self, msg):
      '''
        Add incoming service info into the service map and
        send back an acknowledgement
      '''
      S='; '.join(str(msg).split("\n"))
      logging.info("received service registration: %s"%(S))
      self.serviceMap[msg.serviceName]=(msg.server,msg.port)
      logging.debug("self.serviceMap: %s"%(str(self.serviceMap)))
      ack=MsgLib.ack()
      ack.ok=True
      self.reqSock_.send(ack)

    def handleUnregisterService(self, msg):
      '''
        Remove incoming service info from the service map and
        send back an acknowledgement
      '''
      S='; '.join(str(msg).split("\n"))
      logging.info("received service registration: %s"%(S))
      del self.serviceMap[msg.serviceName]
      ack=MsgLib.ack()
      ack.ok=True
      self.reqSock_.send(ack)

    def handleServiceLookupReq(self, msg):
      '''
        Lookup the requeste service, return servicename, server, and port found
        return 'unavailable', port 0 if failed to find an available service
      '''
      S='; '.join(str(msg).split("\n"))
      logging.info("received service registration: %s"%(S))
      reply=MsgLib.ServiceLookupRep()
      reply.serviceName=msg.serviceName
      try:
        el=self.serviceMap[msg.serviceName]
        logging.debug("found element: %s"%(str(el)))
        reply.server=el[0]
        reply.port=el[1]
      except:
        logging.info("failed to locate service %s"%(msg.serviceName))
        reply.server='unavailable'
        reply.port=0
        pass
      self.reqSock_.send(reply)

  class Client:
    '''
      Instantiate new object, open port to name service 
    '''
    def __init__(self, addr, port):
      self.reqSock_=messaging.Request(['tcp://%s:%d'%(addr,port)])

    def registerService(self,serviceName, port):
      '''
        Send registration message using local port for on-prem style
        deployment, public ip for cloud-style deployments.  Receive
        and process ack.
      '''
      m=MsgLib.RegisterService()
      m.serviceName=serviceName
      m.server=self.getLocalIp()
      m.port=port
      self.reqSock_.send(m)
      ack=self.reqSock_.recv()
      S='; '.join(str(ack).split("\n"))
      logging.info("received registration ack: %s"%(S))

    def unregisterService(self,serviceName, port):
      '''
        Send deregistration message, receive and process ack.
      '''
      m=MsgLib.UnregisterService()
      m.serviceName=serviceName
      m.server=self.getLocalIp()
      m.port=port
      self.reqSock_.send(m)
      msgAvail=self.reqSock_.wait(5000)
      if msgAvail:
        ack=self.reqSock_.recv()
        S='; '.join(str(ack).split("\n"))
        logging.info("received unregistration ack: %s"%(S))

    def getLocalIp(self):
      '''
        Open temporary port, return the local ip address
      '''
      #--create a temp socket to get the local ip address
      s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(('8.8.8.8',1))
      retVal=s.getsockname()[0]
      s.close()
      return retVal

    def getPublicIp(self):
      '''
        Open temporary port, return the public ip address
      '''
      #--retrieve public ip address via dns server (cloud-based use cases)
      data = str(urlopen('http://checkip.dyndns.com/').read())
      return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)

    def lookupService(self, serviceName):
      '''
        Send lookup request to server, process reply and return results
      '''
      m=MsgLib.ServiceLookupReq()
      m.serviceName=serviceName
      self.reqSock_.send(m)
      reply=self.reqSock_.recv()
      Element=namedtuple('Element',['name','server','port'])
      return Element(serviceName,reply.server,reply.port) 
  
