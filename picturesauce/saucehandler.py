import asyncio
import functools
import logging
import os
import random
import re
import string
import tldextract
from copy import copy
from datetime import datetime
from io import BytesIO
import multiprocessing as mp
from multiprocessing.pool import Pool
from saucenao_api import SauceNao
from typing import Any, Dict, List, Literal, Pattern, Tuple, cast, Optional

import aiohttp
import discord
from redbot import VersionInfo, version_info
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import escape, humanize_list

from .converters import Trigger
# from .message import ReTriggerMessage

log = logging.getLogger("red.xangel-cogs.PictureSauce")
_ = Translator("PictureSauce", __file__)


class SauceHandler:
    """
    Handles all processing of triggers
    """

    config: Config
    bot: Red
    re_pool: Pool
    triggers: Dict[int, Trigger]
    trigger_timeout: int

    def __init__(self, *args):
        self.config: Config
        self.bot: Red
        self.re_pool: Pool
        self.triggers: Dict[int, Trigger]
        self.trigger_timeout: int

    async def check_bw_list(self, trigger: Trigger, message: discord.Message):
        author: discord.Member = cast(discord.Member, message.author)
        channel: discord.TextChannel = cast(discord.TextChannel, message.channel)
        if trigger.blacklist:
            if channel.id in trigger.blacklist:
                return False
            if channel.category_id in trigger.blacklist:
                return False
            if message.author.id in trigger.blacklist:
                return False
            for role in author.roles:
                if role.is_default():
                    continue
                if role.id in trigger.blacklist:
                    return False
        elif trigger.whitelist:
            if channel.id in trigger.whitelist:
                return True
            if channel.category_id in trigger.whitelist:
                return True
            if message.author.id in trigger.whitelist:
                return True
            for role in author.roles:
                if role.is_default():
                    continue
                if role.id in trigger.whitelist:
                    return True
        else:
            return None

    async def is_mod_or_admin(self, member: discord.Member) -> bool:
        guild = member.guild
        if member == guild.owner:
            return True
        if await self.bot.is_owner(member):
            return True
        if await self.bot.is_admin(member):
            return True
        if await self.bot.is_mod(member):
            return True
        return False

    async def check_is_command(self, message: discord.Message) -> bool:
        """Checks if the message is a bot command"""
        prefix_list = await self.bot.command_prefix(self.bot, message)
        msg = message.content
        is_command = False
        for prefix in prefix_list:
            if msg.startswith(prefix):
                # Don't run a trigger if it's the name of a command
                command_text = msg.replace(prefix, "").split(" ")[0]
                if not command_text:
                    continue
                command = self.bot.get_command(command_text)
                if command:
                    is_command = True
        return is_command

    async def perform_trigger(self, message: discord.Message, trigger: Trigger) -> None:

        guild: discord.Guild = cast(discord.Guild, message.guild)
        channel: discord.TextChannel = cast(discord.TextChannel, message.channel)
        own_permissions = channel.permissions_for(guild.me)

        if own_permissions.send_messages:
            url_re = "https?.*\.(?:jpg|png|jpeg|webp)"
            urls: list = []

            if message.attachments:
                for attachment in message.attachments:
                    urls.append(attachment.url)
            if re.search(url_re, message.content):
                for url in re.findall(url_re, message.content):
                    urls.append(url)

            if urls:
                saucenao_keys = await self.bot.get_shared_api_tokens("saucenao")
                sauce = SauceNao(saucenao_keys.get("api_key"))
                for url in urls:
                    await channel.trigger_typing()
                    sauce_link = "?url=".format(SauceNao.SAUCENAO_URL, url)
                    results = sauce.from_url(url)[0]

                    embed = discord.Embed(title="{} by {} ()".format(results.title, results.author, results.similarity),
                                          url=sauce_link,
                                          # description="**[{}]({})**".format(results.title, sauce_link),
                                          color=await self.bot.get_embed_colour(channel))
                    embed.set_thumbnail(url=results[0].thumbnail)
                    # setattr(embed.thumbnail, "width", 32)
                    # setattr(embed.thumbnail, "height", 32)

                    for x in range(2):
                        if results.urls[x]:
                            lnk = results.urls[x]
                            ext = tldextract.extract(lnk)
                            embed.add_field(name=ext.subdomain.capitalize(),
                                            value="[Source]({})".format(lnk),
                                            inline=False if len(results.urls) == 1 else True)

                    error_msg = "Retrigger encountered an error in %r with trigger %r"
                    try:
                        if version_info >= VersionInfo.from_str("3.4.6"):
                            await channel.send(
                                embed=embed,
                                delete_after=trigger.delete_after,
                                reference=message
                            )
                        else:
                            await channel.send(
                                embed=embed,
                                delete_after=trigger.delete_after
                            )
                    except discord.errors.Forbidden:
                        log.debug(error_msg, guild, trigger)
                    except Exception:
                        log.exception(error_msg, guild, trigger)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None:
            return
        if message.author.bot:
            return
        # if version_info >= VersionInfo.from_str("3.4.0"):
        #     if await self.bot.cog_disabled_in_guild(self, Red, message.guild):
        #         return
        # if getattr(message, "retrigger", False):
        #     log.debug("A ReTrigger dispatched message, ignoring.")
        #     return

        """
        This is where we iterate through the triggers and perform the
        search. This does all the permission checks and cooldown checks
        before actually running the regex to avoid possibly long regex
        operations.
        """
        guild: discord.Guild = cast(discord.Guild, message.guild)
        if guild.id not in self.triggers:
            return
        # channel: discord.TextChannel = cast(discord.TextChannel, message.channel)
        author: Optional[discord.Member] = guild.get_member(message.author.id)
        if not author:
            return

        blocked = not await self.bot.allowed_by_whitelist_blacklist(author)
        # channel_perms = channel.permissions_for(author)
        is_command = await self.check_is_command(message)
        # is_mod = await self.is_mod_or_admin(author)

        autoimmune = getattr(self.bot, "is_automod_immune", None)
        # auto_mod = ["delete", "kick", "ban", "add_role", "remove_role"]
        for trigger in self.triggers[guild.id]:
            if not trigger.enabled:
                continue
            # if edit and not trigger.check_edits:
            #     continue
            # if trigger.chance:
            #     if random.randint(0, trigger.chance) != 0:
            #         continue

            allowed_trigger = await self.check_bw_list(trigger, message)
            # is_auto_mod = trigger.response_type in auto_mod
            if not allowed_trigger:
                continue
            if is_command and not trigger.ignore_commands:
                continue
            if blocked:
                log.debug(
                    "ReTrigger: Channel is ignored or %r is blacklisted %r",
                    author,
                    trigger,
                )
                continue

            await self.perform_trigger(message, trigger)
            return
