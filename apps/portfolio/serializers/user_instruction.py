import re

from rest_framework import serializers
from apps.portfolio.models import UserInstruction


class UserInstructionSerializer(serializers.ModelSerializer):
    """
    User Instruction Serializer
    """
    class Meta:
        model = UserInstruction
        fields = [
            "portfolio_rebalance_transaction",
            "order_tag",
            "symbol",
            "quantity",
            "filled_quantity",
            "side",
            "leverage",
            "status",
            "reason",
            "asm_consent",
            "asm_reason",
            "price"
        ]


class ReadUserInstructionSerializer(serializers.ModelSerializer):
    """
    User Instruction Serializer
    """
    reason = serializers.SerializerMethodField()

    def get_reason(self, obj):
        if not obj.reason:
            return obj.reason

        pattern = r"(?<=detail\s\=\s).*"
        detailed_reason = re.search(pattern=pattern, string=obj.reason)
        return detailed_reason.group() if detailed_reason else obj.reason

    class Meta:
        model = UserInstruction
        fields = [
            "id",
            "portfolio_rebalance_transaction",
            "trade_placement_id",
            "order_tag",
            "symbol",
            "quantity",
            "filled_quantity",
            "leverage",
            "side",
            "value",
            "status",
            "reason",
            "created",
            "modified",
            "asm_consent",
            "asm_reason",
            "retry_allowed",
            "price"
        ]
