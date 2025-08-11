from mixins.investor_mixin import InvestorMixin
from mixins.project_mixin import ProjectMixin
from mixins.startup_mixin import StartupMixin
from mixins.subscription_mixin import SubscriptionMixin
from mixins.user_mixin import UserMixin
from tests.test_generic_case import BaseAPITestCase, DisableSignalMixinStartup, DisableSignalMixinUser, \
    DisableSignalMixinInvestor


class BaseStartupTestCase(DisableSignalMixinStartup, StartupMixin, UserMixin, BaseAPITestCase):
    pass

class BaseInvestorTestCase(DisableSignalMixinInvestor, InvestorMixin, UserMixin, BaseAPITestCase):
    pass

class BaseInvestmentTestCase(DisableSignalMixinStartup, StartupMixin, UserMixin, InvestorMixin, ProjectMixin, SubscriptionMixin, BaseAPITestCase):
    pass

class BaseProjectTestCase(DisableSignalMixinStartup, StartupMixin, UserMixin, InvestorMixin, ProjectMixin, BaseAPITestCase):
    pass

class BaseUserTestCase(DisableSignalMixinUser, UserMixin, BaseAPITestCase):
    authenticate = False
