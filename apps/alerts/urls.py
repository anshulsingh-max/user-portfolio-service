from django.urls import path

from apps.alerts.apis.holding_threshold import HoldingThresholdView
from apps.alerts.apis.user_portfolio_threshold import UserPortfolioThresholdView
from apps.alerts.views import LossLimitUpdatedNotification, StopLossConstituents

urlpatterns = [
    path("portfolio/thresholds", UserPortfolioThresholdView.as_view(),
         name="user-portfolio-threshold"),
    path("holding/thresholds",  HoldingThresholdView.as_view(),
         name="holding-threshold"),
    path("holding/stop_loss_hit_constituents", StopLossConstituents.as_view(),
         name="stop-loss-hit-constituents"),
    path(
        "send_loss_limit_updated_notification",
        LossLimitUpdatedNotification.as_view(),
        name="send-loss-limit-updated-notification",
    ),
]
