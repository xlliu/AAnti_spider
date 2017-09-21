#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import ipdb

def download(self, stream):
    ramdom = str(uuid.uuid4())
    with open("./simulator/cicp/cicp_test/test_captcha/{}.png".format(ramdom), 'w') as o:
        o.write(stream)

download()