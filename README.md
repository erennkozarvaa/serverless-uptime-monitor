# Serverless Uptime Monitor

Got my AWS CCP, then realized certificates don't build anything — so here's a serverless uptime monitor made with EventBridge, Lambda, DynamoDB, and SNS.

## What it does

Periodically checks whether a target URL is up, records the result, and sends an email alert if the site goes down.

## Architecture

EventBridge (5 min schedule)
│
▼
Lambda (health_check.py)
│
├──► DynamoDB (store result: status, response time, timestamp)
│
└──► SNS (email alert, only if site is down)



**Flow:**
1. EventBridge triggers the Lambda function on a fixed schedule.
2. Lambda sends an HTTP request to the target URL and measures status code and response time.
3. Every check result is written to DynamoDB (url + timestamp as the key, so history is queryable per URL).
4. If the site is down, Lambda publishes an alert to an SNS topic, which emails the subscriber.

## AWS Services Used

| Service | Purpose |
|---|---|
| **Lambda** | Runs the health-check logic on a schedule, no server to manage |
| **EventBridge** | Triggers the Lambda function every 5 minutes |
| **DynamoDB** | Stores check history (on-demand capacity, no capacity planning needed) |
| **SNS** | Sends email alerts when the target is down |

## Why this design

- **Serverless-first**: no infrastructure to provision or patch; pay only for actual invocations.
- **DynamoDB key design**: partition key `url`, sort key `timestamp` — makes it cheap to query "recent history for this URL" without scanning the whole table.
- **Environment variables** (`TABLE_NAME`, `SNS_TOPIC_ARN`, `TARGET_URL`) instead of hardcoded values, so the same function can be reused for a different target without touching the code.
- **Least privilege (in progress)**: current IAM policy uses AWS managed full-access policies for speed during initial build; scoping this down to a minimal custom policy is a planned next step.

## Project Status

This is an active, iterative build. Current state: console-first setup, fully working end-to-end (EventBridge → Lambda → DynamoDB → SNS).

**Next steps:**
- [ ] Scope IAM permissions down to least privilege
- [ ] Add Infrastructure as Code (Terraform)
- [ ] Add CI/CD pipeline
- [ ] Add S3 + CloudFront status dashboard
- [ ] Document architectural decisions in `docs/architecture-decisions.md`

## Tech Stack

Python 3.12 · AWS Lambda · Amazon EventBridge · Amazon DynamoDB · Amazon SNS
