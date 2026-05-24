import json
import logging
import pymsteams
import requests
from django.conf import settings

from apps.utils.notification_schemas import get_error_schema, get_notification_schema

logger = logging.getLogger(__name__)


class Notifications:
    """
    Notification module to send alerts and warnings.
    """

    def __init__(self, message="", title=None, summary=None, alert=False, trace=None, request_id=None):
        """
        Initialize the Notifications class.
        :param message: The notification message.
        :param title: The title of the notification.
        :param summary: The summary of the notification.
        :param alert: A boolean indicating if it's an alert (True) or a warning (False).
        """
        self.message = message
        self.title = title
        self.summary = summary
        self.alert = alert
        self.trace = trace
        self.request_id = request_id

    def __notify_teams(self, webhook_url=settings.MS_TEAMS_WEBHOOK_URL,
                       colour_code=settings.ALERT_CODE, alert=False):
        """
        Send alerts or warnings to the given Microsoft Teams channel.
        :param webhook_url: The URL for the Microsoft Teams channel.
        :param colour_code: The color code for the notification card.
        """
        try:
            if settings.NOTIFY_ON_TEAMS:
                logger.info('Sending notification to Teams channel.')
                if not self.alert:
                    colour_code = settings.WARNING_CODE
                # Create a Microsoft Teams message card
                teams_message = pymsteams.connectorcard(webhook_url)

                # Set the title and text of the message
                teams_message.title(f"Service: {self.title}")
                teams_message.text(self.message)
                teams_message.color(colour_code)

                # Add the error message as a section
                section = pymsteams.cardsection()
                if self.alert:
                    section.activityTitle("Error Trace")
                    section.activityText(self.summary)
                teams_message.addSection(section)
                teams_message.send()
        except Exception as exc:
            logger.info("Error while notifying error to teams")
            logger.exception(exc)

    def __notify_teams_workflow(self):
        """
        Sends a notification to Microsoft Teams using the Teams workflow schema.

        This method constructs a schema for the notification message based on whether
        an alert is required. If an alert is needed, an error schema is used; otherwise,
        a basic notification schema is used. The constructed schema is then sent to
        the specified Microsoft Teams webhook URL.

        Returns:
            None
        """
        logger.info("In __notify_teams_workflow")
        try:
            if settings.NOTIFY_ON_TEAMS:
                workflow_schema = get_notification_schema(self.title,
                                                          self.message)
                if self.alert:
                    workflow_schema = get_error_schema(self.title,
                                                       self.message,
                                                       self.summary,
                                                       self.trace,
                                                       self.request_id)

                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(settings.MS_TEAMS_WEBHOOK_URL,
                                         data=json.dumps(workflow_schema),
                                         headers=headers)
                logger.info(f"{response =}")
            else:
                logger.info(f"Notification for teams is {settings.NOTIFY_ON_TEAMS}. Message: {self.message}")
        except Exception as exc:
            logger.info("Error while notifying error to teams.")
            logger.exception(exc)

    def __notify_zenduty(self):
        """
        Send alerts or warnings to the Zenduty channel.
        """
        if settings.NOTIFY_ON_CALLS:
            # Creating Zenduty payload
            payload = {
                "alert_type": "critical",
                "message": self.message,
                "summary": self.summary
            }
            payload_json = json.dumps(payload)
            response = requests.post(settings.ZENDUTY_URL,
                                     data=payload_json,
                                     timeout=float(settings.API_TIMEOUT))
            logger.info(response)
            logger.info("Response from Zenduty Call API: An incident has been created")

    def notify_message(self, message=None, summary=None, alert=False):
        """
        Notify a message by sending it to the appropriate channels.
        """
        try:
            self.alert = alert
            if message:
                self.message = message
            if summary:
                self.summary = summary
            self.__notify_teams_workflow()
        except Exception as exc:
            logger.info("Error while notifying message to teams")
            logger.exception(exc)

    def notify_error(self, message=None, summary=None, alert=True, trace=None, request_id=None):
        """
        Notify an error by sending it to the appropriate channels.
        """
        self.alert = alert
        if summary:
            self.summary = summary
        if message:
            self.message = message
        if trace:
            self.trace = trace
        if request_id:
            self.request_id = request_id
        self.__notify_zenduty()
        self.__notify_teams_workflow()
