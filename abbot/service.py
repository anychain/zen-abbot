# -*- coding: utf-8 -*-
###########################################
# Licensed Materials - Property of esse.io
# 
# (C) Copyright esse.io. 2015 All Rights Reserved
#
# Author: Bryan HUANG (bryan@esse.io)
#
###########################################


import collections
import datetime
import itertools
import os
import socket
import warnings

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_serialization import jsonutils
from oslo_service import service
from oslo_service import threadgroup
from oslo_utils import uuidutils
from osprofiler import profiler
import six
import webob

from abbot import context
from abbot import exception
from abbot.i18n import _

LOG = logging.getLogger(__name__)


@profiler.trace_cls("rpc")
class EngineListener(service.Service):
    '''
    Listen on an AMQP queue named for the engine.  Allows individual
    engines to communicate with each other for multi-engine support.
    '''

    ACTIONS = (STOP_STACK, SEND) = ('stop_stack', 'send')

    def __init__(self, host, engine_id, thread_group_mgr):
        super(EngineListener, self).__init__()
        self.thread_group_mgr = thread_group_mgr
        self.engine_id = engine_id
        self.host = host

    def start(self):
        super(EngineListener, self).start()
        self.target = messaging.Target(
            server=self.engine_id,
            topic=rpc_api.LISTENER_TOPIC)
        server = rpc_messaging.get_rpc_server(self.target, self)
        server.start()

    def listening(self, ctxt):
        '''
        Respond affirmatively to confirm that the engine performing the
        action is still alive.
        '''
        return True

    def stop_stack(self, ctxt, stack_identity):
        '''Stop any active threads on a stack.'''
        stack_id = stack_identity['stack_id']
        self.thread_group_mgr.stop(stack_id)

    def send(self, ctxt, stack_identity, message):
        stack_id = stack_identity['stack_id']
        self.thread_group_mgr.send(stack_id, message)