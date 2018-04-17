# -*- coding: utf-8 -*-
from AccessControl.ZopeGuards import get_safe_globals
from AccessControl.ZopeGuards import guarded_getattr
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.memoize import forever
from RestrictedPython import compile_restricted_function

import logging


logger = logging.getLogger('collective.flow')


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
        if iface.providedBy(context):
            yield context

        func = getattr(context, 'im_self', None)
        if func is not None:
            context = aq_inner(func)
        else:
            # Don't use Acquisition.aq_inner() since portal_factory (and
            # probably other) things, depends on being able to wrap itself in a
            # fake context.
            context = aq_parent(context)
