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
Abbot API Server. An Zen ReST API to Abbot.
"""

import eventlet
eventlet.monkey_patch(os=False)

import sys

from oslo_config import cfg
import oslo_i18n as i18n
from oslo_log import log as logging
from oslo_service import systemd
import six

from abbot.common import config
from abbot.common.i18n import _LI
from abbot.common import messaging
from abbot.common import wsgi
from abbot import version

i18n.enable_lazy()

LOG = logging.getLogger('abbot.api')


def main():
    try:
        logging.register_options(cfg.CONF)
        cfg.CONF(project='abbot', prog='abbot-api',
                 version=version.version_info.version_string())
        logging.setup(cfg.CONF, 'abbot-api')
        messaging.setup()

        app = config.load_paste_app()

        port = cfg.CONF.abbot_api.bind_port
        host = cfg.CONF.abbot_api.bind_host
        LOG.info(_LI('Starting abbot REST API on %(host)s:%(port)s'),
                 {'host': host, 'port': port})
        server = wsgi.Server('abbot-api', cfg.CONF.abbot_api)
        server.start(app, default_port=port)
        systemd.notify_once()
        server.wait()
    except RuntimeError as e:
        msg = six.text_type(e)
        sys.exit("ERROR: %s" % msg)
