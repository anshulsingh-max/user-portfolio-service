"""
    URLs for User Portfolio
"""
from django.urls import path

from apps.portfolio.apis.basket import Basket, BasketDetails, BasketById
from apps.portfolio.apis.order import RetryOrder, SkipOrder
from apps.portfolio.apis.order_instructions import OrderInstructions, UpdateOrderInstructions
from apps.portfolio.apis.portfolio import UserPortfolio, UserPortfolioById, UserPortfolioBySubscriptionId, \
    ResetUserPortfolioOfUser, UserPortfolioPositions, UserPortfolioSummary, UserPortfolioJTE
from apps.portfolio.apis.rebalance_transaction import RebalanceTransaction, GetRebalanceTransaction, \
    UpdatePortfolioTransaction
from apps.portfolio.apis.user_instruction import UserInstruction, TradeDetails
from apps.portfolio.apis.user_portfolio_rebalance import AddUserPortfolioRebalance, GetUserPortfolioRebalance, \
    UpdateDate, \
    GetRebalanceOrders, UpdateUserPortfolioRebalance, ManualCompleteRebalanceTransaction, \
    BulkUserPortfolioRebalance, CloseRebalance, ManualCompleteLatestRebalanceTransaction

urlpatterns = [
    path('portfoliojte',UserPortfolioJTE.as_view()),
    path('portfolio', UserPortfolio.as_view()),
    path('portfolio/<int:id>', UserPortfolioById.as_view()),
    path('user-portfolio/subscription/cancel/<str:subscription_id>', UserPortfolioBySubscriptionId.as_view()),
    path('user-portfolio/reset', ResetUserPortfolioOfUser.as_view()),
    path('user-portfolio/positions/', UserPortfolioPositions.as_view()),
    path('instruction/<int:id>', UserInstruction.as_view()),
    path('portfolio/rebalance', AddUserPortfolioRebalance.as_view()),
    path('portfolio/rebalance/<int:user_portfolio_id>', GetUserPortfolioRebalance.as_view()),
    path('portfolio/rebalances/_bulk', BulkUserPortfolioRebalance.as_view()),
    path('portfolio/rebalance/date/<int:user_portfolio_rebalance_id>', UpdateDate.as_view()),
    path('portfolio/rebalance/orders/', GetRebalanceOrders.as_view()),
    path('portfolio/rebalance/<int:user_portfolio_rebalance_id>/', UpdateUserPortfolioRebalance.as_view()),
    path('portfolio/rebalance/transaction', RebalanceTransaction.as_view()),
    path('portfolio/rebalance/transaction/<int:portfolio_rebalance_transaction_id>', GetRebalanceTransaction.as_view()),
    path('portfolio/rebalance/transaction/user-instruction', TradeDetails.as_view()),
    path('portfolio/rebalance/transactions/<int:portfolio_rebalance_transaction_id>', UpdatePortfolioTransaction.as_view()),
    path('portfolio/rebalance/transactions/complete/<int:portfolio_rebalance_transaction_id>',
         ManualCompleteRebalanceTransaction.as_view()),
    path('portfolio/rebalance/transactions/manual-complete/latest',
         ManualCompleteLatestRebalanceTransaction.as_view()),
    path('portfolio/rebalance/close/', CloseRebalance.as_view()),
    path('basket', Basket.as_view()),
    path('basket/<int:basket_id>', BasketById.as_view()),
    path('order/order-instruction', OrderInstructions.as_view()),
    path('order/retry/basket/<int:basket_id>', RetryOrder.as_view()),
    path('order/skip/basket/<int:basket_id>', SkipOrder.as_view()),
    path('order/details', BasketDetails.as_view()),
    path('order/instructions/', UpdateOrderInstructions.as_view()),
    path('user-portfolio/summary', UserPortfolioSummary.as_view()),
]
