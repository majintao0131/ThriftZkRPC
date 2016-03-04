#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.exceptions import *
from tornado import gen

DEFAULT_HOST_WEIGHT = 20

class ZkServiceRegisterListener:
    def __init__(self, client):
        self.__client = client

    def __call__(self, state):
        if state == KazooState.LOST:
            print "warning : connection lost."
        elif state == KazooState.CONNECTED:
            print "info : connection connected."
        elif state == KazooState.SUSPENDED:
            print "warning : connection suspended."
        else:
            print "warning : other connection states."

class ZkServiceRegister:
    def __init__(self, zk_address, zk_timeout):
        self.__zkClient = KazooClient(hosts=zk_address, timeout=zk_timeout, read_only=False)
        self.__zkListener = ZkServiceRegisterListener(self.__zkClient)
        self.__zkClient.add_listener(self.__zkListener)
        self.__zkClient.start()

    def register(self, path, host, port, weight=DEFAULT_HOST_WEIGHT):
        try:
            if not self.__zkClient.exists(path):
                self.__zkClient.ensure_path(path)
        except Exception, e:
            print e.message

        reg_path = path + '/' + host + ':' + str(port) + ':' + str(weight)
        if self.__zkClient.exists(reg_path):
            self.__zkClient.delete(reg_path)

        self.__zkClient.create(reg_path, value='', ephemeral=True)

    def unregister(self, path, host, port, weight=DEFAULT_HOST_WEIGHT):
        reg_path = path + '/' + host + ':' + str(port) + ':' + str(weight)
        if self.__zkClient.exists(reg_path):
            try:
                self.__zkClient.delete(reg_path)
            except NoNodeError:
                return True
            except:
                return False

    def stop(self):
        self.__zkClient.stop()