#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import time
import os
import sys
import logging

import gevent

from loads.case import TestCase
from loads.websockets import WebSocketClient

from utils import (
    get_rand,
    get_prob,
    get_uaid,
    str_gen,
    send_http_put)

TIMEOUT = 60

logger = logging.getLogger('WsClient')
fh = logging.FileHandler('/tmp/ws-client.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class WsClient(WebSocketClient):

    """ ws4py websocket client, executes send messages based on
    server response """

    def __init__(self, *args, **kw):
        super(WsClient, self).__init__(*args, **kw)
        self.endpoint = ""
        self.chan = ""
        self.uaid = ""
        self.version = 0
        self.data = {}

        self.count = 0
        self.sleep = 0
        self.max_sleep = 3
        self.max_updates = 10
        self.closer = None

        self.put_end = 0
        self.put_start = 0
        self.reg_time = 0
        self.put_time = 0

    def opened(self):
        super(WsClient, self).opened()
        self.sleep = get_rand(self.max_sleep)
        self.chan = get_uaid()
        self.uaid = get_uaid()
        self.version = int(str_gen(8))
        self.start_time = time.time()
        self.hello()

    def run_forever(self, timeout=TIMEOUT):
        # schedule the web socket to close in TIMEOUT seconds
        # if the server does not do it
        self.closer = gevent.spawn_later(TIMEOUT, self.close)
        self.closer.join()

    def closed(self, code, reason=None):
        super(WsClient, self).closed(code, reason)
        logger.error('Time to register: %s s' % (self.reg_time - self.start_time))
        logger.error('Time to notification: %s s' % (self.put_end - self.put_start))
        logger.error("Closed down: %s %s" % (code, reason))
        self.closer.kill()

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
                logger.error('ERROR status: %s' % data['status'])
                self.close()

    def new_chan(self):
        self.chan = get_uaid()
        self.version = int(str_gen(8))
        self.hello()

    def proc_data(self):
        pass

    def received_message(self, m):
        super(WsClient, self).received_message(m)
        self.data = json.loads(m.data)
        self.check_response(self.data)
        logger.error(self.data)

        if self.count > self.max_updates:
            self.close()
        else:
            self.proc_data()
            self.count += 1


class PingClient(WsClient):
    """ Sends {} to server till max_updates interval is reached """

    def proc_data(self):
        if "messageType" in self.data:
            time.sleep(self.sleep)
            if self.data["messageType"] == "hello":
                self.ping()
            if self.data["messageType"] == "ping":
                self.ping()


class HelloClient(WsClient):
    """ Sends hello and closes socket """

    def proc_data(self):
        if "messageType" in self.data:
            if self.data["messageType"] == "hello":
                self.close()


class ChanClient(WsClient):
    """ Sends hello, registers channel, puts, acks, puts.
        In 'new_chan' mode, unreg then reg a new channel each time. """

    def __init__(self, *args, **kw):
        super(ChanClient, self).__init__(*args, **kw)
        self.chan_type = ""

    def opened(self):
        super(ChanClient, self).opened()
        if self.chan_type == "one_uaid":
            self.uaid = 'one_uaid'

    def proc_data(self):
        if "messageType" in self.data:
            time.sleep(self.sleep)

            if self.data["messageType"] == "hello":
                self.reg()
            if self.data["messageType"] == "register":
                self.reg_time = time.time()
                self.endpoint = self.data["pushEndpoint"]
                self.put()

            if self.data["messageType"] == "notification":
                self.put_end = time.time()
                self.ack()

                if self.chan_type == "new_chan":
                    self.unreg()
                    self.new_chan()
                elif self.chan_type == "multi_chan":
                    self.unreg()
                    self.new_chan()
                    self.new_chan()
                else:
                    self.version += 1
                    self.put()


class FuzzClient(WsClient):
    """ Sends mixed messages to socket """

    def opened(self):
        super(FuzzClient, self).opened()
        self.sleep = get_rand(self.max_sleep)
        self.chan = get_uaid()
        self.uaid = get_uaid()
        self.version = 0
        self.start_time = time.time()
        self.send_fuzz()

    def send_fuzz(self):
        self.reg()
        self.ping()
        self.hello()
        self.unreg()
        self.ack()
        self.hello()
        self.send('{"messageType":"garbage", "channelIDs":[{ "channelID":true, "version": 23 }], "uaid":123}')
        self.send('{"foo":123}')
        self.ping()

    def received_message(self, m):
        super(WsClient, self).received_message(m)
        self.data = json.loads(m.data)
        logger.error(self.data)
        time.sleep(self.sleep)
        self.send_fuzz()
