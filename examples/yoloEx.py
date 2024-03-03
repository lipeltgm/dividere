#!/usr/bin/python3
from pydarknet import Detector, Image
import cv2
import threading
import dividere
import time
import clientMsgs_pb2 as clientMsgs
import numpy as np

class YoloSolver:
  def __init__(self):
    self.net_=Detector(bytes('yolov3.cfg', encoding='utf-8'), bytes('./yolov3.weights', encoding='utf-8'), 0, bytes('./data/coco.data',encoding='utf-8'))

  def findObjects(self, img):
    img_darknet=Image(img)
    results = self.net_.detect(img_darknet)
    return results

  def solve(self, vidFileName):
    vidCapture = cv2.VideoCapture(vidFileName)
    gotFrame=True;
    i=0
    while(vidCapture.isOpened() and gotFrame):
      gotFrame, frame = vidCapture.read()
      if gotFrame:
        print("frame %d"%(i))
        tmpFile='tmp.jpg'
        cv2.imwrite(tmpFile,frame)
        img=cv2.imread(tmpFile)
        img1=Image(frame)
        img2=Image(img)
        results=self.findObjects(frame)
        print(results)
      i+=1

  def __del__(self):
    self.net_=None


class MtYoloSolver(threading.Thread):
  class DealerWorkerMsgReactor(dividere.messaging.MtMsgReactor):
    def __init__(self,obj):
      super(self.__class__,self).__init__(obj)
      self.yolo_=YoloSolver()
  
    def handleImageMsg(self, obj, id, msg):
       tid=threading.get_native_id()
       print("handling msg %s"%(tid))
       outFile="foo=%s.jpg"%(tid)
       with open(outFile, 'wb') as fp:
          fp.write(msg.image)
       img=cv2.imread(outFile)
       results=self.yolo_.findObjects(img)
       reply=clientMsgs.ImageReply()
       for cat, score, bounds in results:
         x, y, w, h = bounds
         d=clientMsgs.Detection()
         d.category=cat
         d.score=score
         b=clientMsgs.BoundingBox()
         b.x=int(x)
         b.y=int(y)
         b.width=int(w)
         b.height=int(h)
         d.bbox.CopyFrom(b)
         reply.detection.extend([d])
       obj.send((id,reply))

  def __init__(self,numWorkers):
    self.numWorkers_=numWorkers
    threading.Thread.__init__(self)
    self.wList_=None
    self.bePort_=dividere.connection.PortManager.acquire()
    self.fePort_=dividere.connection.PortManager.acquire()
    self.proxy_=dividere.connection.Proxy(self.fePort_,self.bePort_)
    self.start()
    self.sock_=dividere.messaging.Dealer('tcp://localhost:%d'%(self.fePort_))

  def run(self):
    print("running; workers: %d"%(self.numWorkers_))
    self.wList_=[self.DealerWorkerMsgReactor([dividere.messaging.Dealer('tcp://localhost:%d'%(self.bePort_))]) for i in range(0,self.numWorkers_)]

  def stop(self):
    [el.stop() for el in self.wList_]
    self.join()
    self.proxy_.stop()

  def solve(self, vidFileName):
    vidCapture = cv2.VideoCapture(vidFileName)
    gotFrame=True;
    i=0
    pendingRequests=0
    while(vidCapture.isOpened() and gotFrame):
      gotFrame, frame = vidCapture.read()
      if gotFrame:
        print("frame %d"%(i))
        if i in range(0,self.numWorkers_):
          msg=clientMsgs.ImageMsg()
          cv2.imwrite('tmp.jpg',frame)
          with open('tmp.jpg','rb') as fp:
            b=bytes(fp.read())
          msg.image=b
          self.sock_.send(msg)
          pendingRequests+=1
        else:
          reply=self.sock_.recv()
          pendingRequests-=1
          print("got: %s"%(str(reply)))
          msg=clientMsgs.ImageMsg()
          cv2.imwrite('tmp.jpg',frame)
          with open('tmp.jpg','rb') as fp:
            b=bytes(fp.read())
          msg.image=b
          reply=self.sock_.send(msg)
          pendingRequests+=1
      i+=1
    #--wait for last N requests
    print("waiting for last %d requests"%(pendingRequests))
    for i in range(0,pendingRequests):
      reply=self.sock_.recv()
      print("got outbound msg %d"%(i))
    print("terminating")

