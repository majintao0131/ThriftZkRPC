#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

from kazoo.client import KazooClient
from kazoo.client import KazooState
from kazoo.recipe.watchers import ChildrenWatch
from kazoo.protocol.states import EventType
from kazoo.exceptions import *
from tornado import gen

class ZkServiceProviderListener:
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

class ZkServiceProvider:
    def __init__(self, zk_address, zk_timeout, connection):
        self.__service_dict = {}
        self.__zk_address = zk_address
        self.__zkClient = KazooClient(hosts=zk_address, timeout=zk_timeout, read_only=True)
        self.__zkClient.start()
        self.__zkListener = ZkServiceProviderListener(self.__zkClient)
        self.__zkClient.add_listener(self.__zkListener)
        self.__connection = connection

    def register_service(self, service, zk_path, client_cls):
        self.__service_dict[service] = (zk_path, client_cls)
        result = self._register_watcher(service, zk_path, client_cls)
        return result

    def _register_watcher(self, service, zk_path, client_cls):
        @self.__zkClient.ChildrenWatch(zk_path)
        def child_changed(data):
            print '+++++++++++++++' + service + ' child changed.++++++++++++++++++'
            print data
            hosts = data
            self.__connection.update_service(service, hosts)

        isExists = self.__zkClient.exists(zk_path)
        if not isExists:
            return False

        try:
            hosts = self.__zkClient.get_children(zk_path)
        except NoNodeError:
            print 'no node for the path of ' + zk_path
            return False
        except:
            print 'other exceptions.'
            return False

        self.__connection.update_service(service, hosts)
        return True

    def stop(self):
        self.__zkClient.stop()