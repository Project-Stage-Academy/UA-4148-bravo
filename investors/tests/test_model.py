from django.core.exceptions import ValidationError

from investors.models import Investor
from tests.test_setup import BaseInvestorTestCase


class InvestorModelCleanTests(BaseInvestorTestCase):

    def test_valid_clean_should_pass(self):
        investor = Investor(
            user=self.user,
            company_name='InvestX',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=1000000,
            stage='mvp'
        )
        try:
            investor.clean()
        except ValidationError:
            self.fail("Investor.clean() raised ValidationError unexpectedly")
