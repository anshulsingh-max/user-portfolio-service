from rest_framework import serializers
from apps.portfolio.models import PortfolioRebalanceTransaction
from apps.portfolio.serializers.user_instruction import ReadUserInstructionSerializer


class PortfolioRebalanceTransactionSerializer(serializers.ModelSerializer):
    """
    Portfolio Rebalance Transaction Serializer
    """
    user_rebalance_json = serializers.JSONField()

    class Meta:
        model = PortfolioRebalanceTransaction
        fields = [
            "portfolio_rebalance",
            "allocation_quantity",
            "user_rebalance_json",
            "type",
            "current_state",
            "executed_list",
            "amount"
        ]


class PortfolioRebalanceTransactionUpdateSerializer(serializers.Serializer):
    """
    Portfolio Rebalance Transaction Serializer
    """
    class Meta:
        model = PortfolioRebalanceTransaction
        fields = [
            "portfolio_rebalance",
            "allocation_quantity",
            "user_rebalance_json",
            "type",
            "current_state",
            "executed_list",
            "amount"
        ]
    executed_list = serializers.ListField(child=serializers.CharField(), required=True)
    amount = serializers.FloatField(required=True)

    def update(self, instance, validated_data):
        instance.executed_list = validated_data.get('executed_list')
        instance.amount = validated_data.get("amount")
        instance.save()
        return instance


class ReadPortfolioRebalanceTransactionSerializer(serializers.ModelSerializer):
    """
    Portfolio Rebalance Transaction Serializer
    """
    user_rebalance_json = serializers.JSONField()
    user_instructions = serializers.SerializerMethodField()

    def get_user_instructions(self, obj):
        """
            User Instructions of the PortfolioRebalanceTransaction
            :return:
        """
        user_instructions = obj.user_instructions.all()
        user_instructions = ReadUserInstructionSerializer(user_instructions, many=True).data
        return user_instructions

    class Meta:
        model = PortfolioRebalanceTransaction
        fields = [
            "id",
            "portfolio_rebalance",
            "allocation_quantity",
            "user_rebalance_json",
            "type",
            "current_state",
            "executed_list",
            "amount",
            "user_instructions"
        ]
