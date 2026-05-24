"""
    User Portfolio serializer
"""
import logging

from django.db.models import Q
from rest_framework import serializers

from apps.holdings.models import Holding, Position
from apps.portfolio.constants import CashTransaction, RebalanceTypes, RebalanceTransactionStates, ProductTypes, Strategy, Side, USER_PORTFOLIO
from apps.portfolio.models.user_portfolio import UserPortfolio
from apps.alerts.models import UserPortfolioThreshold
from apps.alerts.constants import Status, PortfolioThresholdTypes
from apps.alerts.serializers.user_portfolio_threshold import UserPortfolioThresholdReadSerializer
from apps.portfolio.serializers.user_portfolio_rebalance import ReadUserPortfolioRebalanceSerializer

logger = logging.getLogger(__name__)



class UserPortfolioSerializer(serializers.ModelSerializer):
    """
    User Portfolio Serializer
    """
    class Meta:
        model = UserPortfolio
        fields = [
            "user_id",
            "name",
            "portfolio_id",
            "status",
            "subscription_id",
            "broker",
            "proxy",
            "proxy_id",
            "expected_investment",
            "product_type",
            "strategy",
            "mtf_invested_amount",
            "average_leverage",
            "investment_date",
        ]


class ReadUserPortfolioSerializer(serializers.ModelSerializer):
    """
    User Portfolio ReadSerializer
    """
    latest_rebalance = serializers.SerializerMethodField()
    sell_instructions = serializers.SerializerMethodField()
    user_portfolio_threshold = serializers.SerializerMethodField()

    def get_latest_rebalance(self, obj):
        """
            User Instructions of the PortfolioRebalanceTransaction
            :return:
        """
        from apps.portfolio.services.user_portfolio import create_latest_rebalance_dict

        # Use prefetched holdings to avoid additional queries
        investments_flag = any(
            holding.quantity > 0 and holding.symbol != "cash"
            for holding in obj.holdings.all()
        )

        # Use prefetched data and sort in Python to avoid query
        rebalance_list = sorted(obj.user_portfolio_rebalances.all(), key=lambda r: r.id, reverse=True)
        latest_rebalance_list = rebalance_list
        latest_rebalance_status_dict = {}

        # Only compute latest rebalance status for MTF portfolios with ONE_TIME strategy
        if (
            latest_rebalance_list and
            obj.product_type == ProductTypes.MTF.value and
            obj.strategy == Strategy.ONE_TIME.value
        ):
            latest_rebalance_list = latest_rebalance_list[0]
            latest_rebalance_status_dict = {
                "latest_user_portfolio_rebalance_type": latest_rebalance_list.type,
                "latest_user_portfolio_rebalance_transaction_type": latest_rebalance_list.transaction_type,
                "investments": investments_flag
            }
        latest_rebalance = {}
        latest_executed_rebalance_id = None

        for rebalance in rebalance_list:
            if rebalance.rebalance_id:
                latest_executed_rebalance_id = rebalance.rebalance_id
                break

        if not rebalance_list:
            return latest_rebalance

        # Use prefetched data and find max in Python to avoid query
        transactions = list(rebalance_list[0].portfolio_rebalance_transactions.all())
        latest_portfolio_rebalance_transaction = max(transactions, key=lambda t: t.id) if transactions else None
        if latest_portfolio_rebalance_transaction:
            latest_portfolio_rebalance_transaction_state = latest_portfolio_rebalance_transaction.current_state

            if latest_portfolio_rebalance_transaction_state not in [RebalanceTransactionStates.COMPLETED.value,
                                                                    RebalanceTransactionStates.MANUALLY_COMPLETED.value,
                                                                    RebalanceTransactionStates.SKIPPED.value]:
                latest_rebalance = create_latest_rebalance_dict(rebalance_list)
                latest_rebalance.update(latest_rebalance_status_dict)
                latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
                return latest_rebalance

        # Use prefetched data and filter/sort in Python to avoid query
        rebalance_list = sorted(
            [r for r in obj.user_portfolio_rebalances.all() if r.transaction_type != CashTransaction.WITHDRAW.value],
            key=lambda r: r.id,
            reverse=True
        )

        if rebalance_list:
            latest_rebalance = create_latest_rebalance_dict(rebalance_list)
            latest_rebalance.update(latest_rebalance_status_dict)
            latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
            return latest_rebalance
        latest_rebalance.update(latest_rebalance_status_dict)
        latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
        return latest_rebalance

    def get_sell_instructions(self, portfolio):
        """
        Retrieve SELL instructions for all withdraw-type rebalances of a given portfolio,
        enriched with a computed `rebalance_type`.

        This method is only applicable for portfolios with `product_type = MTF` and `strategy = ONE_TIME`. For all
        other product types, an empty list is returned.

        ### Logic:
        1. Validate that the portfolio is of MTF product type and ONE_TIME strategy.
        2. Filter all related `UserPortfolioRebalance` objects where `transaction_type = WITHDRAW`.
        3. For each withdraw rebalance:
           - Determine the effective `rebalance_type`:
             - If `rebalance.type = RECONCILIATION`, then rebalance_type = `"reconciliation"`.
             - If `rebalance.type = INITIAL` and `transaction_type = WITHDRAW`, then rebalance_type = `"squared_off"`.
             - Otherwise, fall back to the raw `rebalance.type`.
           - Collect all associated `UserInstruction` records from its `PortfolioRebalanceTransactions`.
           - Serialize each instruction and append the computed `rebalance_type`.
        4. Return a flattened list of all enriched user instruction dicts.

        ### Performance Considerations:
        - Uses `prefetch_related` to batch-load `portfolio_rebalance_transactions`
          and their nested `user_instructions`, avoiding N+1 query patterns.
        - Returns only serialized instruction data, optimized for large datasets
          (potentially thousands of instructions).

        Args:
            portfolio (UserPortfolio): The portfolio object for which to fetch sell instructions.

        Returns:
            List[dict]: A list of serialized user instructions with an added `rebalance_type` field.
        """
        # logger.info("Fetching sell instructions for portfolio: %s", portfolio.id)
        from apps.portfolio.serializers.user_instruction import ReadUserInstructionSerializer

        # Flow only for MTF product type with ONE_TIME strategy
        if not (
            portfolio.product_type == ProductTypes.MTF.value and
            portfolio.strategy == Strategy.ONE_TIME.value
        ):
            logger.info("Portfolio %s is not MTF or ONE_TIME strategy", portfolio.id)
            return []

        # Build a symbol to avg_buy_price mapping from holdings to avoid per-instruction queries
        holdings_map = {
            holding.symbol: holding.avg_buy_price
            for holding in portfolio.holdings.all()
        }

        # logger.info("Fetching sell instructions for portfolio: %s", portfolio.id)
        # Use prefetched data and filter in Python to avoid query
        withdraw_rebalances = [
            r for r in portfolio.user_portfolio_rebalances.all()
            if r.transaction_type == CashTransaction.WITHDRAW.value
        ]

        serialized_instructions = []

        for rebalance in withdraw_rebalances:
            # Compute rebalance_type based on rules
            # logger.info("Rebalance type: %s", rebalance.type)
            if rebalance.type == RebalanceTypes.RECONCILIATION.value:
                effective_rebalance_type = "reconciliation"
            elif (rebalance.type == RebalanceTypes.INITIAL.value and
                  rebalance.transaction_type == CashTransaction.WITHDRAW.value):
                effective_rebalance_type = "squared_off"
            else:
                effective_rebalance_type = rebalance.type

            # Iterate through rebalance transactions and their user instructions
            for transaction in rebalance.portfolio_rebalance_transactions.all():
                for instruction in transaction.user_instructions.all():
                    instruction_data = ReadUserInstructionSerializer(instance=instruction).data
                    instruction_data["rebalance_type"] = effective_rebalance_type
                    # attach average buy price from holdings if available
                    instruction_data["avg_buy_price"] = holdings_map.get(instruction.symbol)
                    serialized_instructions.append(instruction_data)
        # logger.info("Sell instructions fetched for portfolio: %s", portfolio.id)
        return serialized_instructions

    def get_user_portfolio_threshold(self, obj):
        """
        Return details of the related ACTIVE user portfolio threshold (Profit Target),
        with `target_pct` renamed to `profit_target_1`.
        """
        try:
            thresholds = self.context.get("thresholds")
            # Filter thresholds in Python to avoid extra query
            if thresholds:
                matching_thresholds = [
                    t for t in thresholds
                    if (t.portfolio_type == USER_PORTFOLIO and
                        t.portfolio_id == str(obj.id) and
                        t.status == Status.ACTIVE and
                        t.threshold_type == PortfolioThresholdTypes.PROFIT_TARGET)
                ]
            else:
                matching_thresholds = (
                    UserPortfolioThreshold.objects
                    .filter(
                        portfolio_type=USER_PORTFOLIO,
                        portfolio_id=str(obj.id),
                        status=Status.ACTIVE,
                        threshold_type=PortfolioThresholdTypes.PROFIT_TARGET,
                    )
                    .order_by('-effective_from', '-id')
                )


            if not matching_thresholds:
                return {}

            # Sort by effective_from (desc), then id (desc) to match order_by behavior
            threshold = max(matching_thresholds, key=lambda t: (t.effective_from, t.id))

            data = UserPortfolioThresholdReadSerializer(instance=threshold).data
            return data
        except Exception as exc:
            logger.info("Error fetching active user portfolio threshold for portfolio %s", obj.id)
            logger.exception(exc)
            return {}

    class Meta:
        model = UserPortfolio
        fields = [
            "id",
            "user_id",
            "name",
            "portfolio_id",
            "status",
            "subscription_id",
            "product_type",
            "strategy",
            "latest_rebalance",
            "sell_instructions",
            "created",
            "modified",
            "broker",
            "deactivated_reason",
            "proxy",
            "proxy_id",
            "created",
            "mtf_invested_amount",
            "average_leverage",
            "investment_date",
            "user_portfolio_threshold",
        ]



