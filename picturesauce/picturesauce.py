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

# from redbot.core.utils import menus
from redbot.core.utils.chat_formatting import humanize_list, pagify
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from .converters import (
    ChannelUserRole,
    MultiResponse,
    Trigger,
    ValidEmoji,
    ValidRegex,
)
from .saucehandler import SauceHandler

log = logging.getLogger("red.xangel-cogs.PictureSauce")
_ = Translator("PictureSauce", __file__)


@cog_i18n(_)
class PictureSauce(SauceHandler, commands.Cog):
    """
    PictureSauce bot events using SauceNAO
    See https://regex101.com/ for help building a regex pattern.
        See `[p]retrigger explain` or click the link below for more details.
    """

    # __author__ = ["XangelMusic"]
    # __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 854677551245, force_registration=True)
        default_guild = {
            "modlog": "default",
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




    @commands.command()
    async def saucenao(self, ctx, user: str):
        saucenao_keys = await self.bot.get_shared_api_tokens("saucenao")
        if saucenao_keys.get("api_key") is None:
            return await ctx.send("The SauceNAO API key has not been set.")
        # Use the API key to access content as you normally would

    @commands.group()
    async def sauce(self, ctx: commands.Context) -> None:
        """This does stuff!"""

    # @checks.is_owner()
    @sauce.command()
    async def create(self, ctx: commands.Context) -> None:
        """This does stuff!"""

    # @checks.is_owner()
    @sauce.command()
    async def destroy(self, ctx: commands.Context) -> None:
        """This does stuff!"""

    # @checks.is_owner()
    @sauce.command()
    async def enable(self, ctx: commands.Context):
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce enable")

    # @checks.is_owner()
    @sauce.command()
    async def disable(self, ctx: commands.Context):
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce disable")

    # @checks.is_owner()
    @sauce.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def set(self, ctx: commands.Context, delete_after: Optional[TimedeltaConverter] = None) -> None:
        """
        Add a text response trigger
        `<name>` name of the trigger.
        `<regex>` the regex that will determine when to respond.
        `[delete_after]` Optionally have the text autodelete must include units e.g. 2m.
        `<text>` response of the trigger.
        See https://regex101.com/ for help building a regex pattern.
        See `[p]retrigger explain` or click the link below for more details.
        [For more details click here.](https://github.com/TrustyJAID/Trusty-cogs/blob/master/retrigger/README.md)
        """
        guild = ctx.guild
        author = ctx.message.author.id

        delete_after_seconds = None
        if delete_after:
            if delete_after.total_seconds() > 0:
                delete_after_seconds = delete_after.total_seconds()
            if delete_after.total_seconds() < 1:
                return await ctx.send(_("`delete_after` must be greater than 1 second."))

        if ctx.guild.id not in self.triggers:
            self.triggers[ctx.guild.id] = Trigger(
                author,
                created_at=ctx.message.id,
                delete_after=delete_after_seconds,
            )

        trigger_list = await self.config.guild(guild).trigger_list()
        trigger_list[name] = await new_trigger.to_json()
        await self.config.guild(guild).trigger_list.set(trigger_list)
        await ctx.send(_("Trigger `{name}` set.").format(name=name))

        if len(channel_user_role) < 1:
            return await ctx.send("You must supply 1 or more channels users or roles to be allowed")
        for obj in channel_user_role:
            if obj.id not in trigger.whitelist:
                async with self.config.guild(ctx.guild).trigger_list() as trigger_list:
                    trigger.whitelist.append(obj.id)
                    trigger_list[trigger.name] = await trigger.to_json()
        await self.remove_trigger_from_cache(ctx.guild.id, trigger)
        
        await ctx.send("This command is: sauce set")

    @sauce.command()
    async def block(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce block")

    @sauce.command()
    async def remove(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce unset")

    @sauce.command()
    async def reset(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce reset")

    @set.command()
    async def set_all(self, ctx: commands.Context) -> None:
        """This does stuff!"""
        # Your code will go here
        await ctx.send("This command is: sauce set all")

