import os
import json
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TREE = bot.tree

PRESET_FILE = "presets.json"


# -----------------------------
# PRESET SYSTEM
# -----------------------------

def load_presets():
    if not os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "w") as f:
            json.dump({}, f)

    with open(PRESET_FILE, "r") as f:
        return json.load(f)


def save_presets(data):
    with open(PRESET_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# BOT READY
# -----------------------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    guild = discord.Object(id=GUILD_ID)

    TREE.copy_global_to(guild=guild)
    await TREE.sync(guild=guild)

    print("Slash commands synced.")


# -----------------------------
# MODERATION COMMANDS
# -----------------------------

@TREE.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ Banned {member.mention}")


@TREE.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ Kicked {member.mention}")


@TREE.command(name="timeout", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
    duration = discord.utils.utcnow() + timedelta(minutes=minutes)

    await member.edit(
        timed_out_until=duration,
        reason=reason
    )

    await interaction.response.send_message(
        f"⏳ Timed out {member.mention} for {minutes} minutes"
    )


@TREE.command(name="purge", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):

    await interaction.response.defer(ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(
        f"🧹 Deleted {len(deleted)} messages",
        ephemeral=True
    )


@TREE.command(name="lock", description="Lock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message("🔒 Channel locked")


@TREE.command(name="unlock", description="Unlock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = True

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message("🔓 Channel unlocked")


# -----------------------------
# UTILITY COMMANDS
# -----------------------------

@TREE.command(name="dm", description="Send a DM to a user")
@app_commands.checks.has_permissions(manage_messages=True)
async def dm(interaction: discord.Interaction, member: discord.Member, message: str):

    await member.send(message)

    await interaction.response.send_message(
        f"📨 Sent DM to {member.mention}",
        ephemeral=True
    )


@TREE.command(name="announce", description="Send an announcement")
@app_commands.checks.has_permissions(manage_messages=True)
async def announce(interaction: discord.Interaction, message: str):

    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue()
    )

    embed.set_footer(text=f"Sent by {interaction.user}")

    await interaction.channel.send(embed=embed)

    await interaction.response.send_message(
        "✅ Announcement sent",
        ephemeral=True
    )


@TREE.command(name="userinfo", description="Get user info")
async def userinfo(interaction: discord.Interaction, member: discord.Member):

    embed = discord.Embed(
        title="User Info",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Username",
        value=str(member),
        inline=False
    )

    embed.add_field(
        name="ID",
        value=member.id,
        inline=False
    )

    embed.add_field(
        name="Joined",
        value=member.joined_at.strftime("%d %b %Y"),
        inline=False
    )

    avatar = member.avatar or member.default_avatar
    embed.set_thumbnail(url=avatar.url)

    await interaction.response.send_message(embed=embed)


@TREE.command(name="serverinfo", description="Get server info")
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title="Server Info",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="Server Name",
        value=guild.name,
        inline=False
    )

    embed.add_field(
        name="Members",
        value=guild.member_count,
        inline=False
    )

    embed.add_field(
        name="Created",
        value=guild.created_at.strftime("%d %b %Y"),
        inline=False
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


# -----------------------------
# EVENT COMMAND
# -----------------------------

@TREE.command(name="createevent", description="Create a Discord scheduled event")
@app_commands.checks.has_permissions(manage_events=True)
async def createevent(
    interaction: discord.Interaction,
    name: str,
    description: str,
    date: str,
    time: str,
    channel: discord.VoiceChannel
):

    start_time = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )

    await interaction.guild.create_scheduled_event(
        name=name,
        description=description,
        start_time=start_time,
        entity_type=discord.EntityType.voice,
        channel=channel,
        privacy_level=discord.PrivacyLevel.guild_only
    )

    await interaction.response.send_message(
        f"📅 Event '{name}' created successfully"
    )


# -----------------------------
# PRESET COMMANDS
# -----------------------------

@TREE.command(name="addpreset", description="Add a preset message")
@app_commands.checks.has_permissions(manage_messages=True)
async def addpreset(interaction: discord.Interaction, name: str, message: str):

    presets = load_presets()

    presets[name] = message

    save_presets(presets)

    await interaction.response.send_message(
        f"✅ Preset '{name}' saved"
    )


@TREE.command(name="preset", description="Send a preset message")
async def preset(interaction: discord.Interaction, name: str):

    presets = load_presets()

    if name not in presets:
        await interaction.response.send_message(
            "❌ Preset not found",
            ephemeral=True
        )
        return

    await interaction.channel.send(presets[name])

    await interaction.response.send_message(
        "✅ Preset sent",
        ephemeral=True
    )


@TREE.command(name="listpresets", description="List all presets")
async def listpresets(interaction: discord.Interaction):

    presets = load_presets()

    if not presets:
        await interaction.response.send_message(
            "No presets saved"
        )
        return

    preset_names = "\n".join(presets.keys())

    await interaction.response.send_message(
        f"📋 Presets:\n{preset_names}"
    )


@TREE.command(name="removepreset", description="Remove a preset")
@app_commands.checks.has_permissions(manage_messages=True)
async def removepreset(interaction: discord.Interaction, name: str):

    presets = load_presets()

    if name not in presets:
        await interaction.response.send_message(
            "❌ Preset not found",
            ephemeral=True
        )
        return

    del presets[name]

    save_presets(presets)

    await interaction.response.send_message(
        f"🗑️ Removed preset '{name}'"
    )


bot.run(TOKEN)
