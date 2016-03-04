#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

from RPCServer.RPCServer import RPCServer
from demo.EchoService.EchoService import Processor

import logging

logging.basicConfig()

class EchoServiceHandler(object):
    def __init__(self):
        self.__result_index = 0

    def echo(self, param):
        last_index = self.__result_index
        self.__result_index += 1
        return param + str(last_index)

def server():
    handler = EchoServiceHandler()
    rpc_server = RPCServer('Server.xml', handler)
    if not rpc_server.init():
        return

    rpc_server.start(Processor)

if __name__ == '__main__':
    server()
