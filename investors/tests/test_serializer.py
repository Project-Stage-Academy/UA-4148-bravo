from investors.serializers import InvestorSerializer
from tests.test_setup import BaseInvestorTestCase


class InvestorSerializerTests(BaseInvestorTestCase):

    def test_valid_investor_data(self):
        data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': '1000000.00',
        }
        serializer = InvestorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_company_name_should_fail(self):
        data = {
            'company_name': '   ',
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020
        }
        serializer = InvestorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)
