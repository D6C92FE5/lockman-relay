# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.tcpclient import TCPClient

from relay import loadb, dumpb

@coroutine
def key():
    stream = yield TCPClient().connect('localhost', 8889)
    yield stream.write(dumpb({'command': 'list'}))
    response = loadb((yield stream.read_until(b'\n')))
    print(response)
    stream.close()
    device_code = response[0]['code']

    stream = yield TCPClient().connect('localhost', 8889)
    yield stream.write(dumpb({'command': 'link', 'target': device_code}))
    stream = yield stream.start_tls(True, {'keyfile': 'cert/tls.key', 'certfile': 'cert/tls.crt'})
    yield stream.write(dumpb({'command': 'unlock'}))
    response = loadb((yield stream.read_until(b'\n')))
    print(response)
    stream.close()

IOLoop.instance().add_callback(key)
IOLoop.instance().start()
