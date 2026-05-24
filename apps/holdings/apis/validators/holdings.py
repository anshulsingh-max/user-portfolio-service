"""
    API Request Validators
"""
import copy

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotAcceptable

from apps.holdings.constants import TransactionSide, TransactionParticipants
from apps.portfolio.constants import BrokerEnum


class TransactionParamsValidator(serializers.Serializer):
    """
        Post Transaction Request Params Validator
    """
    def __init__(self, *args, **kwargs):
        data = kwargs['data']
        side_mapper_dict = TransactionSide.MAPPER.value[data['transaction_side']]
        data['source'] = side_mapper_dict[TransactionParticipants.SOURCE.value]
        data['target'] = side_mapper_dict[TransactionParticipants.TARGET.value]
        kwargs['data'] = data
        super().__init__(*args, **kwargs)

    user_portfolio = serializers.IntegerField(required=True, min_value=1)
    source = serializers.ChoiceField(choices=TransactionParticipants.CHOICES.value)
    target = serializers.ChoiceField(choices=TransactionParticipants.CHOICES.value)
    amount = serializers.FloatField(required=True, min_value=1)
    transaction_side = serializers.ChoiceField(source='type', required=False, choices=TransactionSide.CHOICES.value)

class BrokerUsersHoldingsQueryParamsValidator(serializers.Serializer):
    broker = serializers.ChoiceField(choices=BrokerEnum.CHOICES.value)