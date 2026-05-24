"""
    Signals of portfolio app
"""
import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.aggregates import Sum
from apps.holdings.services.transaction import update_or_create_holding
from apps.portfolio.constants import OrderStatus, RebalanceTransactionStates, Asset, Side, OrderCurrentStatus, \
    RebalanceTypes, ProductTypes
from apps.portfolio.models import PortfolioRebalanceTransaction, UserInstruction, Basket, Order, OrderInstruction, \
    UserPortfolioRebalance
from apps.portfolio.services.basket import update_basket_details
from apps.portfolio.services.order_instructions import create_instructions
from apps.portfolio.services.orders import get_next_order_state
from apps.portfolio.services.rebalance_transaction import refresh_portfolio_rebalance_transaction
from apps.portfolio.services.user_instruction import create_user_instruction, expected_rebalance_transaction_status
from apps.portfolio.services.user_portfolio_rebalance import update_rebalance_state
from apps.portfolio.tasks import phase_detail_callback
from apps.portfolio.serializers.portfolio_rebalance_transaction import PortfolioRebalanceTransactionUpdateSerializer
from multitenant.tenant_context import get_current_tenant
from bw_essentials.services.job_scheduler import JobScheduler
from apps.portfolio.models import UserPortfolio

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PortfolioRebalanceTransaction)
def rebalance_transaction_save(sender, instance, created, **kwargs):
    """
        Post save signal for Portfolio Rebalance Transaction
     """
    logger.info(f"Post Portfolio Rebalance Transaction save signal for {created=}")
    logger.info(f"Current status {instance.id} is {instance.current_state} and product type is {instance.portfolio_rebalance.user_portfolio.product_type}")

    if created:
        create_user_instruction(instance.id)

    # if (not created) and instance.portfolio_rebalance.user_portfolio.product_type == ProductTypes.EQUITY.value:
        # logger.info(f"In - Trigger Job-Scheduler for {instance.portfolio_rebalance.user_portfolio.id}")
        # data = {
        #     "user_portfolio_ids": [instance.portfolio_rebalance.user_portfolio.id]
        # }
        # tenant_id = instance.portfolio_rebalance.user_portfolio.broker
        # JobScheduler(settings.APP_NAME, tenant_id).process_user_profile(data)
        # logger.info(f"Out - Trigger Job-Scheduler for {instance.portfolio_rebalance.user_portfolio.id}")

    if instance.current_state in RebalanceTransactionStates.COMPLETION_STATES.value:
        update_rebalance_state(instance.portfolio_rebalance, instance.current_state, instance.type)


