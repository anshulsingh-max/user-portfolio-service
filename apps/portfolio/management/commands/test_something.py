"""
    Command to populate trading symbols in broker data
"""
import logging
import csv

from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Max, F

from apps.portfolio.constants import OrderStatus
from apps.portfolio.models import OrderInstruction
from apps.portfolio.serializers.order_instructions import OrderInstructionSerializer
from apps.portfolio.services.order_instructions import get_cancelled_instructions
from apps.portfolio.services.user_portfolio import get_event_details
from apps.portfolio.tasks.portfolio_rebalance import phase_detail_callback

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
        Class of command
    """

    def handle(self, *args, **options):
        # pylint: disable=unspecified-encoding
        # latest_order_instructions = (
        #     OrderInstruction.objects
        #     .annotate(latest_created=Max('order__user_order__created'))
        #     .filter(created=F('latest_created'),
        #             status='cancel',
        #             order__basket__id=43)
        # )
        # for instruction in latest_order_instructions:
        #     instruction.pk = None
        #     instruction.trade_placement_id = None
        #     instruction.status = 'waiting'
        #     instruction.save()
        print(get_event_details(4391))
