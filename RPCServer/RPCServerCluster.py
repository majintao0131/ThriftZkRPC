#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

import signal
import sys
import os
import time
from RPCServer import RPCServer
from Util.ConfigLoader import ConfigLoader
from tornado.ioloop import IOLoop
from multiprocessing import Process

class RPCServerCluster:
    def __init__(self, path, handler):
        self.__handler = handler
        self.__address = '0.0.0.0'
        self.__server_count = 0
        self.__processores = []
        self.__port = []
        self.__weight = 10
        self.__zk_address = ''
        self.__zk_timeout = 3000
        self.__zk_path = ''
        self.__zk_version = ''
        self.__configs = ConfigLoader(path)

    def init(self):
        if not self.__configs.init():
            return False

        try:
            self.__zk_address = self.__configs.value('server', 'zookeeper', 'address')
            self.__zk_timeout = int(self.__configs.value('server', 'zookeeper', 'timeout'))
        except:
            print 'get zk_address or zk_timeout configure failed.'
            return False

        try:
            self.__zk_path = self.__configs.value('server', 'service', 'path')
            self.__zk_version = self.__configs.value('server', 'service', 'version')
            self.__weight = int(self.__configs.value('server', 'service', 'weight'))
            port_list = self.__configs.value('server', 'service', 'port')
            for port in port_list:
                self.__port.append(int(port))
                self.__server_count += 1
        except:
            print 'get zk_path or zk_version or port or weight configure failed.'
            return False

        self.__address = '192.168.15.246'
        #self.__address = Common.get_ip_address('eth0')

        return True

    def __quit_process(self, signum, frame):
        if signum == signal.SIGINT:
            self.stop()

    def fork_process(self, index, processor_cls):
        if index == self.__server_count:
            return

        forkPID = os.fork()
        if forkPID == 0:
            server = RPCServer(self.__zk_address,
                               self.__zk_path,
                               self.__zk_version,
                               self.__handler,
                               self.__address,
                               self.__port[index],
                               self.__weight,
                               self.__zk_timeout)
            server.start(processor_cls)
        else:
            index += 1
            self.__processores.append(forkPID)
            self.fork_process(index, processor_cls)

    def start(self, processor_cls):
        signal.signal(signal.SIGINT, self.__quit_process)
        if self.__server_count == 0:
            return
        index = 0

        self.fork_process(index, processor_cls)

        IOLoop.instance().start()

    def stop(self):
        for pid in self.__processores:
            os.kill(pid, signal.SIGINT)
            time.sleep(1)

        sys.exit(0)

