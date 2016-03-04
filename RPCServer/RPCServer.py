#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

import sys
import signal
from thrift import TTornado
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory
from ZkServiceRegister import ZkServiceRegister

class RPCServer:
    DEFAULT_LISTEN_PORT = 9000
    DEFAULT_WEIGHT = 10
    DEFAULT_SERVER_ADDRESS = '0.0.0.0'
    DEFAULT_TIMEOUT = 3000

    def __init__(self,
                 zk_address,
                 zk_path,
                 zk_version,
                 handler,
                 address=DEFAULT_SERVER_ADDRESS,
                 port=DEFAULT_LISTEN_PORT,
                 weight=DEFAULT_WEIGHT,
                 timeout=DEFAULT_TIMEOUT):
        self.__handler = handler
        self.__address = address
        self.__port = port
        self.__server = None
        self.__zk_client = None
        self.__zk_address = zk_address
        self.__zk_timeout = timeout
        self.__zk_path = zk_path
        self.__zk_version = zk_version
        self.__weight = weight

    def __register_zookeeper(self):
        self.__zk_client.register(self.__zk_path + '/' + self.__zk_version, self.__address, self.__port, self.__weight)

    def __quit_process(self, signum, frame):
        if signum == signal.SIGINT:
            self.__zk_client.unregister(self.__zk_path + '/' + self.__zk_version, self.__address, self.__port, self.__weight)
            print 'bye boy...'
            sys.exit(0)

    def start(self, processor_cls):
        self.__zk_client = ZkServiceRegister(self.__zk_address, self.__zk_timeout)
        processor = processor_cls(self.__handler)
        pfactory = TBinaryProtocolFactory()
        self.__server = TTornado.TTornadoServer(processor, pfactory)
        signal.signal(signal.SIGINT, self.__quit_process)
        signal.signal(signal.SIGTERM, self.__quit_process)
        self.__server.bind(port=self.__port, address='0.0.0.0')
        self.__server.start(1)
        self.__register_zookeeper()
        print('start server done.')

    def stop(self):
        self.__zk_client.unregister(self.__zk_path + '/' + self.__zk_version, self.__address, self.__port, self.__weight)
        if self.__server:
            self.__server.stop()

        sys.exit(0)


