# chat/README.md

# Project Reporting Bot

This bot aggregates project statistics (GitHub, OpenAI, Anthropic, Gemini) and publishes reports to messaging platforms like Slack and Microsoft Teams.

## Configuration

The bot uses environment variables for configuration. You can run it with a single project via flat environment variables, or support multiple projects by providing a JSON string.

### Sample `.env`

```env
# Single Project Configuration
PROJECT_ID=my-project
REPO=owner/repo
SLACK_CHANNEL_ID=C12345678
# TEAMS_URL=https://...

# API Keys
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# Multi-project Configuration (Optional - overrides single project config if set)
# PROJECTS_JSON={"my-project": {"slack_channel_id": "C12345678", "repo": "owner/repo"}}
```

## Setup Instructions

### Slack Setup

Follow these step-by-step instructions to configure the bot for Slack:

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**.
2. Under **OAuth & Permissions**, scroll down to **Scopes** and add the `chat:write` scope under **Bot Token Scopes**.
3. Scroll up to **OAuth Tokens for Your Workspace** and click **Install to Workspace**.
4. Copy the generated **Bot User OAuth Token** (it starts with `xoxb-`). Use this as the `SLACK_BOT_TOKEN` in your `.env` file.
5. In your Slack workspace, go to the channel where you want the bot to post.
6. Click the channel name at the top. At the bottom of the **About** tab, locate the **Channel ID** (e.g., `C12345678`). Use this as the `SLACK_CHANNEL_ID`.
7. Invite the bot to the channel by typing `/invite @YourBotName` in the message box.

## Running the Bot

Run the bot as a standard Python script:

```bash
python -m chat.main
```