@receiver(post_save, sender=UserInstruction)
def user_instructions_save(sender, instance, created, **kwargs):
    """
        Post save signal for UserInstruction
     """
    logger.info("Post UserInstruction save signal")
    logger.info(f"Current status {instance.id} is {instance.status}")

    if created:
        tenant_id = get_current_tenant()
        order_tag = instance.id
        UserInstruction.objects.filter(id=instance.id).update(order_tag=order_tag)
        logger.info(f"Set order_tag for UserInstruction {instance.id} to {order_tag} (tenant={tenant_id})")
    if instance.status in OrderStatus.COMPLETED_STATES.value:
        logger.info(f"UserInstruction {instance.id} moved to completed state {instance.status};"
            f" evaluating PortfolioRebalanceTransaction {instance.portfolio_rebalance_transaction.id}")
        portfolio_rebalance_transaction = instance.portfolio_rebalance_transaction

        if instance.status == OrderStatus.FILLED.value:
            user_portfolio_id = portfolio_rebalance_transaction.portfolio_rebalance.user_portfolio
            value_in_cash = -1 * instance.value if instance.side == Side.BUY.value else instance.value
            symbol_quantity = instance.filled_quantity if instance.side == Side.BUY.value else -1 * instance.filled_quantity
            price = 0 if instance.side == Side.SELL.value else instance.value / instance.quantity
            logger.info(f"Processing FILLED instruction {instance.id}: side={instance.side}, symbol={instance.symbol}, "
                f"qty_filled={instance.filled_quantity}, value={instance.value}, price={price}, "
                f"user_portfolio={user_portfolio_id}")
            update_or_create_holding(user_portfolio_id, instance.symbol, symbol_quantity, price)
            update_or_create_holding(user_portfolio_id, Asset.CASH.value, value_in_cash, Asset.CASH_PRICE.value)
            refresh_portfolio_rebalance_transaction(portfolio_rebalance_transaction)

            if instance.side == Side.SELL.value:
                logger.info("Calling phase detail callback")
                tenant_id = get_current_tenant()
                phase_detail_callback.delay(portfolio_rebalance_transaction.portfolio_rebalance.id,
                                            tenant_id=tenant_id,
                                            rebalance_transaction_id=portfolio_rebalance_transaction.id)
        else:
            refresh_portfolio_rebalance_transaction(portfolio_rebalance_transaction)

    portfolio_rebalance_transaction = instance.portfolio_rebalance_transaction
    portfolio_rebalance_transaction.refresh_from_db()
    filled_orders = UserInstruction.objects.filter(
        portfolio_rebalance_transaction=portfolio_rebalance_transaction,
        status=OrderStatus.FILLED.value
    )
    executed_list = list(filled_orders.values_list('symbol', flat=True))
    amount = filled_orders.aggregate(total=Sum("value"))['total'] or 0
    updated_data = {
        "executed_list": executed_list,
        "amount": amount
    }
    logger.info(
        f"Aggregated filled orders for PRT {portfolio_rebalance_transaction.id}: executed_list={executed_list}, "
        f"amount={amount}"
    )
    serializer = PortfolioRebalanceTransactionUpdateSerializer(portfolio_rebalance_transaction, data=updated_data)
    logger.info(f"Initialized PortfolioRebalanceTransactionUpdateSerializer for transaction "
                 f"{portfolio_rebalance_transaction.id} with data={updated_data} and "
                 f"{portfolio_rebalance_transaction.current_state = }")
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        logger.info(f"Updated PortfolioRebalanceTransaction {portfolio_rebalance_transaction.id} "
                    f"with executed_list and amount")


@receiver(post_save, sender=Basket)
def user_basket_save(sender, instance, created, **kwargs):
    """
    Signal triggered when a Basket is saved. It either creates a new order or updates
    an existing one based on the current state of user_allocation.

    The signal checks if an order for a given `trading_symbol` already exists for the basket.
    If it exists, it updates the order; otherwise, it creates a new order.
    """

    logger.info("Post User Basket Save Signal")
    logger.info(f"Current status of Basket {instance.id} is {instance.current_state}")

    if instance.user_allocation:
        logger.info(f"Processing user allocation for Basket {instance.id}: {instance.user_allocation}")

        for order_data in instance.user_allocation:
            trading_symbol = order_data.get('symbol')
            stop_loss = order_data.get('stop_loss')
            leverage = order_data.get('leverage')
            states = OrderCurrentStatus.STATES_WITH_SL.value if stop_loss else OrderCurrentStatus.STATES_WITHOUT_SL.value
            try:
                order = Order.objects.get(basket=instance, trading_symbol=trading_symbol)
                order.stop_loss = stop_loss
                order.leverage = leverage
                order.states = states
                logger.info(f"Updating order for {trading_symbol} in Basket {instance.id}")
            except Order.DoesNotExist as exc:
                logger.info(f"Error while creating orders in user_basket_save.")
                order = Order(
                    basket=instance,
                    trading_symbol=trading_symbol,
                    stop_loss=stop_loss,
                    leverage=leverage,
                    states=states
                )
                logger.info(f"Creating new order for {trading_symbol} in Basket {instance.id}")

            order.save()
            logger.info(f"Order saved for {trading_symbol} in Basket {instance.id}")
    else:
        logger.info("User allocation does not exists to create instructions.")


