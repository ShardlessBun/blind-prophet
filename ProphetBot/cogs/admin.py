import asyncio
import logging

import discord
from discord import SlashCommandGroup, Option, ExtensionAlreadyLoaded, ExtensionNotFound, ExtensionNotLoaded, \
    ApplicationContext
from discord.ext import commands, tasks
from os import listdir

from ProphetBot.constants import ADMIN_GUILDS
from ProphetBot.helpers import is_owner, is_admin, get_adventure
from ProphetBot.bot import BpBot

log = logging.getLogger(__name__)

def setup(bot: commands.Bot):
    bot.add_cog(Admin(bot))


class Admin(commands.Cog):
    bot: BpBot  # Typing annotation for my IDE's sake
    admin_commands = SlashCommandGroup("admin", "Bot administrative commands", guild_ids=ADMIN_GUILDS)

    def __init__(self, bot):
        self.bot = bot
        log.info(f'Cog \'Admin\' loaded')

    @commands.Cog.listener()
    async def on_db_connected(self):
        if not self.reload_category_task.is_running():
            asyncio.ensure_future(self.reload_category_task.start())

    @commands.Cog.listener()
    async def on_compendium_loaded(self):
        if not self.reload_item_task.is_running():
            asyncio.ensure_future(self.reload_item_task.start())

    @admin_commands.command(
        name="load",
        description="Load a cog"
    )
    @commands.check(is_owner)
    async def load_cog(self, ctx: ApplicationContext,
                       cog: Option(str, description="Cog name", required=True)):
        """
        Loads a cog in the bot

        :param ctx: Application context
        :param cog: Cog name to load
        """
        try:
            self.bot.load_extension(f'ProphetBot.cogs.{cog}')
        except ExtensionAlreadyLoaded:
            return await ctx.respond(f'Cog already loaded', ephemeral=True)
        except ExtensionNotFound:
            return await ctx.respond(f'No cog found by the name: {cog}', ephemeral=True)
        except:
            return await ctx.respond(f'Something went wrong', ephemeral=True)
        await ctx.respond(f'Cog Loaded.', ephemeral=True)

    @admin_commands.command(
        name="unload",
        description="Unload a cog"
    )
    @commands.check(is_owner)
    async def unload_cog(self, ctx: ApplicationContext,
                         cog: Option(str, description="Cog name", required=True)):
        """
        Unloads a cog from the bot

        :param ctx: Application context
        :param cog: Cog name to unload
        """
        try:
            self.bot.unload_extension(f'ProphetBot.cogs.{cog}')
        except ExtensionNotLoaded:
            return await ctx.respond(f'Cog was already unloaded', ephemeral=True)
        except ExtensionNotFound:
            return await ctx.respond(f'No cog found by the name: {cog}', ephemeral=True)
        except:
            return await ctx.respond(f'Something went wrong', ephemeral=True)
        await ctx.respond(f'Cog unloaded', ephemeral=True)

    # TODO: Once compendium is up and running reload that too in place of sheets
    @admin_commands.command(
        name="reload",
        description="Reloads either a specific cog, refresh DB information, or reload everything"
    )
    @commands.check(is_owner)
    async def reload_cog(self, ctx: ApplicationContext,
                         cog: Option(str, description="Cog name, ALL, or SHEET", required=True)):
        """
        Used to reload a cog, refresh DB information, or reload all cogs and DB information

        :param ctx: Context
        :param cog: cog to reload, SHEET to reload sheets, ALL to reload all
        """
        await ctx.defer()

        if str(cog).upper() == 'ALL':
            for file_name in listdir('./ProphetBot/cogs'):
                if file_name.endswith('.py'):
                    ext = file_name.replace('.py', '')
                    self.bot.unload_extension(f'ProphetBot.cogs.{ext}')
                    self.bot.load_extension(f'ProphetBot.cogs.{ext}')
            await ctx.respond("All cogs reloaded")
            await self._reload_sheets(ctx)
        elif str(cog).upper() in ['DB', 'COMPENDIUM']:
            await self._reload_DB(ctx)
            await ctx.respond(f'Done')
        elif str(cog).upper() in ['INVENTORY']:
            await self._reload_items(ctx)
            await ctx.respond(f'Done')
        else:
            try:
                self.bot.unload_extension(f'ProphetBot.cogs.{cog}')
            except ExtensionNotLoaded:
                return await ctx.respond(f'Cog was already unloaded', ephemeral=True)
            except ExtensionNotFound:
                return await ctx.respond(f'No cog found by the name: {cog}', ephemeral=True)
            except:
                return await ctx.respond(f'Something went wrong', ephemeral=True)

            self.bot.load_extension(f'ProphetBot.cogs.{cog}')
            await ctx.respond(f'Cog {cog} reloaded')

    @admin_commands.command(
        name="list",
        description="List out all cogs"
    )
    @commands.check(is_owner)
    async def list(self, ctx: ApplicationContext):
        """
        List all cogs

        :param ctx: Context
        """

        files = []
        for file_name in listdir('./ProphetBot/cogs'):
            if file_name.endswith('.py'):
                files.append(file_name[:-3])
        await ctx.respond("\n".join(files))

    @commands.command("overwrites")
    @commands.check(is_owner)
    async def overwrites(self, ctx: ApplicationContext):
        str = f"**Channel Overwrites**\n"

        for key in ctx.channel.overwrites:
            str += f"{key.name.replace('@', '')}"
            str += f" - {ctx.channel.overwrites[key]._values}\n"

        str += f"\n\n**Category Overwrites**\n"

        for key in ctx.channel.category.overwrites:
            str += f"{key.name.replace('@', '')}"
            str += f"{ctx.channel.category.overwrites[key]._values}\n"

        await ctx.send(str)

    @commands.command('msg')
    @commands.check(is_owner)
    async def msg_check(self, ctx: ApplicationContext,
                        channel_id: int,
                        message_id: int):
        if channel := ctx.guild.get_channel(channel_id):
            if message := discord.utils.get(await channel.history(limit=100).flatten(), id=message_id):
                print(message.attachments)
                print(message.content)
                await ctx.send(f"Attachments: {message.attachments}")

    @commands.command("reactions")
    @commands.check(is_owner)
    async def reactions(self, ctx: ApplicationContext, message_id: int, channel_id: int):
        if channel := ctx.guild.get_channel(channel_id):
            if message := discord.utils.get(await channel.history(limit=100).flatten(), id=message_id):
                reaction_info = []
                for reaction in message.reactions:
                    async for user in reaction.users():
                        reaction_info.append((user.id, user.name, user.display_name))

                output_text = "\n".join(f"{user_id},{username},{display_name}" for user_id, username, display_name in reaction_info)

                # Write the information to a file
                file_name = f'reaction_info_{message_id}.txt'
                with open(file_name, 'w') as file:
                    file.write(output_text)

                # Send the file as an attachment with a message
                with open(file_name, 'rb') as file:
                    file = discord.File(file)
                    await ctx.send(f'Reaction information for message {message_id}:', file=file)

                # Delete the file after sending
                import os
                os.remove(file_name)

    # --------------------------- #
    # Private Methods
    # --------------------------- #

    async def _reload_DB(self, ctx):
        await self.bot.compendium.reload_categories(self.bot)
        await ctx.send("Compendium reloaded")

    async def _reload_items(self, ctx):
        await self.bot.compendium.load_items(self.bot)
        await ctx.send("Items reloading")

    # --------------------------- #
    # Tasks
    # --------------------------- #
    @tasks.loop(minutes=30)
    async def reload_category_task(self):
        await self.bot.compendium.reload_categories(self.bot)

    @tasks.loop(hours=24)
    async def reload_item_task(self):
        await self.bot.compendium.load_items(self.bot)
