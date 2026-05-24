from rest_framework import serializers
from apps.alerts.constants import PortfolioThresholdTypes, Status, ThresholdSource, PortfolioSides


class UserPortfolioThresholdParamsValidator(serializers.Serializer):
    """
    Serializer for validating the parameters required to create or update a
    UserPortfolioThreshold.

    All fields are mandatory and directly map to the model definition.

    Attributes:
        portfolio_type (str): The type of portfolio entity (e.g., USER_PORTFOLIO, BASKET, STRATEGY).
        portfolio_id (str): The unique identifier of the portfolio entity.
        threshold_type (str): The type of threshold rule. Must be one of PortfolioThresholdTypes.
        target_pct (Decimal): The percentage-based threshold (max 9 digits, 6 decimals).
        target_value (Decimal): The absolute value-based threshold (max 18 digits, 2 decimals).
        status (str): The status of the threshold. Must be one of Status choices.
        source (str): The origin of the rule (User, Admin, Dealer). Must be one of ThresholdSource.
        source_id (str): The unique identifier of the user, admin, or dealer.
    """

    portfolio_type = serializers.CharField(required=True, max_length=50)
    portfolio_id = serializers.CharField(required=True, max_length=100)
    side = serializers.ChoiceField(required=True, choices=PortfolioSides.choices)
    threshold_type = serializers.ChoiceField(required=True, choices=PortfolioThresholdTypes.choices)
    target_pct = serializers.FloatField(required=False)
    target_value = serializers.FloatField(required=False)
    status = serializers.ChoiceField(required=True, choices=Status.choices)
    source = serializers.ChoiceField(required=True, choices=ThresholdSource.choices)
    source_id = serializers.CharField(required=True)


class UserPortfolioThresholdQueryParamsValidator(serializers.Serializer):
    """
    Validates the query parameters for fetching UserPortfolioThresholds.

    Provides a helper property `.filters` that returns only non-null query params
    suitable for direct use in Django ORM filter().
    """

    portfolio_type = serializers.CharField(required=True)
    portfolio_id = serializers.CharField(required=True)
    side = serializers.ChoiceField(choices=PortfolioSides.choices, required=False)
    threshold_type = serializers.ChoiceField(choices=PortfolioThresholdTypes.choices, required=False)
    status = serializers.ChoiceField(choices=Status.choices, required=False)
    source_id = serializers.CharField(required=False)

    @property
    def filters(self) -> dict:
        """
        Return only non-null validated query parameters as a dictionary
        suitable for Django ORM filtering.

        Example:
            validated_data = {
                'portfolio_type': 'user_portfolio',
                'portfolio_id': '7',
                'side': 'long',
                'threshold_type': None,
                'status': 'active'
                'source_id': None
            }
            self.filters -> {
                'portfolio_type': 'user_portfolio',
                'portfolio_id': '7',
                'side': 'long',
                'status': 'active'
            }
        """
        if not hasattr(self, "validated_data"):
            raise AttributeError("You must call `.is_valid()` before accessing `.filters`")
        return {k: v for k, v in self.validated_data.items() if v is not None}


class UserPortfolioThresholdUpdateSerializer(serializers.Serializer):
    """
    Serializer to validate update requests for UserPortfolioThreshold.

    Only target_pct, status, and source can be updated.
    """
    target_pct = serializers.FloatField(required=False)
    status = serializers.ChoiceField(
        choices=Status.choices, required=False
    )
    source = serializers.ChoiceField(
        choices=ThresholdSource.choices,
        required=False
    )
    source_id = serializers.CharField(
        required=False
    )


class UpdateUserPortfolioThresholdSerializer(serializers.Serializer):
    """
    Validates fields for updating a UserPortfolioThreshold.
    All fields are optional, allowing partial updates.

    Fields:
        target_pct (Decimal): New percentage threshold (optional).
        status (str): Threshold status (optional, active/inactive).
        source (str): Origin of the update (optional, user/admin/dealer).
        source_id (str): ID of the user, admin, or dealer (optional).
    """
    id = serializers.IntegerField(required=True)
    target_pct = serializers.FloatField(required=False)
    status = serializers.ChoiceField(
        choices=Status.choices,
        required=False
    )
    source = serializers.ChoiceField(
        choices=ThresholdSource.choices,
        required=False
    )
    source_id = serializers.CharField(
        required=False
    )