class MpYoloSolver():
  class DealerWorkerMsgReactor(dividere.messaging.MpMsgReactor):
    def initThread(self):
      self.yolo_=YoloSolver()
      
    def handleImageMsg(self, obj, id, msg):
       tid=threading.get_native_id()
       print("handling msg %s"%(tid))
       outFile="foo=%s.jpg"%(tid)
       with open(outFile, 'wb') as fp:
          fp.write(msg.image)
       img=cv2.imread(outFile)
       results=self.yolo_.findObjects(img)
       reply=clientMsgs.ImageReply()
       for cat, score, bounds in results:
         x, y, w, h = bounds
         d=clientMsgs.Detection()
         d.category=cat
         d.score=score
         b=clientMsgs.BoundingBox()
         b.x=int(x)
         b.y=int(y)
         b.width=int(w)
         b.height=int(h)
         d.bbox.CopyFrom(b)
         reply.detection.extend([d])
       obj.send((id,reply))

  def __init__(self,numWorkers):
    self.numWorkers_=numWorkers
    threading.Thread.__init__(self)
    self.wList_=None
    self.bePort_=dividere.connection.PortManager.acquire()
    self.fePort_=dividere.connection.PortManager.acquire()
    self.proxy_=dividere.connection.Proxy(self.fePort_,self.bePort_)
    self.sock_=dividere.messaging.Dealer('tcp://localhost:%d'%(self.fePort_))
    self.wList_=[self.DealerWorkerMsgReactor(["Dealer('tcp://localhost:%d')"%(self.bePort_)]) for i in range(0,self.numWorkers_)]

  def stop(self):
    [el.stop() for el in self.wList_]
    self.proxy_.stop()

  def solve(self, vidFileName):
    vidCapture = cv2.VideoCapture(vidFileName)
    gotFrame=True;
    i=0
    pendingRequests=0
    while(vidCapture.isOpened() and gotFrame):
      gotFrame, frame = vidCapture.read()
      if gotFrame:
        print("frame %d"%(i))
        if i in range(0,self.numWorkers_):
          msg=clientMsgs.ImageMsg()
          cv2.imwrite('tmp.jpg',frame)
          with open('tmp.jpg','rb') as fp:
            b=bytes(fp.read())
          msg.image=b
          self.sock_.send(msg)
          pendingRequests+=1
        else:
          reply=self.sock_.recv()
          pendingRequests-=1
          print("got: %s"%(str(reply)))
          msg=clientMsgs.ImageMsg()
          cv2.imwrite('tmp.jpg',frame)
          with open('tmp.jpg','rb') as fp:
            b=bytes(fp.read())
          msg.image=b
          reply=self.sock_.send(msg)
          pendingRequests+=1
      i+=1
    #--wait for last N requests
    print("waiting for last %d requests"%(pendingRequests))
    for i in range(0,pendingRequests):
      reply=self.sock_.recv()
      print("got outbound msg %d"%(i))
    print("terminating")

#-----main-----
vidFile='clip.mp4'
Ts=[]
if True:
  obj=YoloSolver()
  t0=time.time()
  obj.solve(vidFile)
  t1=time.time()
  obj=None
  Ts.append(('seq run',t1-t0))

if True:
  for i in [1,2,3,5,7]:
    obj=MtYoloSolver(i)
    time.sleep(i*2); #--give workers time to initialize to avoid routing to single worker
    t0=time.time()
    obj.solve(vidFile)
    t1=time.time()
    Ts.append(('mt(%d) run'%(i),t1-t0))
    obj.stop()
    obj=None

if True:
  for i in [1,2,3,5,7]:
    obj=MpYoloSolver(i)
    time.sleep(i*2); #--give workers time to initialize to avoid routing to single worker
    t0=time.time()
    obj.solve(vidFile)
    t1=time.time()
    Ts.append(('mp(%d) run'%(i),t1-t0))
    obj.stop()
    obj=None

print("")
print("========================================")
print(Ts)
for e in Ts:
  print("%s %s"%(e[0],e[1]))
