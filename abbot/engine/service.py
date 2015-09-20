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

LOG = logging.getLogger(__name__)

