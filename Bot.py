# This example covers advanced startup options and uses some real world examples for why you may need them.

import asyncio
import logging
import sqlite3
import logging.handlers
from dotenv import dotenv_values
import os

from typing import List, Optional

import discord
from discord.ext import commands

class CustomBot(commands.Bot):

    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        testing_guild_id: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.testing_guild_id = 1047097921998442557
        self.initial_extensions = initial_extensions
    
    async def setup_hook(self) -> None:

        for extension in self.initial_extensions:
            print(extension)
            await self.load_extension(extension)

        if self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)

            self.tree.copy_global_to(guild=guild)

            await self.tree.sync(guild=guild)

async def main():

    # Get environmental variables from the config.env file
    config = dotenv_values("config.env")

    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    exts = ['Extensions.deadline']
    async with CustomBot(commands.when_mentioned, initial_extensions=exts, testing_guild_id=1047097921998442557, intents=discord.Intents.all()) as bot:
        print("Starting")
        await bot.start(config['DISCORD_BOT_TOKEN'])


# For most use cases, after defining what needs to run, we can just tell asyncio to run it:
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())