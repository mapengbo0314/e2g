# Design: Project Reporting Scheduled Bot

## 1. Overview
A stateless serverless application designed to run on a weekly schedule. It aggregates metrics from AI platforms, GitHub, etc., and publishes reports to Slack and Microsoft Teams for various projects.

## 2. Architecture & Data Flow
**Infrastructure:**
*   **Compute:** A serverless function (e.g., AWS Lambda or Google Cloud Function).
*   **Trigger:** A cron job/scheduler (e.g., EventBridge or Cloud Scheduler) executing weekly.
*   **Configuration Store:** A NoSQL database (e.g., DynamoDB) storing mapping rules: Project ID -> [List of Repos, List of AI APIs, Slack Channel ID, Teams Power Automate URL].
*   **Secret Store:** A Secrets Manager (e.g., AWS Secrets Manager) strictly for API keys and Bot Tokens.

**Execution Flow:**
1.  **Initialize:** The function wakes up via the cron trigger.
2.  **Load Config:** Queries the Configuration Store for active projects and their destinations.
3.  **Load Secrets:** Retrieves necessary API keys from the Secret Store.
4.  **Fetch Data:** For each project, calls `fetchers` in parallel using the retrieved keys.
5.  **Aggregate:** Groups raw data by Project ID.
6.  **Publish:**
    *   **Slack:** Uses a single Slack App (Bot Token) to post to specific Channel IDs.
    *   **Teams:** Sends standardized JSON payloads to Power Automate HTTP trigger URLs.

## 3. Core Components
The code will be housed in a new `chat/` directory within the root repository.

*   `chat/main.py`: The entry point orchestrating the flow.
*   `chat/config.py`: Handles connections to NoSQL and Secret Manager.
*   `chat/fetchers/ai_usage.py`: Connects to OpenAI/Anthropic APIs.
*   `chat/fetchers/github_stats.py`: Connects to GitHub API.
*   `chat/publishers/slack_publisher.py`: Posts messages using the Slack Bot Token.
*   `chat/publishers/teams_publisher.py`: Posts JSON payloads to Teams Power Automate URLs.

## 4. Error Handling
*   **Isolated Failures:** If a specific fetcher fails, it logs the error but does not crash the script.
*   **Report Annotation:** The final report includes an "Errors/Warnings" section if data sources fail.
*   **Critical Failures:** Failure to load the Configuration Store or Secret Store halts execution.