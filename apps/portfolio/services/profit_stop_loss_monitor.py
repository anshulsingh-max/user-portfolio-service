"""
services/portfolio_stop_loss_monitor.py

This module defines the `ProfitStopLossMonitor` class, which is responsible for monitoring
investment baskets and orders. It checks profit targets for baskets, stop loss thresholds for
individual orders, and sends notifications when conditions are met.

Classes:
    - ProfitStopLossMonitor: Handles monitoring logic for profit targets and stop loss.

Functions:
    - get_live_price: Fetches live market price for a trading symbol.
    - send_notification: Sends a notification to the user.
    - check_profit_target: Evaluates profit targets for a basket.
    - check_stop_loss: Evaluates stop loss for an order.
    - _notify_and_update_basket: Sends a notification and updates the basket status when a profit target is hit.
    - _notify_and_update_order: Sends a notification and updates the order status when a stop loss is hit.
    - run_monitor: Main function to monitor all baskets in the "MONITORING" state.

Dependencies:
    - Django ORM for querying and updating baskets and orders.
    - `apps.utils.prices.get_live_price_nse` for fetching live prices.
    - Django settings for configuration like notification delays.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from apps.portfolio.constants import BasketStates, NotificationEventsMTF, ProductTypes
from apps.portfolio.models import Basket, Order

from apps.portfolio.services.user_instruction import user_portfolio_business_event_callback
from apps.utils.prices import get_live_price_nse

logger = logging.getLogger(__name__)


class ProfitStopLossMonitor:
    """
    The `ProfitStopLossMonitor` class handles monitoring of profit targets for baskets
    and stop loss conditions for individual orders. It also sends notifications to
    users when conditions are met.

    Attributes:
        notification_gap (timedelta): Minimum time gap between consecutive notifications.
    """

    def __init__(self):
        logger.info("Initializing ProfitStopLossMonitor.")
        self.notification_gap = timedelta(hours=settings.MONITORING_NOTIFICATION_DELAY)

    def get_live_price(self, symbol):
        """
        Fetches the live price for a given trading symbol.

        Args:
            symbol (str): The trading symbol to fetch the price for.

        Returns:
            float: The current price of the trading symbol, or None if not available.
        """
        logger.info(f"Fetching live price for symbol: {symbol}.")
        price_dict = get_live_price_nse(symbol)
        if 'price' in price_dict:
            logger.info(f"Live price for {symbol}: {price_dict['price']}.")
        else:
            logger.error(f"Failed to fetch live price for {symbol}.")
        return price_dict.get('price')

    def send_notification(self, basket, event_name):
        """
        Sends a notification to a user.

        Args:
            basket (basket instance): user basket instance.
            event_name (str): The name of the event to send notification.
        """
        logger.info(f"Sending notification to User {basket.user_id}: {event_name}.")
        event_details = {
            "event_name": event_name,
            "username": basket.user_id,
            "platform": ProductTypes.MTF.value,
            "basket_id": basket.id,
            "model_id": basket.model_id

        }
        return user_portfolio_business_event_callback(event_details)

    def check_profit_target(self, basket_id):
        """
        Checks if the basket has met any defined profit targets. Sends notifications
        and updates the basket status when targets are hit.

        Args:
            basket_id (Basket): The basket id to evaluate.
        """
        logger.info(f"Checking profit targets for Basket {basket_id}.")
        basket = Basket.objects.get(id=basket_id)
        total_invested = basket.amount
        if not total_invested:
            logger.error(f"Basket {basket.id} has no invested amount.")
            return

        current_value = 0
        for order in basket.user_basket.all():
            if not order.buy_price:
                continue
            current_value += order.initial_amount * (self.get_live_price(order.trading_symbol) / order.buy_price)


        logger.info(f"Basket {basket.id} - Total Invested: {total_invested}, Current Value: {current_value}.")

        if basket.profit_target_2_value and current_value >= basket.profit_target_2_value:
            logger.info(
                f"Basket {basket.id} - Current value: {current_value} meets or exceeds Profit Target 2 value: {basket.profit_target_2_value}.")

            if not basket.pt2_hit:
                logger.info(f"Profit Target 2 not previously hit for Basket {basket.id}. Proceeding to update.")
                basket.pt2_hit = True
                basket.pt2_hit_time = timezone.now()
                basket.pt1_hit = True
                basket.pt1_hit_time = timezone.now()
                basket.save()
                self._notify_and_update_basket(basket,
                                               2,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_2_MTF.value)
            if basket.pt2_hit and not basket.last_notification_sent:
                self._notify_and_update_basket(basket,
                                               2,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_2_MTF.value)

            elif (timezone.now() - basket.last_notification_sent).total_seconds() > self.notification_gap.total_seconds():
                logger.info(f"Basket {basket.id} - Notification gap exceeded. Sending notification again.")
                self._notify_and_update_basket(basket,
                                               2,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_2_MTF.value)
            else:
                logger.info(f"Profit Target 2 already hit for Basket {basket.id}. No further action taken.")
                return

        elif basket.profit_target_1_value and current_value >= basket.profit_target_1_value:
            logger.info(
                f"Basket {basket.id} - Current value: {current_value} meets or exceeds Profit Target 1 value: {basket.profit_target_1_value}.")

            if not basket.pt1_hit:
                logger.info(f"Profit Target 1 not previously hit for Basket {basket.id}. Proceeding to update.")
                basket.pt1_hit = True
                basket.pt1_hit_time = timezone.now()
                basket.save()
                self._notify_and_update_basket(basket,
                                               1,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_1_MTF.value)
            if basket.pt1_hit and not basket.last_notification_sent:
                logger.info(
                    f"Basket {basket.id} - Profit Target 1 hit but notification not sent. Sending the notification again.")
                self._notify_and_update_basket(basket,
                                               1,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_1_MTF.value)

            elif (timezone.now() - basket.last_notification_sent).total_seconds() > self.notification_gap.total_seconds():
                logger.info(f"Basket {basket.id} - Notification gap exceeded. Sending notification again.")
                self._notify_and_update_basket(basket,
                                               1,
                                               event_name=NotificationEventsMTF.PROFIT_TARGET_HIT_1_MTF.value)
            else:
                logger.info(f"Profit Target 1 already hit for Basket {basket.id}. No further action taken.")
                return

        else:
            logger.info(
                f"No profit target hit for Basket {basket.id}. "
                f"Current value: {current_value}, "
                f"Profit Target 1: {basket.profit_target_1_value}, "
                f"Profit Target 2: {basket.profit_target_2_value}."
            )

    def _notify_and_update_basket(self, basket, target_hit, event_name):
        """
        Sends a notification and updates the basket's state for a profit target hit.

        Args:
            basket (Basket): The basket being monitored.
            target_hit (int): The profit target level hit (1 or 2).
            event_name (str): The name of the event to send notification.
        """
        logger.info(f"Preparing to send notification for Basket {basket.id}, Target {target_hit}, {event_name}.")

        if self.send_notification(basket, event_name):
            logger.info(f"Notification sent for Basket {basket.id}: {event_name}.")
            basket.last_notification_sent = timezone.now()
            basket.save()

    def check_stop_loss(self, order_id):
        """
        Checks if an order's current price has reached the stop loss threshold.
        Sends notifications and updates the order status if the stop loss is hit.

        Args:
            order_id: The order id to evaluate.
        """
        logger.info(f"Checking stop loss for Order {order_id}.")
        order = Order.objects.get(id=order_id)

        if order.stop_loss and order.buy_price:
            current_price = self.get_live_price(order.trading_symbol)
            stop_loss_price = order.buy_price * (1 - order.stop_loss / 100)

            logger.info(f"Order {order.id} - Current Price: {current_price}, Stop Loss Price: {stop_loss_price}.")

            if current_price <= stop_loss_price:
                logger.info(
                    f"Order {order.id} - Current Price: {current_price} has reached or fallen below Stop Loss Price: {stop_loss_price}.")

                if not order.stop_loss_hit:
                    logger.info(f"Order {order.id} - Stop Loss not previously hit. Proceeding to update and notify.")

                    order.stop_loss_hit = True
                    order.stop_loss_hit_time = timezone.now()
                    order.save()
                    self._notify_and_update_order(order, NotificationEventsMTF.STOP_LOSS_HIT_MTF.value)

                elif order.stop_loss_hit and not order.last_notification_sent:
                    logger.info(
                        f"Order {order.id} - Stop Loss hit but notification not sent. Sending the notification again.")
                    self._notify_and_update_order(order, NotificationEventsMTF.STOP_LOSS_HIT_MTF.value)

                elif (
                        timezone.now() - order.last_notification_sent).total_seconds() > self.notification_gap.total_seconds():
                    self._notify_and_update_order(order, NotificationEventsMTF.STOP_LOSS_HIT_MTF.value)

                elif (timezone.now() - order.last_notification_sent).total_seconds() > self.notification_gap.total_seconds():
                    logger.info(f"Order {order.id} - Notification gap exceeded. Sending notification again.")
                    self._notify_and_update_order(order, NotificationEventsMTF.STOP_LOSS_HIT_MTF.value)

                else:
                    logger.info(
                        f"Order {order.id} - Stop Loss already hit and notification gap not exceeded. No action taken.")
                    return

            else:
                logger.info(
                    f"Order {order.id} - Stop Loss not hit. "
                    f"Current Price: {current_price} is above Stop Loss Price: {stop_loss_price}."
                )
        else:
            logger.info(f"Order {order.id} does not have a stop loss configured.")

    def _notify_and_update_order(self, order, event_name):
        """
        Sends a notification and updates the order status for a stop loss hit.

        Args:
            order: The order instance to update.
            event_name (str): The name of the event to send notification.
        """
        logger.info(f"Updating Order {order.id} for Stop Loss: {event_name}.")

        if self.send_notification(order.basket, event_name):
            order.last_notification_sent = timezone.now()
            order.save()

    def run_monitor(self):
        """
        Main function to monitor all baskets in the "MONITORING" state.
        Checks profit targets and stop loss for each basket and its associated orders.
        """
        logger.info("Starting monitoring for baskets in MONITORING state.")
        for basket in Basket.objects.filter(current_state=BasketStates.MONITORING.value):
            logger.info(f"Monitoring Basket {basket.id}.")
            self.check_profit_target(basket)
            for order in basket.user_basket.all():
                logger.info(f"Monitoring Order {order.id} in Basket {basket.id}.")
                self.check_stop_loss(order)
