__author__ = 'jintao'

from RPCClient.RPCClient import RPCClient
import logging
from tornado.ioloop import IOLoop
import datetime
from tornado import gen
import time
from time import clock

rpc_client = None
logging.basicConfig()

@gen.coroutine
def communicate(param):
    global rpc_client
    conn = rpc_client.get_client('EchoService1').echo(param)

    if not conn:
        print 'no valid connection to be used.'
        return
    start = clock()
    result = yield conn.connection().echo(param)
    finish = clock()
    print 'use ' + str(finish - start) + ' us, result : ' + result
    rpc_client.put_client('EchoService1', conn)

def client():
    global rpc_client
    rpc_client = RPCClient('Client.xml')
    if not rpc_client.init():
        print 'client init failed.'
        return
    time.sleep(1)
    io_loop = IOLoop.instance()
    def doCommunicate(param):
        communicate(param)
        io_loop.add_timeout(datetime.timedelta(seconds=0.1), doCommunicate, param)
    io_loop.add_callback(doCommunicate, "test1\n")
    #io_loop.add_callback(doCommunicate, "test2")
    #io_loop.add_callback(doCommunicate, "test3")
    io_loop.start()

if __name__ == '__main__':
    print 'in'
    client()
    print 'out'