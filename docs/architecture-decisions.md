# Architecture Decisions

This document explains the reasoning behind key technical choices in this project.

## 1. Why serverless (Lambda) instead of a server on EC2?

The workload is a small, periodic check — it runs for a few seconds every 5 minutes and is idle the rest of the time. Running a dedicated EC2 instance would mean paying for 24/7 uptime for a task that needs a few seconds of compute. Lambda charges per invocation and per millisecond of execution, which fits this access pattern far better, and removes the need to patch or manage an OS.

## 2. Why EventBridge instead of a cron job on a server?

Since there's no server, there's no cron. EventBridge's scheduled rules provide the same "run this on a schedule" behavior without needing infrastructure to host the scheduler itself. It also decouples the trigger from the function — if a second target needs monitoring later, that's a second rule pointing at the same or a different Lambda, not a change to a crontab file.

## 3. Why DynamoDB instead of a relational database (e.g. PostgreSQL / RDS)?

The access pattern here is simple and predictable: write a new check result, and occasionally read recent results for a given URL. This doesn't need joins, transactions across tables, or complex queries — a strong signal for a NoSQL key-value store over a relational database.

DynamoDB also matches the serverless philosophy of the rest of the stack: no database server to provision, patch, or scale manually. On-demand capacity mode means cost is tied to actual usage instead of a pre-provisioned instance size.

**Table key design:** partition key `url`, sort key `timestamp`.
This groups all checks for the same URL together and keeps them sorted by time, so querying "recent history for this URL" is a direct, efficient lookup instead of a full table scan. If the project later monitors multiple URLs, this key structure scales naturally — each URL gets its own partition.

## 4. Why SNS for alerting instead of, e.g., calling an email API directly from Lambda?

SNS decouples "detecting a problem" from "deciding how to notify someone about it." The Lambda function only needs to know: publish a message to this topic. It doesn't need to know whether that becomes an email, an SMS, or (later) a Slack message — that's a subscription-level concern. Adding a new notification channel later means adding a subscription to the topic, not changing the Lambda code.

## 5. Why environment variables instead of hardcoded values?

`TABLE_NAME`, `SNS_TOPIC_ARN`, and `TARGET_URL` are all injected via Lambda environment variables rather than hardcoded in the function. This means the exact same code could be deployed as a second function monitoring a different URL, or pointed at a different table/topic, without touching a single line of code — configuration is separated from logic.

## 6. Known trade-off: IAM permissions

The current setup uses AWS managed policies (`AmazonDynamoDBFullAccess`, `AmazonSNSFullAccess`) attached to the Lambda execution role. This was a deliberate speed trade-off to get the end-to-end flow working first. The function only actually needs `dynamodb:PutItem` on one specific table and `sns:Publish` on one specific topic — scoping the IAM policy down to exactly that (least privilege) is tracked as a next step in the README.


