# -*- coding: utf-8 -*-
from Acquisition import aq_base
from collective.flow.interfaces import IFlowSubmission
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.behavior import DexterityBehaviorAssignable
from venusianconfiguration import configure
from zope.component import adapter
from zope.component import ComponentLookupError
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@configure.adapter.factory()
@adapter(IFlowSubmission)
@implementer(IBehaviorAssignable)
class FlowSubmissionBehaviorAssignable(DexterityBehaviorAssignable):
    def enumerateBehaviors(self):
        for behavior in super(FlowSubmissionBehaviorAssignable,
                              self).enumerateBehaviors():
            yield behavior
        try:
            # We cannot acquire from parent FlowFolder, because behaviors
            # are resolved (this method called) without acquisition chain
            behaviors = aq_base(self.context.submission_behaviors) or []
        except AttributeError:
            behaviors = []
        for behavior in behaviors:
            try:
                yield getUtility(IBehavior, name=behavior)
            except ComponentLookupError:
                pass


@configure.utility.factory(
    name='collective.flow.submission.behaviors',
    provides=IVocabularyFactory,
)
class SubmissionBehaviorsVocabulary(object):
    def __call__(self, context=None):
        terms = []
        for reg in getUtilitiesFor(IBehavior):
            if reg[0].startswith('submission_'):
                terms.append(
                    SimpleTerm(
                        value=reg[0],
                        token=reg[0],
                        title=reg[1].title,
                    ),
                )
        return SimpleVocabulary(terms)
