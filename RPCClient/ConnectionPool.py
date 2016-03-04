#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'jintao'

from Queue import Queue

from thrift.TTornado import TTornadoStreamTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory
from tornado import gen

DEFAULT_NETWORK_TIMEOUT = 0
DEFAULT_POOL_SIZE = 20
HOST_STATUS_VALID = 2
HOST_STATUS_INIT = 1
HOST_STATUS_INVALID = 0
CONNECTION_TYPE_TEMPORARY = 0
CONNECTION_TYPE_PERMANENT = 1
MAX_POOL_SIZE = 100

class RPCConnection:
    def __init__(self, host, type, connection):
        self.__host = host
        self.__type = type
        self.__connection = connection

    def host(self):
        return self.__host

    def type(self):
        return self.__type

    def connection(self):
        return self.__connection

class HostNode:
    def __init__(self, version, host, port, weight, client_cls, network_timeout):
        self.__version = version
        self.__host = host
        self.__port = port
        self.__weight = weight
        self.__client_cls = client_cls
        self.__connection_queue = []
        self.__network_timeout = network_timeout
        self.__permanet_size = 0
        self.__current_size = 0
        self.__status = HOST_STATUS_INVALID

    def _create_connection(self, type):
        transport = TTornadoStreamTransport(self.__host, self.__port)
        pfactory = TBinaryProtocolFactory()
        connection = self.__client_cls(transport, pfactory)
        rpc_connection = RPCConnection(self.__host + ':' + str(self.__port) + ':' + str(self.__weight), type, connection)

        try:
            transport.open()
        except Exception,e:
            pass

        return rpc_connection

    def init(self):
        for i in range(0, self.__weight):
            try:
                print 'create permanent connection.'
                conn = self._create_connection(CONNECTION_TYPE_PERMANENT)
            except Exception, e:
                return False

            self.__connection_queue.append(conn)
            self.__current_size += 1
            self.__permanet_size += 1
            self.__status = HOST_STATUS_INIT
            if self.__current_size == self.__weight:
                self.__status = HOST_STATUS_VALID

            if self.__current_size >= MAX_POOL_SIZE:
                break

        return True

    def refresh(self, version):
        self.__version = version

    def version(self):
        return self.__version

    def status(self):
        return self.__status

    def set_status(self, status):
        self.__status = status

    def close_all(self):
        while True:
            try:
                conn = self.__connection_queue.pop(0)
                conn.connection()._transport.close()
            except IndexError, e:
                break
        self.__current_size = 0
        self.__permanet_size = 0
        print 'permanent size : ' + str(self.__permanet_size)
        print 'current size : ' + str(self.__current_size)

    def get_connection(self):
        try:
            conn = self.__connection_queue.pop(0)
            return conn
        except IndexError, e:
            if self.__current_size >= MAX_POOL_SIZE:
                return None

            conn = self._create_connection(CONNECTION_TYPE_TEMPORARY)
            print 'create temporary connection'
            self.__current_size += 1
            print 'current size : ' + str(self.__current_size)
            return conn

    def put_connection(self, conn):
        if self.__status == HOST_STATUS_INVALID:
            conn.connection()._transport.close()
            if self.__permanet_size > 0:
                self.__permanet_size -= 1
            if self.__current_size > 0:
                self.__current_size -= 1
            return

        if conn.type() == CONNECTION_TYPE_TEMPORARY:
            print 'close temporary connection'
            conn.connection()._transport.close()
            if self.__current_size > 0:
                self.__current_size -= 1
            return

        self.__connection_queue.append(conn)


class ServiceNode:
    def __init__(self, service_name, zk_path, client_cls):
        self.__service_name = service_name
        self.__zk_path = zk_path
        self.__version = 0
        self.__client_cls = client_cls
        self.__host_pool = {}       # dict<host, pool>

    def refresh(self, host_list):
        print 'service node : ' + self.__service_name + ' refresh'
        self.__version += 1
        for host in host_list:
            if host not in self.__host_pool:
                self.add_host(host)
            else:
                print 'refresh host version : ' + str(self.__version)
                self.__host_pool[host].refresh(self.__version)

        self.clear_hosts()

    def version(self):
        return self.__version

    def zk_path(self):
        return self.__zk_path

    def service_name(self):
        return self.__service_name

    def clear_hosts(self):
        for host in self.__host_pool.keys():
            print 'host : ' + host
            host_node = self.__host_pool[host]
            if host_node.version() < self.__version:
                print "host version : " + str(host_node.version()) + "; service version : " + str(self.__version)
                self.__host_pool[host].close_all()
                del self.__host_pool[host]
                print 'clear host : ' + str(self.__host_pool[host])

    '''
        method : add_host
        create the connections for the new host asynchronously
    '''
    def add_host(self, host, network_timeout=DEFAULT_NETWORK_TIMEOUT):
        args = host.split(":")
        if len(args) != 3:
            return False
        try:
            host_name = args[0]
            port = int(args[1])
            weight = int(args[2])
        except:
            return False

        print 'new node : ' + host_name
        new_node = HostNode(self.__version, host_name, port, weight, self.__client_cls, network_timeout)
        self.__host_pool[host] = new_node
        result = new_node.init()
        return True

    '''
        method : remove_host
        firstly, remove the host from the host list,
        then close all connection of the host
    '''
    def remove_host(self, host):
        if host in self.__host_pool:
            node = self.__host_pool[host]
            node.set_status(HOST_STATUS_INVALID)
            node.close()
            del self.__host_pool[host]

    def get_client(self):
        count = len(self.__host_pool)
        passed = 0
        while passed < count:
            try:
                (host, host_node) = self.__host_pool.popitem()
                passed += 1
                self.__host_pool[host] = host_node
                if host_node.status() == HOST_STATUS_VALID or host_node.status() == HOST_STATUS_INIT:
                    conn = host_node.get_connection()
                    return conn
            except KeyError:
                return None

    def put_client(self, conn):
        if conn.host() not in self.__host_pool:
            conn.connection()._transport.close()
            return False

        host_node = self.__host_pool[conn.host()]
        host_node.put_connection(conn)
        return True


class ConnectionPool:
    def __init__(self):
        self.__service_pool = {}

    def register_service(self, service, zk_path, client_cls):
        if service not in self.__service_pool:
            new_node = ServiceNode(service, zk_path, client_cls)
            self.__service_pool[service] = new_node
            return new_node

        return self.__service_pool[service]

    def update_service(self, service, hosts):
        if service not in self.__service_pool:
            return False

        service_node = self.__service_pool[service]
        print 'service_node name : ' + str(service_node)
        service_node.refresh(hosts)

    def unregister_service(self, service):
        if service not in self.__service_pool:
            raise gen.Return(True)

        service_node = self.__service_pool[service]
        del self.__service_pool[service]
        service_node.clear_hosts()

    def get_client(self, service_name):
        if service_name not in self.__service_pool:
            return None

        service_node = self.__service_pool[service_name]
        client = service_node.get_client()

        return client

    def put_client(self, service_name, client):
        if service_name not in self.__service_pool:
            client.connection()._transport.close()
            return True

        service_node = self.__service_pool[service_name]
        return service_node.put_client(client)