class ReadUserPortfolioSerializerJTE(serializers.ModelSerializer):
    """
    User Portfolio ReadSerializer
    """
    latest_rebalance = serializers.SerializerMethodField()
    sell_instructions = serializers.SerializerMethodField()
    user_portfolio_threshold = serializers.SerializerMethodField()
    holdings = serializers.SerializerMethodField()
    rebalances = serializers.SerializerMethodField()

    def get_latest_rebalance(self, obj):
        """
            User Instructions of the PortfolioRebalanceTransaction
            :return:
        """
        from apps.portfolio.services.user_portfolio import create_latest_rebalance_dict

        # Use prefetched holdings to avoid additional queries
        investments_flag = any(
            holding.quantity > 0 and holding.symbol != "cash"
            for holding in obj.holdings.all()
        )

        # Use prefetched data and sort in Python to avoid query
        rebalance_list = sorted(obj.user_portfolio_rebalances.all(), key=lambda r: r.id, reverse=True)
        latest_rebalance_list = rebalance_list
        latest_rebalance_status_dict = {}

        # Only compute latest rebalance status for MTF portfolios with ONE_TIME strategy
        if (
            latest_rebalance_list and
            obj.product_type == ProductTypes.MTF.value and
            obj.strategy == Strategy.ONE_TIME.value
        ):
            latest_rebalance_list = latest_rebalance_list[0]
            latest_rebalance_status_dict = {
                "latest_user_portfolio_rebalance_type": latest_rebalance_list.type,
                "latest_user_portfolio_rebalance_transaction_type": latest_rebalance_list.transaction_type,
                "investments": investments_flag
            }
        latest_rebalance = {}
        latest_executed_rebalance_id = None

        for rebalance in rebalance_list:
            if rebalance.rebalance_id:
                latest_executed_rebalance_id = rebalance.rebalance_id
                break

        if not rebalance_list:
            return latest_rebalance

        # Use prefetched data and find max in Python to avoid query
        transactions = list(rebalance_list[0].portfolio_rebalance_transactions.all())
        latest_portfolio_rebalance_transaction = max(transactions, key=lambda t: t.id) if transactions else None
        if latest_portfolio_rebalance_transaction:
            latest_portfolio_rebalance_transaction_state = latest_portfolio_rebalance_transaction.current_state

            if latest_portfolio_rebalance_transaction_state not in [RebalanceTransactionStates.COMPLETED.value,
                                                                    RebalanceTransactionStates.MANUALLY_COMPLETED.value,
                                                                    RebalanceTransactionStates.SKIPPED.value]:
                latest_rebalance = create_latest_rebalance_dict(rebalance_list)
                latest_rebalance.update(latest_rebalance_status_dict)
                latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
                return latest_rebalance

        # Use prefetched data and filter/sort in Python to avoid query
        rebalance_list = sorted(
            [r for r in obj.user_portfolio_rebalances.all() if r.transaction_type != CashTransaction.WITHDRAW.value],
            key=lambda r: r.id,
            reverse=True
        )

        if rebalance_list:
            latest_rebalance = create_latest_rebalance_dict(rebalance_list)
            latest_rebalance.update(latest_rebalance_status_dict)
            latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
            return latest_rebalance
        latest_rebalance.update(latest_rebalance_status_dict)
        latest_rebalance['latest_executed_rebalance_id'] = latest_executed_rebalance_id
        return latest_rebalance

    def get_sell_instructions(self, portfolio):
        """
        Retrieve SELL instructions for all withdraw-type rebalances of a given portfolio,
        enriched with a computed `rebalance_type`.

        This method is only applicable for portfolios with `product_type = MTF` and `strategy = ONE_TIME`. For all
        other product types, an empty list is returned.

        ### Logic:
        1. Validate that the portfolio is of MTF product type and ONE_TIME strategy.
        2. Filter all related `UserPortfolioRebalance` objects where `transaction_type = WITHDRAW`.
        3. For each withdraw rebalance:
           - Determine the effective `rebalance_type`:
             - If `rebalance.type = RECONCILIATION`, then rebalance_type = `"reconciliation"`.
             - If `rebalance.type = INITIAL` and `transaction_type = WITHDRAW`, then rebalance_type = `"squared_off"`.
             - Otherwise, fall back to the raw `rebalance.type`.
           - Collect all associated `UserInstruction` records from its `PortfolioRebalanceTransactions`.
           - Serialize each instruction and append the computed `rebalance_type`.
        4. Return a flattened list of all enriched user instruction dicts.

        ### Performance Considerations:
        - Uses `prefetch_related` to batch-load `portfolio_rebalance_transactions`
          and their nested `user_instructions`, avoiding N+1 query patterns.
        - Returns only serialized instruction data, optimized for large datasets
          (potentially thousands of instructions).

        Args:
            portfolio (UserPortfolio): The portfolio object for which to fetch sell instructions.

        Returns:
            List[dict]: A list of serialized user instructions with an added `rebalance_type` field.
        """
        # logger.info("Fetching sell instructions for portfolio: %s", portfolio.id)
        from apps.portfolio.serializers.user_instruction import ReadUserInstructionSerializer

        # Flow only for MTF product type with ONE_TIME strategy
        if not (
            portfolio.product_type == ProductTypes.MTF.value and
            portfolio.strategy == Strategy.ONE_TIME.value
        ):
            logger.info("Portfolio %s is not MTF or ONE_TIME strategy", portfolio.id)
            return []

        # Build a symbol to avg_buy_price mapping from holdings to avoid per-instruction queries
        holdings_map = {
            holding.symbol: holding.avg_buy_price
            for holding in portfolio.holdings.all()
        }

        # logger.info("Fetching sell instructions for portfolio: %s", portfolio.id)
        # Use prefetched data and filter in Python to avoid query
        withdraw_rebalances = [
            r for r in portfolio.user_portfolio_rebalances.all()
            if r.transaction_type == CashTransaction.WITHDRAW.value
        ]

        serialized_instructions = []

        for rebalance in withdraw_rebalances:
            # Compute rebalance_type based on rules
            # logger.info("Rebalance type: %s", rebalance.type)
            if rebalance.type == RebalanceTypes.RECONCILIATION.value:
                effective_rebalance_type = "reconciliation"
            elif (rebalance.type == RebalanceTypes.INITIAL.value and
                  rebalance.transaction_type == CashTransaction.WITHDRAW.value):
                effective_rebalance_type = "squared_off"
            else:
                effective_rebalance_type = rebalance.type

            # Iterate through rebalance transactions and their user instructions
            for transaction in rebalance.portfolio_rebalance_transactions.all():
                for instruction in transaction.user_instructions.all():
                    instruction_data = ReadUserInstructionSerializer(instance=instruction).data
                    instruction_data["rebalance_type"] = effective_rebalance_type
                    # attach average buy price from holdings if available
                    instruction_data["avg_buy_price"] = holdings_map.get(instruction.symbol)
                    serialized_instructions.append(instruction_data)
        # logger.info("Sell instructions fetched for portfolio: %s", portfolio.id)
        return serialized_instructions

    def get_user_portfolio_threshold(self, obj):
        """
        Return details of the related ACTIVE user portfolio threshold (Profit Target),
        with `target_pct` renamed to `profit_target_1`.
        """
        try:
            thresholds = self.context.get("thresholds")
            # Filter thresholds in Python to avoid extra query
            if 'thresholds' in self.context:
                matching_thresholds = [
                    t for t in thresholds
                    if (t.portfolio_type == USER_PORTFOLIO and
                        t.portfolio_id == str(obj.id) and
                        t.status == Status.ACTIVE and
                        t.threshold_type == PortfolioThresholdTypes.PROFIT_TARGET)
                ]
            else:
                matching_thresholds = (
                    UserPortfolioThreshold.objects
                    .filter(
                        portfolio_type=USER_PORTFOLIO,
                        portfolio_id=str(obj.id),
                        status=Status.ACTIVE,
                        threshold_type=PortfolioThresholdTypes.PROFIT_TARGET,
                    )
                    .order_by('-effective_from', '-id')
                )


            if not matching_thresholds:
                return {}

            # Sort by effective_from (desc), then id (desc) to match order_by behavior
            threshold = max(matching_thresholds, key=lambda t: (t.effective_from, t.id))

            data = UserPortfolioThresholdReadSerializer(instance=threshold).data
            return data
        except Exception as exc:
            logger.info("Error fetching active user portfolio threshold for portfolio %s", obj.id)
            logger.exception(exc)
            return {}

    def get_holdings(self, obj):
        res=[]
        for holding in obj.holdings.all():
            if holding.quantity > 0:
                res.append({
                    "id":holding.id,
                    "symbol":holding.symbol,
                    "quantity":holding.quantity,
                    "average_price":holding.avg_buy_price
                })
        return res

    def get_rebalances(self, obj):
        rebalance = obj.user_portfolio_rebalances.all()
        srebalances= ReadUserPortfolioRebalanceSerializer(instance=rebalance,many=True)
        return srebalances.data




    class Meta:
        model = UserPortfolio
        fields = [
            "id",
            "user_id",
            "name",
            "portfolio_id",
            "status",
            "subscription_id",
            "product_type",
            "strategy",
            "latest_rebalance",
            "sell_instructions",
            "created",
            "modified",
            "broker",
            "deactivated_reason",
            "proxy",
            "proxy_id",
            "created",
            "mtf_invested_amount",
            "average_leverage",
            "investment_date",
            "user_portfolio_threshold",
            "holdings",
            "rebalances",
        ]


class UserPortfolioPositionsSerializer(serializers.ModelSerializer):
    avg_buy_price = serializers.FloatField(source='buy_price')
    order_id = serializers.SerializerMethodField()
    model_id = serializers.CharField(source='basket.model_id', read_only=True)

    class Meta:
        model = Position
        fields = ['id', 'created', 'modified', 'symbol', 'quantity', 'avg_buy_price', 'basket', 'order_id',
                  'model_id']

    def get_order_id(self, obj):
        """
        Get the first order ID from the related basket's orders.
        """
        orders = obj.basket.user_basket.all()
        matching_order = orders.filter(trading_symbol=obj.symbol).first()
        return matching_order.id if matching_order else None