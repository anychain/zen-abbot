# -*- coding: utf-8 -*-
###########################################
# Licensed Materials - Property of esse.io
# 
# (C) Copyright esse.io. 2015 All Rights Reserved
#
# Author: Bryan HUANG (bryan@esse.io)
#
###########################################


import oslo_i18n as i18n

from cinder.openstack.common import gettextutils

DOMAIN = 'abbot'

_translators = i18n.TranslatorFactory(domain=DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary

# Translators for log levels.
#
# The abbreviated names are meant to reflect the usual use of a short
# name like '_'. The "L" is for "log" and the other letter comes from
# the level.
_LI = _translators.log_info
_LW = _translators.log_warning
_LE = _translators.log_error
_LC = _translators.log_critical


def enable_lazy(enable=True):
    return i18n.enable_lazy(enable)


def translate(value, user_locale=None):
    return i18n.translate(value, user_locale)


def get_available_languages():
    return i18n.get_available_languages(DOMAIN)


# Parts in oslo-incubator are still using gettextutils._(), _LI(), etc., from
# oslo-incubator. Until these parts are changed to use oslo.i18n, Cinder
# needs to do something to allow them to work. One option is to continue to
# initialize gettextutils, but with the way that Cinder has initialization
# spread out over mutltiple entry points, we'll monkey-patch
# gettextutils._(), _LI(), etc., to use our oslo.i18n versions.

# FIXME(dims): Remove the monkey-patching and update openstack-common.conf and
# do a sync with oslo-incubator to remove gettextutils once oslo-incubator
# isn't using oslo-incubator gettextutils any more.

gettextutils._ = _
gettextutils._LI = _LI
gettextutils._LW = _LW
gettextutils._LE = _LE
gettextutils._LC = _LC
