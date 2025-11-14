import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ─────────────────────────────────────────────
#   BOT SETUP
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─────────────────────────────────────────────
#   USER DATA
# ─────────────────────────────────────────────

data = {
    "interviews": 0,
    "trainings": 0,
    "shifts": 0,
    "reports": 0,

    "goal_interviews": 0,
    "goal_trainings": 0,
    "goal_shifts": 0,
    "goal_reports": 0
}

# Updates claim category name automatically
async def update_claim_category(ctx):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name="CLAIM")

    if category is None:
        return

    total_sessions = data["interviews"] + data["trainings"]

    if total_sessions <= 1:
        new_name = "Requests"
    elif 2 <= total_sessions < 5:
        new_name = "Claim"
    else:
        new_name = f"Claim {total_sessions}"

    try:
        await category.edit(name=new_name)
    except:
        pass

# ─────────────────────────────────────────────
#   COMMANDS
# ─────────────────────────────────────────────

@bot.command()
async def i(ctx, amount: int = 1):
    """Log interviews"""
    data["interviews"] += amount
    await update_claim_category(ctx)
    await ctx.send(f"Interview logged! Total: {data['interviews']}")

@bot.command()
async def t(ctx, amount: int = 1):
    """Log trainings"""
    data["trainings"] += amount
    await update_claim_category(ctx)
    await ctx.send(f"Training logged! Total: {data['trainings']}")

@bot.command()
async def s(ctx, amount: int = 1):
    """Log shifts"""
    data["shifts"] += amount
    await ctx.send(f"Shift logged! Total: {data['shifts']}")

@bot.command()
async def r(ctx, amount: int = 1):
    """Log reports"""
    data["reports"] += amount
    await ctx.send(f"Report logged! Total: {data['reports']}")

@bot.command()
async def resetweek(ctx):
    """Reset all stats and set new goals"""
    for k in data:
        data[k] = 0

    await ctx.send("Week reset! Please enter new goals:\n"
                   "**Format:** !goals [interviews] [trainings] [shifts] [reports]")

@bot.command()
async def goals(ctx, inter: int, train: int, shifts: int, reports: int):
    """Set weekly goals"""
    data["goal_interviews"] = inter
    data["goal_trainings"] = train
    data["goal_shifts"] = shifts
    data["goal_reports"] = reports

    await ctx.send("Goals updated!")

@bot.command()
async def progress(ctx):
    """Show promotion progress bar"""
    out = (
        f"**📊 Promotion Progress**\n\n"
        f"Interviews: {data['interviews']} / {data['goal_interviews']}\n"
        f"Trainings: {data['trainings']} / {data['goal_trainings']}\n"
        f"Shifts: {data['shifts']} / {data['goal_shifts']}\n"
        f"Reports: {data['reports']} / {data['goal_reports']}\n"
    )
    await ctx.send(out)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
