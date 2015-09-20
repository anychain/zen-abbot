# -*- coding: utf-8 -*-
###########################################
# Licensed Materials - Property of esse.io
# 
# (C) Copyright esse.io. 2015 All Rights Reserved
#
# Author: Bryan HUANG (bryan@esse.io)
#
###########################################


"""Policy Engine For Abbot"""


from oslo_config import cfg
from oslo_log import log as logging
from oslo_policy import policy
import six

from abbot.common import exception


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

DEFAULT_RULES = policy.Rules.from_dict({'default': '!'})
DEFAULT_RESOURCE_RULES = policy.Rules.from_dict({'default': '@'})


class Enforcer(object):
    """Responsible for loading and enforcing rules."""

    def __init__(self, scope='heat', exc=exception.NotAuthorized,
                 default_rule=DEFAULT_RULES['default'], policy_file=None):
        self.scope = scope
        self.exc = exc
        self.default_rule = default_rule
        self.enforcer = policy.Enforcer(
            CONF, default_rule=default_rule, policy_file=policy_file)

    def set_rules(self, rules, overwrite=True):
        """Create a new Rules object based on the provided dict of rules."""
        rules_obj = policy.Rules(rules, self.default_rule)
        self.enforcer.set_rules(rules_obj, overwrite)

    def load_rules(self, force_reload=False):
        """Set the rules found in the json file on disk."""
        self.enforcer.load_rules(force_reload)

    def _check(self, context, rule, target, exc, *args, **kwargs):
        """Verifies that the action is valid on the target in this context.

           :param context: Heat request context
           :param rule: String representing the action to be checked
           :param target: Dictionary representing the object of the action.
           :raises: self.exc (defaults to heat.common.exception.Forbidden)
           :returns: A non-False value if access is allowed.
        """
        do_raise = False if not exc else True
        credentials = context.to_dict()
        return self.enforcer.enforce(rule, target, credentials,
                                     do_raise, exc=exc, *args, **kwargs)

    def enforce(self, context, action, scope=None, target=None):
        """Verifies that the action is valid on the target in this context.

           :param context: Heat request context
           :param action: String representing the action to be checked
           :param target: Dictionary representing the object of the action.
           :raises: self.exc (defaults to heat.common.exception.Forbidden)
           :returns: A non-False value if access is allowed.
        """
        _action = '%s:%s' % (scope or self.scope, action)
        _target = target or {}
        return self._check(context, _action, _target, self.exc, action=action)

    def check_is_admin(self, context):
        """Whether or not roles contains 'admin' role according to policy.json

           :param context: Heat request context
           :returns: A non-False value if the user is admin according to policy
        """
        return self._check(context, 'context_is_admin', target={}, exc=None)


class ResourceEnforcer(Enforcer):
    def __init__(self, default_rule=DEFAULT_RESOURCE_RULES['default'],
                 **kwargs):
        super(ResourceEnforcer, self).__init__(
            default_rule=default_rule, **kwargs)

    def enforce(self, context, res_type, scope=None, target=None):
        # NOTE(pas-ha): try/except just to log the exception
        try:
            result = super(ResourceEnforcer, self).enforce(
                context, res_type,
                scope=scope or 'resource_types',
                target=target)
        except self.exc as ex:
            LOG.info(six.text_type(ex))
            raise
        if not result:
            if self.exc:
                raise self.exc(action=res_type)
            else:
                return result

    def enforce_job(self, job, scope=None, target=None):
        for res in job.resources.values():
            self.enforce(job.context, res.type(), scope=scope, target=target)
