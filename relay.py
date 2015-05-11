# -*- coding: utf-8 -*-

import json
import logging
import os

from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.tcpserver import TCPServer


default_config = {
    'client-side-port': 8888,
    'key-side-port': 8889,
}


def dumpb(o):
    return json.dumps(o).encode() + b'\n'


def loadb(b):
    return json.loads(b[:-1].decode())


class ClientSide(TCPServer):

    def __init__(self):
        super().__init__()
        self.clients = {}

    @coroutine
    def handle_stream(self, stream, address):
        request = loadb((yield stream.read_until(b'\n')))
        request['stream'] = stream
        self.clients[request['device']] = request

    def list(self):
        return list({'code': c['device'], 'name': c['name']} for c in self.clients.values())

    def link(self, key_stream, target):
        client_stream = self.clients[target]['stream']
        def key_read(_):
            key_stream.read_bytes(4096, key_read, client_stream.write)
        def client_read(_):
            client_stream.read_bytes(4096, client_read, key_stream.write)
        key_read(None)
        client_read(None)


class KeySide(TCPServer):

    def __init__(self, client_side):
        super().__init__()
        self.client_side = client_side

    @coroutine
    def handle_stream(self, stream, address):
        request = loadb((yield stream.read_until(b'\n')))
        command = request['command']
        if command == 'list':
            yield stream.write(dumpb(self.client_side.list()))
        else:
            self.client_side.link(stream, request['target'])


def load_config(path):
    config = {}
    logging.info('load config from {}'.format(path))
    if os.path.exists(path):
        with open(path) as f:
            config = json.load(f)
    else:
        logging.warning('config file not found, use default config')
    for k, v in default_config.items():
        config.setdefault(k, v)
    return config


def main():
    config = load_config('lockman-relay.json')
    client_side = ClientSide()
    client_side.listen(config['client-side-port'])
    key_side = KeySide(client_side)
    key_side.listen(config['key-side-port'])


if __name__ == '__main__':
    main()
    IOLoop.instance().start()
