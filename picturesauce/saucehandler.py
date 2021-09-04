import asyncio
import functools
import logging
import os
import random
import string
from copy import copy
from datetime import datetime
from io import BytesIO
import multiprocessing as mp
from multiprocessing.pool import Pool
from typing import Any, Dict, List, Literal, Pattern, Tuple, cast, Optional

import aiohttp
import discord
from redbot import VersionInfo, version_info
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import escape, humanize_list

log = logging.getLogger("red.xangel-cogs.PictureSauce")
_ = Translator("PictureSauce", __file__)


class SauceHandler:
    async def perform_trigger(self, message: discord.Message, trigger: Trigger, find: List[str]) -> None:
        guild: discord.Guild = cast(discord.Guild, message.guild)
        channel: discord.TextChannel = cast(discord.TextChannel, message.channel)
        author: discord.Member = cast(discord.Member, message.author)
        reason = _("Trigger response: {trigger}").format(trigger=trigger.name)
        own_permissions = channel.permissions_for(guild.me)

        if "text" in trigger.response_type and own_permissions.send_messages:
            await channel.trigger_typing()
            if trigger.multi_payload:
                text_response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "text")
            else:
                text_response = str(trigger.text)
            response = await self.convert_parms(message, text_response, trigger, find)
            if response and not channel.permissions_for(author).mention_everyone:
                response = escape(response, mass_mentions=True)
            if version_info >= VersionInfo.from_str("3.4.6") and trigger.reply is not None:
                try:
                    await channel.send(
                        response,
                        tts=trigger.tts,
                        delete_after=trigger.delete_after,
                        reference=message,
                        allowed_mentions=trigger.allowed_mentions(),
                    )
                except discord.errors.Forbidden:
                    log.debug("PictureSauce encountered an error in %r with trigger %r", guild, trigger)
                except Exception:
                    log.exception("PictureSauce encountered an error in %r with trigger %r", guild, trigger)
            else:
                try:
                    await channel.send(
                        response,
                        tts=trigger.tts,
                        delete_after=trigger.delete_after,
                        allowed_mentions=trigger.allowed_mentions(),
                    )
                except discord.errors.Forbidden:
                    log.debug("PictureSauce encountered an error in %r with trigger %r", guild, trigger)
                except Exception:
                    log.exception("PictureSauce encountered an error in %r with trigger %r", guild, trigger)

        if "dm" in trigger.response_type:
            if trigger.multi_payload:
                dm_response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "dm")
            else:
                dm_response = str(trigger.text)
            response = await self.convert_parms(message, dm_response, trigger, find)
            try:
                await author.send(response, allowed_mentions=trigger.allowed_mentions())
            except discord.errors.Forbidden:
                log.debug("Retrigger encountered an error in %r with trigger %r", guild, trigger)
            except Exception:
                log.exception("Retrigger encountered an error in %r with trigger %r", guild, trigger)

        if "dmme" in trigger.response_type:
            if trigger.multi_payload:
                dm_response = "\n".join(t[1] for t in trigger.multi_payload if t[0] == "dmme")
            else:
                dm_response = str(trigger.text)
            response = await self.convert_parms(message, dm_response, trigger, find)
            trigger_author = self.bot.get_user(trigger.author)
            if not trigger_author:
                try:
                    trigger_author = await self.bot.fetch_user(trigger.author)
                except Exception:
                    log.exception("Retrigger encountered an error in %r with trigger %r", guild, trigger)
            try:
                await trigger_author.send(response, allowed_mentions=trigger.allowed_mentions())
            except discord.errors.Forbidden:
                trigger.enabled = False
                log.debug("Retrigger encountered an error in %r with trigger %r", guild, trigger)
            except Exception:
                log.exception("Retrigger encountered an error in %r with trigger %r", guild, trigger)

        if "command" in trigger.response_type:
            if trigger.multi_payload:
                command_response = [t[1] for t in trigger.multi_payload if t[0] == "command"]
                for command in command_response:
                    command = await self.convert_parms(message, command, trigger, find)
                    msg = copy(message)
                    prefix_list = await self.bot.command_prefix(self.bot, message)
                    msg.content = prefix_list[0] + command
                    msg = ReTriggerMessage(message=msg)
                    self.bot.dispatch("message", msg)
            else:
                msg = copy(message)
                command = await self.convert_parms(message, str(trigger.text), trigger, find)
                prefix_list = await self.bot.command_prefix(self.bot, message)
                msg.content = prefix_list[0] + command
                msg = ReTriggerMessage(message=msg)
                self.bot.dispatch("message", msg)

        if "delete" in trigger.response_type and own_permissions.manage_messages:
            # this should be last since we can accidentally delete the context when needed
            log.debug("Performing delete trigger")
            try:
                await message.delete()
                if await self.config.guild(guild).filter_logs():
                    await self.modlog_action(message, trigger, find, _("Deleted Message"))
            except discord.errors.NotFound:
                log.debug("Retrigger encountered an error in %r with trigger %r", guild, trigger)
            except discord.errors.Forbidden:
                log.debug("Retrigger encountered an error in %r with trigger %r", guild, trigger)
            except Exception:
                log.exception("Retrigger encountered an error in %r with trigger %r", guild, trigger)

    async def convert_parms(
        self, message: discord.Message, raw_response: str, trigger: Trigger, find: List[str]
    ) -> str:
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/customcom/customcom.py
        # ctx = await self.bot.get_context(message)
        results = RE_CTX.findall(raw_response)
        for result in results:
            param = await self.transform_parameter(result, message)
            raw_response = raw_response.replace("{" + result + "}", param)
        results = RE_POS.findall(raw_response)
        if results:
            for result in results:
                content = message.content
                if trigger.read_filenames and message.attachments:
                    content = (
                        message.content + " " + " ".join(f.filename for f in message.attachments)
                    )
                search = trigger.regex.search(content)
                if not search:
                    continue
                try:
                    arg = search.group(int(result[0]))
                    raw_response = raw_response.replace("{" + result[0] + "}", arg)
                except IndexError:
                    log.error("Regex pattern is too broad and no matched groups were found.")
                    continue
                except Exception:
                    log.exception("Retrigger encountered an error with trigger %r", trigger)
                    continue
        raw_response = raw_response.replace("{count}", str(trigger.count))
        if hasattr(message.channel, "guild"):
            prefixes = await self.bot.get_prefix(message.channel)
            raw_response = raw_response.replace("{p}", prefixes[0])
            raw_response = raw_response.replace("{pp}", humanize_list(prefixes))
            raw_response = raw_response.replace("{nummatch}", str(len(find)))
            raw_response = raw_response.replace("{lenmatch}", str(len(max(find))))
            raw_response = raw_response.replace("{lenmessage}", str(len(message.content)))
        return raw_response
        # await ctx.send(raw_response)