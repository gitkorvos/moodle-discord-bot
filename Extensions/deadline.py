import discord
from discord import app_commands
from discord.ext import commands

from Utils import API

from datetime import datetime, timedelta
import re

def mask_string(s):
    return '*' * len(s)

class MyCog(commands.Cog):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    
  @app_commands.command(name="register")
  async def command_register(self, interaction: discord.Interaction, username: str = "", password: str = "") -> None:
    """ Register your Moodle Account Details """
    
    register_embed = discord.Embed(title="Register Moodle Account", description="You have registered your moodle account details sucessfully.")
    register_embed.description = register_embed.description + f"\n**` Username: `** {username}\n**` Password: `** {mask_string}"
    register_embed.description = register_embed.description + "\n\nNote: This does currently check if your login is correct, please ensure you use the correct details before attempting other commands."

    await interaction.response.send_message(embed=register_embed, ephemeral=True)

    API.register_account(interaction.user.id, username, password)
    await interaction.response.send_message("Hello from command 1!", ephemeral=True)

  @app_commands.command(name="deadlines")
  async def command_deadlines(self, interaction: discord.Interaction) -> None:
    """ Get your current and past deadline activities """

    await interaction.response.defer(thinking=True)

    _, username, password = API.get_account(interaction.user.id)

    print(username, password)
    data = API.get_events_data(username, password)

    deadlines_embed = discord.Embed(title="Your Deadlines", description="May be up to 30 minutes out of date", color=0xFEE75C)

    index = 0
    for event in data:
        date_object = datetime.strptime(event['due_date'], ' %d %B %Y, %I:%M %p')
        if date_object > datetime.now():
            index = index + 1
            diff = date_object - datetime.now()
            days_remaining = diff.days
            deadlines_embed.add_field(name=f'**======================` Event #{index} `======================**', 
            value=f"**Event Name**\n{event['event_title']}\n\n**Module Codes:**\n{event['event_codes']}\n\n**Module Name:**\n{event['event_name']}\n\n**Due Date**\n{event['due_date']}\n\nYou have {days_remaining} day(s) remaining to submit\n[-> Add Submission](http://example.com)", inline=False)

    await interaction.followup.send(embed=deadlines_embed, ephemeral=False)

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(MyCog(bot))