@receiver(post_save, sender=Order)
def orders_save(sender, instance, created, **kwargs):
    """
    Signal triggered after an Order is saved. If the Order is newly created, it generates
    and saves OrderInstruction instances based on the user allocation of the associated Basket.

    Args:
        sender (Model): The model class that sent the signal (Order).
        instance (Order): The instance of the Order that was saved.
        created (bool): A boolean indicating if the Order was just created (True if created).
        **kwargs: Additional keyword arguments provided by the signal.

    Process:
        - Logs the order's current state.
        - If the order was created, it iterates over the `user_allocation` from the associated
          Basket.
        - For each allocation, a new OrderInstruction is created with details like `symbol`,
          `quantity`, and `side`, and a unique `order_tag` is generated.
        - The OrderInstruction is saved to the database.
    """

    logger.info("Post Orders Save Signal")
    logger.info(f"Current status of Order {instance.id} is {instance.current_status}")

    if created:
        create_instructions(instance)
    if instance.current_status in [OrderCurrentStatus.BUY.value,
                                   OrderCurrentStatus.SELL.value,
                                   OrderCurrentStatus.SKIP.value]:
        update_basket_details(instance)


@receiver(post_save, sender=OrderInstruction)
def order_instruction_save(sender, instance, created, **kwargs):
    """
    Signal triggered after an OrderInstruction is saved. It updates the related Order's
    amount and price (buy or sell), as well as the initial and end amounts based on the side of the instruction.
    """

    logger.info("Post Order Instructions Save Signal")
    logger.info(f"Current status of OrderInstruction {instance.id} is {instance.status}")

    order = Order.objects.get(id=instance.order.id)

    if created:
        logger.info(f"{created =}, updating order current state.")
        order.current_status = get_next_order_state(instance)
        order.save()

    if instance.status == OrderStatus.FILLED.value:
        setattr(order, f"{instance.side}_price", instance.order_price)

        initial_amount = OrderInstruction.objects.filter(
            order=order,
            side=Side.BUY.value,
            status=OrderStatus.FILLED.value
        ).aggregate(total=Sum('value')).get('total') or 0

        end_amount = OrderInstruction.objects.filter(
            order=order,
            side=Side.SELL.value,
            status=OrderStatus.FILLED.value
        ).aggregate(total=Sum('value')).get('total') or 0

        order.initial_amount = initial_amount
        order.end_amount = end_amount

        order.current_status = get_next_order_state(instance)
        order.save()

        logger.info(f"Order {order.id} updated with {instance.side}_price: {instance.order_price}, "
                    f"amount: initial_amount: {order.initial_amount}, end_amount: {order.end_amount}")


@receiver(post_save, sender=UserPortfolioRebalance)
def user_portfolio_rebalance_save(sender, instance, created, **kwargs):
    """
    Updates the rebalance_id of the corresponding Order instance when a new UserPortfolioRebalance instance of type
    RebalanceTypes.CASH_ALLOCATION is created.

    Args:
        sender (UserPortfolioRebalance): The model that sent the signal.
        instance (UserPortfolioRebalance): The instance that was saved.
        created (bool): Whether the instance was created or updated.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    logger.info("Post User Portfolio Rebalance Save Signal")

    if created and instance.type == RebalanceTypes.CASH_ALLOCATION.value:
        last_user_portfolio_rebalance = (
            UserPortfolioRebalance.objects.filter(user_portfolio=instance.user_portfolio).
            exclude(id=instance.id).order_by('-id').first())

        if last_user_portfolio_rebalance:
            UserPortfolioRebalance.objects.filter(id=instance.id).update(rebalance_id=last_user_portfolio_rebalance.rebalance_id)
            logger.info(f"Updated rebalance_id for Order {instance.id} to {last_user_portfolio_rebalance.rebalance_id}")
        else:
            logger.warning(f"No previous UserPortfolioRebalance found for user portfolio {instance.user_portfolio.id}")


@receiver(post_save, sender=UserPortfolio)
def user_portfolio_post_save(sender, instance, created, **kwargs):
    """
    Post save signal for UserPortfolio.
    Calls external API when a portfolio is created or updated.
    """
    logger.info(f"In post_save for UserPortfolio, {instance.product_type=}")
    try:
        if instance.product_type == ProductTypes.EQUITY.value:
            tenant_id = instance.broker
            data = {
                "user_portfolio_ids": [instance.id]
            }
            JobScheduler(settings.APP_NAME, tenant_id).process_user_profile(data)
    except Exception as e:
        logger.exception(f"Failed to call API for UserPortfolio {instance.id}: {e}")
