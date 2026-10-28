# Birthday Bot

A simple Discord bot: members save their birthday, and the bot announces it in the server on the day.

## 1. Create the bot on Discord

1. Go to https://discord.com/developers/applications and click **New Application**.
2. Open the **Bot** tab, click **Reset Token**, and copy the token (keep it secret!).
3. Open **OAuth2 → URL Generator**:
   - Scopes: `bot` and `applications.commands`
   - Bot permissions: `Send Messages` and `View Channels`
4. Open the generated URL and invite the bot to your server.

## 2. Run it

Requires Python 3.9+.

```powershell
pip install -r requirements.txt
$env:DISCORD_TOKEN = "paste-your-token-here"
python bot.py
```

Instead of setting `$env:DISCORD_TOKEN`, you can create a file named `.env` next to `bot.py` containing:

```
DISCORD_TOKEN=your-token-here
```

`.env` is in `.gitignore`, so it never gets uploaded to GitHub.

The bot must stay running to make announcements (leave the window open, or host it somewhere like a Raspberry Pi or a cloud server).

## 3. Use it

| Command | What it does |
|---|---|
| `/setbirthday month day` | Save your birthday |
| `/removebirthday` | Remove your birthday |
| `/birthdays` | List everyone's birthdays in this server |
| `/setchannel #channel` | (Admins) choose where announcements go |

If no channel is set, announcements go to the server's system channel (where "welcome" messages appear).

Birthdays are checked at midnight, 6am, noon and 6pm (in the computer's time zone) and on startup, and each person is announced once per year. Data is saved to `birthdays.json`.
