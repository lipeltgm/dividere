#!/usr/bin/python3
import dividere
import time
import logging
import argparse

#-----main-----
if __name__ == '__main__':
  descript='Integration/Unit tests for framework'
  parser=argparse.ArgumentParser(description=descript)
  parser.add_argument('--verbose',action='store_true',default=False)

  userArgs=parser.parse_args()
  if userArgs.verbose:
    logLevel=logging.DEBUG
  else:
    logLevel=logging.INFO
  logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)s-%(funcName)s()] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',level=logLevel)

  p=dividere.connection.Pub('tcp://*:5555')
  s=dividere.connection.Sub('tcp://localhost:5555')
  time.sleep(2)
  p=None
  s=None

