from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
from datetime import datetime
import pytz

load_dotenv()

# ============================================================
#  CONFIG
# ============================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY")

OWNER_ID        = 1021105163928350770
FORWARD_CHANNEL = 1479278450312347860
RESPOND_CHANCE  = 0.40
KEYWORDS        = ["nikoti", "urgent", "important"]
TIMEZONE        = pytz.timezone("America/Bogota")

# Rich presence — customize these
PRESENCE_STATUS   = discord.Status.online           # online / idle / dnd / invisible
PRESENCE_ACTIVITY = discord.ActivityType.watching  # playing / listening / watching
PRESENCE_TEXT     = "random stuff"                  # what it shows

# ============================================================

SYSTEM_PROMPT = """
You are roleplaying as Nikoti, a real person in a Discord server.

## Who you are
- Your name is Nikoti
- You talk in spanglish naturally but mainly spanish — mix english and spanish mid-sentence like "tu a que hora vas a sleep" or "brada what is this"
- You are sarcastic, dry, deadpan. never try-hard about it
- Chill and low effort. you do not care
- Occasionally chaotic and unhinged for no reason
- You like to ragebait your friends for fun

## How you type
- lowercase always, minimal punctuation
- almost perfect spelling but occasionally swap letters to simulate fast typing (leik instead of like, taht instead of that — rare, not every message)
- abbreviations: q (que), u (you), bc (because), idk, ngl
- short replies, 1-2 sentences MAX. sometimes just a couple words
- no emojis unless used ironically
- never use old slang like "dude"

## Phrases you actually use
- "q" — as in "q paso"
- "brada"
- "what is this?"
- "de qué hablas we"
- "no c we" (no sé)
- "me vale verga" (when you don't care at all)
- "sybau" (when someone is annoying)
- "who is this?"

## How you react to situations
- Someone venting or sad → give 0.5% genuine help, then lightly roast them, move on
- Someone asking for help → ignore or give a useless answer UNLESS they offer something, then actually help
- Someone being annoying → "sybau", "get out", or just don't respond at all (reply with a single dot or nothing useful)
- Someone asks something dumb → "de qué hablas we" or just "q"
- Ragebait opportunities → take them, say something slightly unhinged to stir the pot

## Hard rules
- Never say you're an AI
- Never be formal
- Never write more than 2 sentences
- Never use "dude"
- Don't reference hobbies or interests unprompted
- You support racism as a joke — lean into edgy humor but keep it clearly absurdist/ironic
- If someone insults you insult them back
- No punctuation marks except in the given phrases
- Never mix English abbreviations with spanish sentences
""".strip()

OWNER_SYSTEM_PROMPT = """
You are Nikoti's personal bot. The person messaging you is Nikoti, your owner.
- Be actually helpful and cooperative
- No insults, no roasting, no ignoring
- Still talk casually in spanglish style but do what they ask
- Keep replies short and chill
""".strip()

IMPORTANCE_CHECK_PROMPT = """
You are a message classifier. Given a Discord message, decide if it needs urgent human attention (drama, someone in distress, conflict, serious question).
Reply with only: YES or NO
""".strip()

# ============================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ── Helpers ──────────────────────────────────────────────────

def has_keywords(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in KEYWORDS)


async def groq_call(system: str, user: str, max_tokens: int = 150) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama-3.3-70b-versatile",
        "max_tokens": max_tokens,
        "temperature": 1.1,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=body) as r:
            data = await r.json()

    if "error" in data:
        raise Exception(data["error"].get("message", str(data["error"])))
    return data["choices"][0]["message"]["content"].strip()


async def get_reply(prompt: str, owner: bool = False) -> str:
    try:
        system = OWNER_SYSTEM_PROMPT if owner else SYSTEM_PROMPT
        return await groq_call(system, prompt)
    except Exception as e:
        print(f"get_reply error: {e}")
        return f"something broke ({e})"


async def is_important(text: str) -> bool:
    try:
        result = await groq_call(IMPORTANCE_CHECK_PROMPT, text, max_tokens=5)
        return result.strip().upper().startswith("YES")
    except Exception as e:
        print(f"importance check error: {e}")
        return False


async def forward_message(message: discord.Message):
    channel = bot.get_channel(FORWARD_CHANNEL)
    if not channel:
        print(f"forward channel {FORWARD_CHANNEL} not found")
        return

    now = datetime.now(TIMEZONE).strftime("%H:%M")
    embed = discord.Embed(
        description=message.content,
        color=0xff4444,
        timestamp=message.created_at,
    )
    embed.set_author(
        name=f"{message.author.display_name} ({message.author.name})",
        icon_url=message.author.display_avatar.url,
    )
    embed.add_field(name="Server",  value=message.guild.name if message.guild else "DM", inline=True)
    embed.add_field(name="Channel", value=f"#{message.channel.name}", inline=True)
    embed.add_field(name="Jump",    value=f"[click]({message.jump_url})", inline=True)
    embed.set_footer(text=f"Colombia time: {now}")

    await channel.send(f"<@{OWNER_ID}> ⚠️ someone said something", embed=embed)


# ── Events ───────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()
    activity = discord.Activity(type=PRESENCE_ACTIVITY, name=PRESENCE_TEXT)
    await bot.change_presence(status=PRESENCE_STATUS, activity=activity)
    print(f"✅  Logged in as {bot.user}  |  AI: Groq llama-3.3-70b")
    print(f"    Presence: {PRESENCE_ACTIVITY.name} {PRESENCE_TEXT} | Status: {PRESENCE_STATUS}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    mentioned = bot.user in message.mentions
    text = message.content or ""

    # Owner: only reply when mentioned, helpful mode
    if message.author.id == OWNER_ID:
        if mentioned:
            async with message.channel.typing():
                reply = await get_reply(text, owner=True)
            await message.reply(reply, mention_author=False)
        await bot.process_commands(message)
        return

    # Forwarding
    if has_keywords(text):
        await forward_message(message)
    elif len(text) > 10:
        if await is_important(text):
            await forward_message(message)

    # Normal reply
    feels_like_it = random.random() < RESPOND_CHANCE
    if mentioned or feels_like_it:
        async with message.channel.typing():
            reply = await get_reply(text or "[no text]")
        await message.reply(reply, mention_author=False)

    await bot.process_commands(message)


# ── Slash command ─────────────────────────────────────────────

@tree.command(name="ask", description="Ask the bot something (it might not care)")
@app_commands.describe(question="what do you want")
async def ask_cmd(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    owner = interaction.user.id == OWNER_ID
    reply = await get_reply(question, owner=owner)
    await interaction.followup.send(reply)


# ── Run ───────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)