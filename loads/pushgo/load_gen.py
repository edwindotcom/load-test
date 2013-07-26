#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import time

from ws4py.client.threadedclient import WebSocketClient

from loads.case import TestCase
from pushtest.utils import (
    get_rand,
    get_prob,
    get_uaid,
    str_gen,
    send_http_put)

TARGET_SERVER = "ws://ec2-54-244-206-75.us-west-2.compute.amazonaws.com:8080"
# TARGET_SERVER = "ws://localhost:8080"

# either error or debug
LOG_LEVEL = 'error' 

def _log(txt, level = 'debug'):
    if LOG_LEVEL == level:
        print '::', txt


class WsClient(WebSocketClient):

    """ ws4py websocket client, executes send messages based on
    server response """

    endpoint = ""
    chan = ""
    uaid = ""
    version = 0
    count = 0
    sleep = 20

    reg_time = 0
    put_start = 0
    put_end = 0

    client_type = ""
    max_sleep = 21
    max_updates = 10
    timeout = 30
    last_time = 0

    client_types = {'conn_close': 30,
                    'conn_noack': 5,
                    'one_chan': 30,
                    'multi_chan': 30,
                    'ping_loop': 5}

    def opened(self):
        self.client_type = 'ping_loop'
        #self.client_type = get_prob(self.client_types)
        _log(self.client_type)

        self.sleep = get_rand(self.max_sleep)
        self.chan = str_gen(8)
        self.uaid = get_uaid()
        self.version = int(str_gen(8))
        self.start_time = time.time()
        self.last_time = self.start_time

        self.hello()

    def closed(self, code, reason=None):
        if self.client_type != 'ping_loop':
            _log('\nTime to register: %s s' % (self.reg_time - self.start_time))
            _log('Time to notification: %s s' % (self.put_end - self.put_start))

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
                _log('ERROR status: %s' % data['status'], 'error')
                self.close()

    def new_chan(self):
        self.chan = str_gen(8)
        self.version = int(str_gen(8))
        self.hello()

    def check_timeout(self):
        _log(time.time() - self.last_time)
        if time.time() > self.last_time + float(self.timeout):
            _log('\nTIMEOUT: %s seconds' % self.timeout, 'error')
            self.close()
        else:
            self.last_time = time.time()

    def received_message(self, m):
        data = json.loads(m.data)
        self.check_response(data)
        self.check_timeout()

        _log(data)

        if self.count > self.max_updates:
            self.close()
        else:
            if "messageType" in data:
                time.sleep(self.sleep)

                if data["messageType"] == "hello":
                    if self.client_type == 'ping_loop':
                        self.ping()
                    else:
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


class TestLoad(TestCase):

    """
    Load test for pushgo. Runs types of tests:
    - connect, hello, register, update, ack, close
    - connect, hello, register, update, close
    - connect, hello, register, update loop one channel, ack, close
    - connect, hello, register, update loop different channel, ack, close
    - ping_loop: connect, hello, ping loop, close

    You can run this by installing Loads and running this:
    loads-runner load_gen.TestLoad.test_load -c 10 -u 10
    """

    def test_load(self):
        try:
            ws = WsClient(TARGET_SERVER)

            ws.connect()
            ws.run_forever()
        except Exception as e:
            _log('Exception: %s' % e)
            ws.close()
