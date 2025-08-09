from rest_framework import serializers

from investors.models import Investor


class InvestorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investor model.
    Includes all fields defined in the abstract Company base class and Investor-specific fields.
    """
    class Meta:
        model = Investor
        fields = [
            'id',
            'user',
            'industry',
            'company_name',
            'location',
            'logo',
            'description',
            'website',
            'email',
            'founded_year',
            'team_size',
            'stage',
            'fund_size',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def validate_company_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
