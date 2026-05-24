"""
Module to store schemas for teams workflows.
"""
from django.utils import timezone


def get_error_schema(service_url, message, summary, error_trace=None, request_id=None):
    """
    Returns the schema for an error message to be sent to Microsoft Teams.

    Args:
        service_url (str): The URL of the service.
        message (str): The error message.
        summary (str): A summary of the error.
        error_trace (str, optional): The error trace details. Defaults to None.
        request_id (str, optional): The ID of the request. Defaults to None.

    Returns:
        dict: The schema for the error message.
    """
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                            "type": "Container",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "ERROR",
                                    "color": "attention",
                                    "weight": "bolder",
                                    "size": "large"
                                }
                            ],
                            "style": "attention"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Service: {service_url}",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{message}",
                            "weight": "bolder",
                            "wrap": True,
                            "isSubtle": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "Summary:",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{summary}",
                            "wrap": True,
                            "fontType": "monospace"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Error Trace:",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{error_trace}",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "Request ID:",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{request_id}",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "Timestamp:",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{str(timezone.now())}",
                            "wrap": True,
                            "isSubtle": True
                        }
                    ]
                }
            }
        ]
    }


def get_notification_schema(service_url, message):
    """
    Returns the schema for a message notification to be sent to Microsoft Teams.

    Args:
        service_url (str): The URL of the service.
        message (str): The log message.

    Returns:
        dict: The schema for the log message.
    """
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.0",
                    "body": [
                        {
                            "type": "Container",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "Notification",
                                    "color": "good",
                                    "weight": "bolder",
                                    "size": "large"
                                }
                            ],
                            "style": "good"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Service: {service_url}",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{message}",
                            "weight": "bolder",
                            "wrap": True,
                            "isSubtle": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "Timestamp:",
                            "weight": "bolder",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{str(timezone.now())}",
                            "wrap": True,
                            "isSubtle": True
                        }
                    ]
                }
            }
        ]
    }
