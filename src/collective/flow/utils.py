# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.users import UnrestrictedUser
from AccessControl.ZopeGuards import get_safe_globals
from AccessControl.ZopeGuards import guarded_getattr
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.memoize import forever
from RestrictedPython import compile_restricted_function

import logging
import plone.api as api


logger = logging.getLogger('collective.flow')


def unrestricted(func):
    def wrapper(self, *args, **kwargs):
        old_security_manager = getSecurityManager()  # noqa: P001
        newSecurityManager(  # noqa: P001
            None,
            UnrestrictedUser('manager', '', ['Manager'], []),
        )
        try:
            return func(self, *args, **kwargs)
        finally:
            setSecurityManager(old_security_manager)  # noqa: P001

    return wrapper


def get_navigation_root_language(context):
    try:
        return (
            aq_inner(api.portal.get_navigation_root(context)).Language() or
            api.portal.get_default_language()
        )
    except AttributeError:
        return api.portal.get_default_language()


@forever.memoize
def prepare_restricted_function(p, body, name, filename, globalize=None):
    # we just do what they do in PythonScript...
    r = compile_restricted_function(p, body, name, filename, globalize)

    code = r[0]
    errors = r[1]
    warnings = tuple(r[2])

    if errors:
        logger.warning('\n'.join(errors))
        raise SyntaxError()
    elif warnings:
        logger.warning('\n'.join(warnings))

    g = get_safe_globals()
    g['_getattr_'] = guarded_getattr
    g['__debug__'] = __debug__
    g['__name__'] = 'script'
    loc = {}
    exec code in g, loc
    f = loc.values()[0]

    return f.func_code, g, f.func_defaults or ()


# noinspection PyUnresolvedReferences
def parents(context, iface=None):
    """Iterate through parents for the context (providing the given interface).

    Return generator to walk the acquisition chain of object, considering that
    it could be a function.

    Source: http://plone.org/documentation/manual/developer-manual/archetypes/
    appendix-practicals/b-org-creating-content-types-the-plone-2.5-way/
    writing-a-custom-pas-plug-in
    """
    context = aq_inner(context)

    while context is not None:
        if iface is None or iface.providedBy(context):
            yield context

        func = getattr(context, 'im_self', None)
        if func is not None:
            context = aq_inner(func)
        else:
            # Don't use Acquisition.aq_inner() since portal_factory (and
            # probably other) things, depends on being able to wrap itself in a
            # fake context.
            context = aq_parent(context)
