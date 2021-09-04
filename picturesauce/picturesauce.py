import asyncio
import logging
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Optional, Union

import discord
from discord.ext import tasks
from redbot.core import Config, VersionInfo, checks, commands, modlog, version_info
from redbot.core.commands import TimedeltaConverter
from redbot.core.i18n import Translator, cog_i18n

@cog_i18n(_)
class PictureSauce(commands.Cog):
        """
    Trigger bot events using regular expressions
    See https://regex101.com/ for help building a regex pattern.
        See `[p]retrigger explain` or click the link below for more details.
        [For more details click here.](https://github.com/TrustyJAID/Trusty-cogs/blob/master/retrigger/README.md)
    """

    __author__ = ["XangelMusic"]
    __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 964565433247, force_registration=True)
        default_guild = {
            "trigger_list": {},
            "allow_multiple": False,
            "modlog": "default",
            "ban_logs": False,
            "kick_logs": False,
            "add_role_logs": False,
            "remove_role_logs": False,
            "filter_logs": False,
            "bypass": False,
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(trigger_timeout=1)
        self.re_pool = Pool()
        self.triggers = {}
        self.__unload = self.cog_unload
        self.trigger_timeout = 1
        self.save_loop.start()


    @commands.group()
    @commands.guild_only()
    async def sauce(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("I can do stuff!")

    @checks.is_owner()
    @sauce.command()
    async def enable(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @sauce.command()
    async def disable(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @sauce.command()
    async def set(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @sauce.command()
    async def block(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @sauce.command()
    async def unset(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @sauce.command()
    async def reset(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @set.command()
    async def all(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")

    @checks.is_owner()
    @unset.command()
    async def all(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("Enable!")
