#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import time

from loads.case import TestCase

import gevent
from gevent import monkey

from wsocket import WsClient, PingClient, HelloClient, ChanClient, FuzzClient

TARGET_SERVER = "ws://ec2-54-244-206-75.us-west-2.compute.amazonaws.com:8080"
PATCHED = False
TIMEOUT  = 60


class TestLoad(TestCase):

    def setup():
        global PATCHED
        if not PATCHED:
            monkey.patch_all()
            PATCHED = True

    def test_ping(self):
        ws = self.create_ws(TARGET_SERVER, klass=PingClient)
        ws.connect()

        # wait here until the server closes the socket
        # or until timeout is reached
        ws.run_forever(timeout=TIMEOUT)

    def test_hello(self):
        ws = self.create_ws(TARGET_SERVER, klass=HelloClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_one_chan(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_new_chan(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.chan_type = "new_chan"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_one_uaid(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.chan_type = "one_uaid"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_fuzz(self):
        ws = self.create_ws(TARGET_SERVER, klass=FuzzClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)