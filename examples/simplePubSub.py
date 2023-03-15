#!/usr/bin/python3
import dividere
import foo_pb2 as foo
import time

Port=5555
pub=dividere.messaging.Publisher('tcp://*:%d'%(Port))
sub=dividere.messaging.Subscriber('tcp://localhost:%d'%(Port))
time.sleep(2); #--delay to address 'late joiner'

msg=foo.msg01()
msg.field1='abcd'
pub.send(msg)
got=sub.recv()
assert(got==msg)

#--destroy pub/sub objects to free resources and terminate threads
pub=None
sub=None

