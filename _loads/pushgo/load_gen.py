#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import time
import random

import gevent
from gevent import monkey

from loads.case import TestCase
from wsocket import (WsClient,
                     PingClient,
                     HelloClient,
                     ChanClient,
                     FuzzClient)

TARGET_SERVER = "ws://ec2-54-244-206-75.us-west-2.compute.amazonaws.com:8080"
PATCHED = False
TIMEOUT = 60
MIN_SLEEP = 5
MAX_SLEEP = 10
MAX_UPDATES = 20

class TestLoad(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLoad, self).__init__(*args, **kwargs)
        self.choices = ([self.test_ping] * 20 +
                        [self.test_hello] * 15 +
                        [self.test_one_chan] * 25 +
                        [self.test_new_chan] * 25 +
                        [self.test_multi_chan] * 10 +
                        [self.test_fuzz] * 5)

        self.choices_long = ([self.test_ping_long] * 20 +
                             [self.test_hello_long] * 15 +
                             [self.test_one_chan_long] * 25 +
                             [self.test_new_chan_long] * 25 +
                             [self.test_multi_chan_long] * 10 +
                             [self.test_fuzz_long] * 5)


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

    def test_ping_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=PingClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_hello(self):
        ws = self.create_ws(TARGET_SERVER, klass=HelloClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_hello_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=HelloClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_one_chan(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_one_chan_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_new_chan(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.chan_type = "new_chan"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_new_chan_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.chan_type = "new_chan"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_multi_chan(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.chan_type = "multi_chan"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_multi_chan_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=ChanClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.chan_type = "multi_chan"
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_fuzz(self):
        ws = self.create_ws(TARGET_SERVER, klass=FuzzClient)
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_fuzz_long(self):
        ws = self.create_ws(TARGET_SERVER, klass=FuzzClient)
        ws.sleep = MIN_SLEEP
        ws.max_sleep = MAX_SLEEP
        ws.max_updates = MAX_UPDATES
        ws.connect()
        ws.run_forever(timeout=TIMEOUT)

    def test_all(self):
        """ Current rates:

        - test_ping: 20%
        - test_hello: 15%
        - test_one_chan: 25%
        - test_new_chan: 25%
        - test_multi_chan: 10%
        - test_fuzz: 5%
        """
        random.choice(self.choices)()

    def test_all_long(self):

        random.choice(self.choices_long)()
