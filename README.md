# Discord "You" Bot — Setup Guide

## 1. Install dependencies
```
pip install -r requirements.txt
```

## 2. Create your Discord bot
1. Go to https://discord.com/developers/applications
2. New Application → give it a name
3. Bot tab → Reset Token → copy it
4. Enable **Message Content Intent** (Bot → Privileged Gateway Intents)
5. OAuth2 → URL Generator → scopes: `bot`, `applications.commands`
   → permissions: `Send Messages`, `Read Message History`
6. Open the generated URL to invite it to your server

## 3. Get your AI API key
- **Claude:** https://console.anthropic.com → API Keys
- **OpenAI:** https://platform.openai.com → API Keys

## 4. Edit bot.py
Open `bot.py` and fill in the top section:
```python
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
AI_PROVIDER   = "claude"   # or "openai"
AI_API_KEY    = "YOUR_AI_API_KEY"
```

## 5. Customise your personality
Edit `SYSTEM_PROMPT` in `bot.py` to add more *you* to it:
- phrases you use a lot
- topics you always have opinions on
- things you'd never say
- your spelling/typing quirks

## 6. Run it
```
python bot.py
```

## How it works
| Trigger | Behaviour |
|---|---|
| Bot is @mentioned | Always replies |
| Random (20% chance) | Chimes in uninvited |
| `/ask <question>` | Slash command, always responds |

Change `RESPOND_CHANCE = 0.20` to tune how chatty it is (0.0 = never random, 1.0 = always).
