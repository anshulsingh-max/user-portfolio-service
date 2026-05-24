import os

MASTER_DATA_BASE_URL = os.environ.get('MASTER_DATA_BASE_URL', '')
NOTIFY_ON_TEAMS = os.environ.get('NOTIFY_ON_TEAMS', False) in [True, 'True', 'true']
NOTIFY_ON_CALLS = os.environ.get('NOTIFY_ON_CALLS', False) in [True, 'True', 'true']
ZENDUTY_URL = os.environ.get('ZENDUTY_URL', '')
API_TIMEOUT = os.environ.get('API_TIMEOUT', '')

TEAMS_WEBHOOK_URL = os.environ.get('TEAMS_WEBHOOK_URL', '')
JOB_SCHEDULER_BASE_URL = os.environ.get('JOB_SCHEDULER_BASE_URL', '')
JOB_SCHEDULER_API_KEY = os.environ.get('JOB_SCHEDULER_API_KEY', '')
PROMETHEUS_USER_APP_BASE_URL=os.environ.get('PROMETHEUS_USER_APP_BASE_URL', '')
PROMETHEUS_USER_APP_API_KEY = os.environ.get('PROMETHEUS_USER_APP_API_KEY', '')
AWS_REGION = os.environ.get('AWS_REGION', '')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_EVENT_BUS_ARN = os.environ.get('AWS_EVENT_BUS_ARN', '')