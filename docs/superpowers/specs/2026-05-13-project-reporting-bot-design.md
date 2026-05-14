# Design: Project Reporting Scheduled Bot

## 1. Overview
A stateless serverless application designed to run on a weekly schedule. It aggregates metrics from AI platforms, GitHub, cloud infrastructure, etc., and publishes reports to Slack and Microsoft Teams for various projects.

### 1.1 Comprehensive Metrics Expansion
We track the following metric categories:
1.  **Harness / AI Metrics:** Tokens in/out consumed, number of times prompted, and cost of tokens across OpenAI, Anthropic, and Gemini.
2.  **Repository / Engineering Metrics:** PRs submitted, code line changes, bugs closed, and releases done via GitHub.
3.  **Infrastructure Metrics:** Costs of infrastructure like GCP or AWS, fetched dynamically based on available credentials.

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
*   `chat/fetchers/ai_usage.py`: Connects to OpenAI, Anthropic, and Gemini APIs.
*   `chat/fetchers/github_stats.py`: Connects to GitHub API for engineering metrics.
*   `chat/fetchers/cloud_costs.py`: Dynamically fetches AWS and GCP infrastructure costs.
*   `chat/publishers/slack_publisher.py`: Posts messages using the Slack Bot Token.
*   `chat/publishers/teams_publisher.py`: Posts JSON payloads to Teams Power Automate URLs.

## 4. Error Handling
*   **Isolated Failures:** If a specific fetcher fails, it logs the error but does not crash the script.
*   **Report Annotation:** The final report includes an "Errors/Warnings" section if data sources fail.
*   **Critical Failures:** Failure to load the Configuration Store or Secret Store halts execution.

## 5. Testing & Verification
To verify the bot functions correctly before enterprise deployment, we will build a local test harness.
*   **Local Overrides:** `config.py` will support a `TEST_MODE` flag. When enabled, it will bypass DynamoDB/Secrets Manager and load configuration/secrets directly from a local `.env` file.
*   **Sample Run:** To test, you will need to provide:
    *   A Slack Bot Token installed in your workspace.
    *   The Channel ID of your sample Slack channel.
    *   (Optional) A sample API key (e.g., GitHub Personal Access Token) to test real data fetching.
*   The function will execute locally, pulling sample data (or mocked data if keys are omitted) and publishing a real message to the sample Slack channel to verify formatting and connectivity.