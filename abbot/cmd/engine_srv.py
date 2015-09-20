# -*- coding: utf-8 -*-
###########################################
# Licensed Materials - Property of esse.io
# 
# (C) Copyright esse.io. 2015 All Rights Reserved
#
# Author: Bryan HUANG (bryan@esse.io)
#
###########################################

"""
Abbot Engine Server.  This does the work of actually implementing the API
calls made by the user.  Normal communications is done via the abbot API
which then calls into this engine.
"""

import eventlet
eventlet.monkey_patch()

import sys

from oslo_config import cfg
import oslo_i18n as i18n
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
from oslo_service import service

from abbot.common import config
from abbot.common.i18n import _LC
from abbot.common import messaging
from abbot.rpc import api as rpc_api
from abbot import version

i18n.enable_lazy()

LOG = logging.getLogger('abbot.engine')


def main():
    logging.register_options(cfg.CONF)
    cfg.CONF(project='abbot', prog='abbot-engine',
             version=version.version_info.version_string())
    logging.setup(cfg.CONF, 'abbot-engine')
    logging.set_defaults()
    messaging.setup()

    config.startup_sanity_check()

    from heat.engine import service as engine  # noqa

    srv = engine.EngineService(cfg.CONF.host, rpc_api.ENGINE_TOPIC)
    launcher = service.launch(cfg.CONF, srv,
                              workers=cfg.CONF.num_engine_workers)
    launcher.wait()
