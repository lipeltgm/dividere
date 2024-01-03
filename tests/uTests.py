#!/usr/bin/python3
import logging
import argparse
import unittest
import sys

sys.path.append("../")
import dividere

from connectionTests import *
from messagingTests import *
from docTests import *
from serviceRegistryTests import *
from serviceTests import *

#-----main-----
if __name__ == '__main__':
  descript='Integration/Unit tests for framework'
  parser=argparse.ArgumentParser(description=descript)
  parser.add_argument('--verbose',action='store_true',default=False)
  parser.add_argument('--quiet',action='store_true',default=False)
  userArgs, uTestArgs=parser.parse_known_args(sys.argv)
  if userArgs.verbose:
    logLevel=logging.DEBUG
  else:
    logLevel=logging.INFO

  if userArgs.quiet:
    logLevel=logging.ERROR

  logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)s-%(funcName)s()] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logLevel)

  unittest.main(argv=uTestArgs)

