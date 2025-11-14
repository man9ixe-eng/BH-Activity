import os
import json
import datetime
import discord
from discord.ext import commands

# =====================
# CONFIG: ENV VARS ONLY
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Render
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # tracker text channel
CLAIM_CATEGORY_ID = int(os.getenv("CLAIM_CATEGORY_ID", "0"))  # category to rename

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

STATS_FILE = "stats.json"

# Default stats structure
DEFAULT_STATS = {
    "interviews": 0,
    "trainings": 0,
    "shift_minutes": 0,
    "tickets": 0,
    "reports": 0,

    "goal_interviews": 0,
    "goal_trainings": 0,
    "goal_shift_minutes": 0,
    "goal_tickets": 0,
    "goal_reports": 0,

    "message_id": None
}

stats = {}


# =====================
# STATS LOAD / SAVE
# =====================

def load_stats():
    global stats
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    # merge defaults in case we add new keys later
    merged = DEFAULT_STATS.copy()
    merged.update(data)
    stats = merged


def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


# =====================
# WEEK RANGE + CLAIM STATUS
# =====================

def current_week_range():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return f"{monday.strftime('%b %d')} — {sunday.strftime('%b %d')}"


def get_total_sessions():
    return stats["interviews"] + stats["trainings"]


def compute_claim_status():
    total = get_total_sessions()
    if total < 2:
        return "Requests"
    elif total < 5:
        return "Claim"
    else:
        return f"Claim {total}"


# =====================
# BUILD TRACKER MESSAGE
# =====================

def build_tracker_content():
    week = current_week_range()
    return (
        f"🎀 **Mani’s Weekly Tracker** — {week}\n\n"
        f"🗂 **Interviews:** {stats['interviews']} / {stats['goal_interviews']}\n"
        f"📘 **Trainings:** {stats['trainings']} / {stats['goal_trainings']}\n"
        f"⏱ **Shifts:** {stats['shift_minutes']} / {stats['goal_shift_minutes']} minutes\n"
        f"🎫 **Tickets:** {stats['tickets']} / {stats['goal_tickets']}\n"
        f"📄 **Reports:** {stats['reports']} / {stats['goal_reports']}\n\n"
        f"Claim Status: **{compute_claim_status()}**\n\n"
        f"Last Updated: <t:{int(datetime.datetime.utcnow().timestamp())}:t>"
    )


# =====================
# UPDATE TRACKER + CATEGORY
# =====================

async def update_claim_category(guild: discord.Guild | None):
    if not guild or CLAIM_CATEGORY_ID == 0:
        return

    category = guild.get_channel(CLAIM_CATEGORY_ID)
    if not isinstance(category, discord.CategoryChannel):
        return

    new_name = compute_claim_status()
    try:
        await category.edit(name=new_name)
    except Exception as e:
        print(f"Failed to rename category: {e}")


async def update_tracker(channel: discord.TextChannel):
    content = build_tracker_content()

    # create or edit tracker message
    msg_id = stats.get("message_id")
    try:
        if msg_id:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(content=content)
        else:
            msg = await channel.send(content)
            stats["message_id"] = msg.id
            save_stats()
    except discord.NotFound:
        msg = await channel.send(content)
        stats["message_id"] = msg.id
        save_stats()
    except Exception as e:
        print(f"Error updating tracker: {e}")

    # rename category based on sessions
    await update_claim_category(channel.guild)


# =====================
# CHECK: ONLY IN TRACKER CHANNEL
# =====================

def in_tracker_channel():
    async def predicate(ctx):
        return ctx.channel.id == CHANNEL_ID
    return commands.check(predicate)


# =====================
# COMMANDS
# =====================

@bot.command(name="resetweek")
@in_tracker_channel()
async def resetweek(ctx: commands.Context):
    """Reset weekly stats and set new goals interactively."""

    # reset current counts
    stats["interviews"] = 0
    stats["trainings"] = 0
    stats["shift_minutes"] = 0
    stats["tickets"] = 0
    stats["reports"] = 0

    def check(m: discord.Message):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.reply(
        "New week! 🎀 Let’s set your goals.\n\n"
        "How many **interviews** do you want to aim for?"
    )
    msg = await bot.wait_for("message", check=check)
    stats["goal_interviews"] = int(msg.content)

    await ctx.send("How many **trainings**?")
    msg = await bot.wait_for("message", check=check)
    stats["goal_trainings"] = int(msg.content)

    await ctx.send("How many **shift minutes**?")
    msg = await bot.wait_for("message", check=check)
    stats["goal_shift_minutes"] = int(msg.content)

    await ctx.send("How many **tickets**?")
    msg = await bot.wait_for("message", check=check)
    stats["goal_tickets"] = int(msg.content)

    await ctx.send("How many **reports**?")
    msg = await bot.wait_for("message", check=check)
    stats["goal_reports"] = int(msg.content)

    save_stats()
    await update_tracker(ctx.channel)
    await ctx.send("Goals set. We’re live for the week ✨")


@bot.command(name="i")
@in_tracker_channel()
async def add_interviews(ctx: commands.Context, amount: int):
    """!i 1 → add 1 interview"""
    stats["interviews"] += amount
    save_stats()
    await update_tracker(ctx.channel)


@bot.command(name="t")
@in_tracker_channel()
async def add_trainings(ctx: commands.Context, amount: int):
    """!t 1 → add 1 training"""
    stats["trainings"] += amount
    save_stats()
    await update_tracker(ctx.channel)


@bot.command(name="s")
@in_tracker_channel()
async def add_shift_minutes(ctx: commands.Context, amount: int):
    """!s 45 → add 45 shift minutes"""
    stats["shift_minutes"] += amount
    save_stats()
    await update_tracker(ctx.channel)


@bot.command(name="tk")
@in_tracker_channel()
async def add_tickets(ctx: commands.Context, amount: int):
    """!tk 1 → add 1 ticket answered"""
    stats["tickets"] += amount
    save_stats()
    await update_tracker(ctx.channel)


@bot.command(name="r")
@in_tracker_channel()
async def add_reports(ctx: commands.Context, amount: int):
    """!r 1 → add 1 report"""
    stats["reports"] += amount
    save_stats()
    await update_tracker(ctx.channel)


@bot.command(name="stats")
@in_tracker_channel()
async def show_stats(ctx: commands.Context):
    """Force-refresh tracker if needed."""
    await update_tracker(ctx.channel)


# =====================
# BOT READY
# =====================

@bot.event
async def on_ready():
    load_stats()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Tracker channel not found. Check CHANNEL_ID.")
        return
    await update_tracker(channel)


if __name__ == "__main__":
    load_stats()
    if not BOT_TOKEN:
        print("BOT_TOKEN env var is missing.")
    else:
        bot.run(BOT_TOKEN)
