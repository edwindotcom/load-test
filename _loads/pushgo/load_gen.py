#!/usr/bin/python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import time

from loads.case import TestCase

import gevent
from gevent import monkey

from wsocket import WsClient
from pushtest.utils import (
    get_rand,
    get_prob,
    get_uaid,
    str_gen,
    send_http_put)

TARGET_SERVER = "ws://ec2-54-244-206-75.us-west-2.compute.amazonaws.com:8080"
# TARGET_SERVER = "ws://localhost:8080"
PATCHED = False
TIMEOUT  = 10


class TestLoad(TestCase):

    """
    Load test for pushgo. Runs types of tests:
    - connect, hello, register, update, ack, close
    - connect, hello, register, update, close
    - connect, hello, register, update loop one channel, ack, close
    - connect, hello, register, update loop different channel, ack, close
    - connect, hello, register, update, ack, ping loop, close

    You can run this by installing Loads and running this:
    loads-runner load_test.load_gen.TestLoad.test_load -c 10 -u 10
    """
    def test_load(self):
        global PATCHED
        if not PATCHED:
            monkey.patch_all()
            PATCHED = True

        ws = self.create_ws(TARGET_SERVER, klass=WsClient)
        ws.connect()

        # wait here until the server closes the socket
        # or until timeout is reached
        ws.run_forever(timeout=TIMEOUT)