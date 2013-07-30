#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import time
import os, sys

from loads.case import TestCase
from loads.websockets import WebSocketClient

from pushtest.utils import (
    get_rand,
    get_prob,
    get_uaid,
    str_gen,
    send_http_put)

TARGET_SERVER = "ws://ec2-54-244-206-75.us-west-2.compute.amazonaws.com:8080"
# TARGET_SERVER = "ws://localhost:8080"
VERBOSE = True

def _log(txt):
    if VERBOSE:
        print '::', txt


class WsClient(WebSocketClient):

    """ ws4py websocket client, executes send messages based on
    server response """

    endpoint = ""
    chan = ""
    uaid = ""
    version = 0
    count = 0
    sleep = 0
    put_end = 0
    put_start = 0
    reg_time = 0
    put_time = 0

    client_type = ""
    max_sleep = 1
    max_updates = 5
    timeout = 20

    client_types = {'conn_close': 30,
                    'conn_noack': 5,
                    'one_chan': 30,
                    'multi_chan': 30,
                    'ping_loop': 5}

    def opened(self):
        super(WsClient, self).opened()
        self.client_type = get_prob(self.client_types)
        _log(self.client_type)

        self.sleep = get_rand(self.max_sleep)
        self.chan = str_gen(8)
        self.uaid = get_uaid()
        self.version = int(str_gen(8))
        self.start_time = time.time()

        self.hello()

    def closed(self, code, reason=None):
        super(WsClient, self).closed(code, reason)
        print('\nTime to register: %s s' % (self.reg_time - self.start_time))
        print('Time to notification: %s s' % (self.put_end - self.put_start))
        _log("Closed down: %s %s" % (code, reason))

    def hello(self):
        self.send('{"messageType":"hello", "channelIDs":[], "uaid":"%s"}'
                  % self.uaid)

    def reg(self):
        self.send(
            '{"messageType":"register", "channelID":"%s", "uaid":"%s"}' %
            (self.chan, self.uaid))

    def unreg(self):
        self.send(
            '{"messageType":"unregister", "channelID":"%s"}' %
            self.uaid)

    def put(self):
        self.put_start = time.time()
        send_http_put(self.endpoint, "version=%s" % self.version)

    def ack(self):
        self.send('{"messageType":"ack",  "updates": [{"channelID": "%s", "version": %s}]}'
                  % (self.chan, self.version))

    def ping(self):
        self.send('{}')

    def check_response(self, data):
        if "status" in data.keys():
            if data['status'] != 200:
                _log('ERROR status: %s' % data['status'])
                self.close()

    def new_chan(self):
        self.chan = str_gen(8)
        self.version = int(str_gen(8))
        self.hello()

    def received_message(self, m):
        super(WsClient, self).received_message(m)
        data = json.loads(m.data)
        self.check_response(data)

        _log(data)

        if self.count > self.max_updates:
            self.close()
        elif time.time() > self.start_time + float(self.timeout):
            _log('TIMEOUT: %s seconds' % self.timeout)
            self.close()
        else:
            if "messageType" in data:
                time.sleep(self.sleep)

                if data["messageType"] == "hello":
                    self.reg()
                if data["messageType"] == "register":
                    self.reg_time = time.time()
                    self.endpoint = data["pushEndpoint"]
                    self.put()
                if data["messageType"] == "ping":
                    self.ping()

                if data["messageType"] == "notification":
                    self.put_end = time.time()
                    if self.client_type != 'conn_noack':
                        self.ack()
                    if self.client_type == 'conn_close' or self.client_type == 'conn_noack':
                        self.unreg()
                        self.close()
                    if self.client_type == 'one_chan':
                        self.version += 1
                        self.put()
                    elif self.client_type == 'multi_chan':
                        self.unreg()
                        self.new_chan()
                    elif self.client_type == 'ping_loop':
                        self.ping()

                self.count += 1



