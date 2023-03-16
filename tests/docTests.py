import unittest
import dividere
import sys
import inspect
import logging

class docTests(unittest.TestCase):
  ModuleList=[dividere.connection, dividere.messaging]

  def test00(self):
    #--confirm each class in the module list has documentation
    for m in docTests.ModuleList:
      logging.debug("reviewing %s module"%(m.__name__))
      for className,classObj in [(name, obj) for name,obj in inspect.getmembers(m) if inspect.isclass(obj)]:
        logging.debug("confirming %s has class documentation"%(className))
        self.assertTrue(classObj.__doc__, "failed to find doc string for %s"%(className))

  def test01(self):
    for m in docTests.ModuleList:
      logging.debug("reviewing %s module"%(m.__name__))
      for className,classObj in [(name, obj) for name,obj in inspect.getmembers(m) if inspect.isclass(obj)]:
        logging.debug("inspecting %s"%(className))
        methodList = [method for method in dir(classObj) if not method.startswith('__')]
        for method in methodList:
          fx=eval("%s.%s.%s"%(m.__name__,className,method))
          self.assertTrue(fx.__doc__, "failed to find doc string for %s"%(str(fx)))

