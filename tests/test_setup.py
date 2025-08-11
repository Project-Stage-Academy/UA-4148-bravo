from mixins.startup_mixin import StartupMixin
from mixins.subscription_mixin import SubscriptionMixin
from mixins.user_mixin import UserMixin
from mixins.investor_mixin import InvestorMixin
from mixins.project_mixin import ProjectMixin
from startups.models import Startup
from investors.models import Investor
from tests.test_generic_case import BaseAPITestCase
from users.models import User


class BaseStartupTestCase(StartupMixin, UserMixin, BaseAPITestCase):
    model = Startup


class BaseInvestorTestCase(InvestorMixin, UserMixin, BaseAPITestCase):
    model = Investor


class BaseInvestmentTestCase(StartupMixin, UserMixin, InvestorMixin, ProjectMixin, SubscriptionMixin, BaseAPITestCase):
    model = Startup


class BaseProjectTestCase(StartupMixin, UserMixin, InvestorMixin, ProjectMixin, BaseAPITestCase):
    model = Startup


class BaseUserTestCase(UserMixin, BaseAPITestCase):
    model = User
    authenticate = False
