import json
import os
import time
import urllib.request
import boto3
from datetime import datetime, timezone

TABLE_NAME = os.environ.get("TABLE_NAME", "uptime-monitor-results")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
TARGET_URL = os.environ.get("TARGET_URL", "https://example.com")

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc).isoformat()
    status_code = None
    is_up = False
    error_message = None

    start = time.time()
    try:
        req = urllib.request.Request(TARGET_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.status
            is_up = 200 <= status_code < 400
    except Exception as e:
        error_message = str(e)
        is_up = False
    finally:
        response_time_ms = int((time.time() - start) * 1000)

    table.put_item(Item={
        "url": TARGET_URL,
        "timestamp": timestamp,
        "status_code": status_code if status_code else 0,
        "response_time_ms": response_time_ms,
        "is_up": is_up,
        "error_message": error_message or "",
    })

    if not is_up and SNS_TOPIC_ARN:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"ALERT: {TARGET_URL} is DOWN",
            Message=f"Health check failed at {timestamp}\nStatus: {status_code}\nError: {error_message}",
        )

    return {
        "statusCode": 200,
        "body": json.dumps({"url": TARGET_URL, "is_up": is_up, "status_code": status_code}),
    }
