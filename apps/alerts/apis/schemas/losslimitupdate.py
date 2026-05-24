from drf_yasg import openapi

loss_limit_updated_notification_request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_portfolio_id"],
            properties={
                "user_portfolio_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="User portfolio ID to notify",
                ),
                "loss_limit": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Optional loss limit override",
                ),
            },
        )

loss_limit_updated_notification_response_body={
            202: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        }

stop_loss_constituents_request_body=[
            openapi.Parameter(
                'user_portfolio_id',
                openapi.IN_QUERY,
                description='User portfolio ID to check for stop loss alerts',
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ]

stop_loss_constituents_response_body={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'alerts': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'symbol': openapi.Schema(type=openapi.TYPE_STRING),
                                'target_pct': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'avg_buy_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'stop_loss_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'live_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        ),
                        description='List of holdings with stop loss hit'
                    )
                }
            )
        }