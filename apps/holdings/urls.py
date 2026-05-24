"""
    URLs for brokers APIs
"""
from django.urls import path

from apps.holdings.apis.holdings import Holdings, UserHoldings, BrokerUsersHoldings, BulkHoldings
from apps.holdings.apis.transaction import Transaction

urlpatterns = [
    path("transaction", Transaction.as_view()),
    path("holdings/<int:user_portfolio_id>", Holdings.as_view()),
    path("holdings/_bulk", BulkHoldings.as_view()),
    path("user/holdings/<str:user_id>", UserHoldings.as_view()),
    path("<str:broker_name>/users", BrokerUsersHoldings.as_view())
]
