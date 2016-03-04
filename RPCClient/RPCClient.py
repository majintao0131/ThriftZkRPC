#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

from ConnectionPool import ConnectionPool
from ZkServiceProvider import ZkServiceProvider
from Util.ConfigLoader import ConfigLoader

class RPCClient:
    def __init__(self, path):
        self.__zk_provider = None
        self.__connection_pool = None
        self.__path = path
        self.__zookeeper_hosts = ''
        self.__zookeeper_timeout = 0
        self.__service_list = []
        self.__config = ConfigLoader(path)

    def load_class(self, name, module):
        components = name.split('.')
        cls = getattr(module, components[0])
        for comp in components[1:]:
            cls = getattr(cls, comp)
        return cls

    def init(self):
        if not self.__config.init():
            return False
        try:
            self.__zookeeper_hosts = self.__config.value('client', 'zookeeper','address')
            self.__zookeeper_timeout = int(self.__config.value('client', 'zookeeper','timeout'))
        except:
            return False

        self.__connection_pool = ConnectionPool()
        self.__zk_provider = ZkServiceProvider(self.__zookeeper_hosts, self.__zookeeper_timeout, self.__connection_pool)

        self.__service_list = self.__config.value('client', 'service')
        if not self.__service_list:
            return False

        for service in self.__service_list:
            try:
                service_name = service['service_name']
                service_path = service['name'] + '/' + service['version']
                module_name = service['client_module']
                module = __import__(module_name)
                client_cls_name = service['client_class']
                client_cls = self.load_class(client_cls_name, module)
                self.__connection_pool.register_service(service_name, service_path, client_cls)
                if not self.__zk_provider.register_service(service_name, service_path, client_cls):
                    print 'register service to zookeeper provider failed.'
                    return False
            except:
                print 'load module or class failed.'
                return False

        return True

    def service(self, service):
        if not self.__connection_pool:
            print 'Dont init the connection pool.'
            return None

        host_node = self.__connection_pool.get_host(service)
        return host_node

    def get_client(self, serivce):
        if not self.__connection_pool:
            print 'Dont init the connection pool.'
            return None

        client = self.__connection_pool.get_client(serivce)
        return client

    def put_client(self, service, client):
        return self.__connection_pool.put_client(service, client)

