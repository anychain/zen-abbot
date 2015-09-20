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

from abbot.common import context
from abbot.common import exception
from abbot.common.i18n import _
from abbot.common import messaging as rpc_messaging
from abbot.common import policy

LOG = logging.getLogger(__name__)


@profiler.trace_cls("rpc")
class EngineService(service.Service):
    """
    Manages the running instances from creation to destruction.
    All the methods in here are called from the RPC backend.  This is
    all done dynamically so if a call is made via RPC that does not
    have a corresponding method here, an exception will be thrown when
    it attempts to call into this class.  Arguments to these methods
    are also dynamically added and will be named as keyword arguments
    by the RPC caller.
    """

    RPC_API_VERSION = '0.1'

    def __init__(self, host, topic):
        super(EngineService, self).__init__()
        self.host = host
        self.topic = topic
        self.binary = 'abbot-engine'
        self.hostname = socket.gethostname()

        # The following are initialized here, but assigned in start() which
        # happens after the fork when spawning multiple worker processes
        self.listener = None
        self.worker_service = None
        self.engine_id = None
        self.target = None
        self.service_id = None
        self._rpc_server = None
        self.software_config = service_software_config.SoftwareConfigService()
        self.resource_enforcer = policy.ResourceEnforcer()

        if cfg.CONF.trusts_delegated_roles:
            warnings.warn('The default value of "trusts_delegated_roles" '
                          'option in abbot.conf is changed to [] in Kilo '
                          'and abbot will delegate all roles of trustor. '
                          'Please keep the same if you do not want to '
                          'delegate subset roles when upgrading.',
                          Warning)

    def start(self):
        self.engine_id = stack_lock.StackLock.generate_engine_id()
        self.thread_group_mgr = ThreadGroupManager()
        self.listener = EngineListener(self.host, self.engine_id,
                                       self.thread_group_mgr)
        LOG.debug("Starting listener for engine %s" % self.engine_id)
        self.listener.start()

        target = messaging.Target(
            version=self.RPC_API_VERSION, server=self.host,
            topic=self.topic)

        self.target = target
        self._rpc_server = rpc_messaging.get_rpc_server(target, self)
        self._rpc_server.start()
        self._client = rpc_messaging.get_rpc_client(
            version=self.RPC_API_VERSION)

        self.service_manage_cleanup()

        super(EngineService, self).start()

    def _stop_rpc_server(self):
        # Stop rpc connection at first for preventing new requests
        LOG.debug("Attempting to stop engine service...")
        try:
            self._rpc_server.stop()
            self._rpc_server.wait()
            LOG.info(_LI("Engine service is stopped successfully"))
        except Exception as e:
            LOG.error(_LE("Failed to stop engine service, %s"), e)

    def stop(self):
        self._stop_rpc_server()

        ctxt = context.get_admin_context()
        service_objects.Service.delete(ctxt, self.service_id)
        LOG.info(_LI('Service %s is deleted'), self.service_id)

        # Terminate the engine process
        LOG.info(_LI("All threads were gone, terminating engine"))
        super(EngineService, self).stop()

    def reset(self):
        super(EngineService, self).reset()
        logging.setup(cfg.CONF, 'abbot')

    def service_manage_cleanup(self):
        cnxt = context.get_admin_context()
        last_updated_window = (3 * cfg.CONF.periodic_interval)
        time_line = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=last_updated_window)

        service_refs = service_objects.Service.get_all_by_args(
            cnxt, self.host, self.binary, self.hostname)
        for service_ref in service_refs:
            if (service_ref['id'] == self.service_id or
                    service_ref['deleted_at'] is not None or
                    service_ref['updated_at'] is None):
                continue
            if service_ref['updated_at'] < time_line:
                # hasn't been updated, assuming it's died.
                LOG.info(_LI('Service %s was aborted'), service_ref['id'])
                service_objects.Service.delete(cnxt, service_ref['id'])
