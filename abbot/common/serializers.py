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
Utility methods for serializing responses
"""

import datetime

from lxml import etree
from oslo_log import log as logging
from oslo_serialization import jsonutils
import six

LOG = logging.getLogger(__name__)


class JSONResponseSerializer(object):

    def to_json(self, data):
        def sanitizer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return six.text_type(obj)

        response = jsonutils.dumps(data, default=sanitizer)
        LOG.debug("JSON response : %s" % response)
        return response

    def default(self, response, result):
        response.content_type = 'application/json'
        response.body = six.b(self.to_json(result))
