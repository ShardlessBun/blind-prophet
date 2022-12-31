import bisect
import logging
from datetime import datetime
from statistics import mean
import discord
from discord import ApplicationContext, Option, SlashCommandGroup, Role
from discord.ext import commands
from ProphetBot.bot import BpBot
from ProphetBot.helpers import update_dm, get_adventure, get_character, get_adventure_from_role, is_admin
from ProphetBot.models.db_objects import Adventure
from ProphetBot.models.embeds import AdventureCloseEmbed, ErrorEmbed, AdventureStatusEmbed
from ProphetBot.queries import insert_new_adventure, update_adventure

log = logging.getLogger(__name__)


def setup(bot: commands.Bot):
    bot.add_cog(Adventures(bot))


 # TODO: Add @Spectator role option for view only into all IC channels; @Quester for sign-ups and spectator for viewing
 # TODO: Script for modifing/integrating @Spectator role
 # TODO: Set tier command

class Adventures(commands.Cog):
    bot: BpBot  # Typing annotation for my IDE's sake
    adventure_commands = SlashCommandGroup("adventure", "Adventure commands")
    room_commands = SlashCommandGroup("room", "Room commands")

    def __init__(self, bot):
        # Setting up some objects
        self.bot = bot

        log.info(f'Cog \'Adventures\' loaded')

    @adventure_commands.command(
        name="create",
        description="Creates a new adventure"
    )
    async def adventure_create(self, ctx: ApplicationContext,
                               adventure_name: Option(str, description="The name of the adventure as it should show up"
                                                                       "in the category and channel names",
                                                      required=True),
                               role_name: Option(str, description="The name of the Role to be created for adventure"
                                                                  "participants", required=True),
                               dm: Option(discord.Member, description="The DM of the adventure. "
                                                                      "Multiple DM's can be added via the add_dm "
                                                                      "command", required=True)):
        """
        Creates a channel category and role for the adventure, as well as two private channels.

        :param ctx: Context
        :param adventure_name: The name of the adventure as it should show up in the category channel
        :param role_name: The name of the Role to be created for adventure participants
        :param dm: The DM of the adventure
        """
        await ctx.defer()

        # Create the role
        if discord.utils.get(ctx.guild.roles, name=role_name):
            return await ctx.respond(f"Error: role '@{role_name}' already exists")
        else:
            adventure_role = await ctx.guild.create_role(name=role_name, mentionable=True,
                                                         reason=f"Created by {ctx.author.nick} for adventure"
                                                                f"{adventure_name}")
            log.info(f"ADVENTURE: Role {adventure_role} created")

            # Setup role permissions
            category_permissions = dict()
            category_permissions[adventure_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            if loremaster_role := discord.utils.get(ctx.guild.roles, name="Loremaster"):
                category_permissions[loremaster_role] = discord.PermissionOverwrite(view_channel=True,
                                                                                    send_messages=True)
            if lead_dm_role := discord.utils.get(ctx.guild.roles, name="Lead DM"):
                category_permissions[lead_dm_role] = discord.PermissionOverwrite(view_channel=True,
                                                                                 send_messages=True)
            if bots_role := discord.utils.get(ctx.guild.roles, name="Bots"):
                category_permissions[bots_role] = discord.PermissionOverwrite(view_channel=True,
                                                                              send_messages=True)
            category_permissions[ctx.guild.default_role] = discord.PermissionOverwrite(
                view_channel=False,
                send_messages=False
            )

            # Add DM to the role and let them manage messages in their channels
            category_permissions = await update_dm(dm, category_permissions, adventure_role, adventure_name)
            ic_overwrites = category_permissions.copy()
            ooc_overwrites = category_permissions.copy()

            # Setup the questers
            if quester_role := discord.utils.get(ctx.guild.roles, name="Quester"):
                ic_overwrites[quester_role] = discord.PermissionOverwrite(
                    view_channel=True
                )
                ooc_overwrites[quester_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )

            log.info('ADVENTURE: Done creating category permissions and OOC overwrites')

            new_adventure_category = await ctx.guild.create_category_channel(
                name=adventure_name,
                overwrites=category_permissions,
                reason=f"Creating category for {adventure_name}"
            )

            ic_channel = await ctx.guild.create_text_channel(
                name=adventure_name,
                category=new_adventure_category,
                overwrites=ic_overwrites,
                position=0,
                reason=f"Creating adventure {adventure_name} IC Room"
            )

            ooc_channel = await ctx.guild.create_text_channel(
                name=f"{adventure_name}-ooc",
                category=new_adventure_category,
                overwrites=ooc_overwrites,
                position=1,
                reason=f"Creating adventure {adventure_name} OOC Room"
            )

            tier = ctx.bot.compendium.get_object("c_adventure_tier", 1)

            adventure = Adventure(guild_id=ctx.guild.id,name=adventure_name, role_id=adventure_role.id, dms=[dm.id], tier=tier,
                                  category_channel_id=new_adventure_category.id, ep=0)

            async with ctx.bot.db.acquire() as conn:
                await conn.execute(insert_new_adventure(adventure))

            await ooc_channel.send(f"Adventure {adventure.name} successfully created!\n"
                                   f"Role: {adventure_role.mention}\n"
                                   f"IC Room: {ic_channel.mention}\n"
                                   f"OOC Room: {ooc_channel.mention}\n\n"
                                   f"{dm.mention} - Please ensure your permissions are correct in these rooms! "
                                   f"If so, you can start adding players with /adventure add\n"
                                   f"See /adventure help for more details.")

            await ctx.delete()

    @adventure_create.error
    async def create_error(self, ctx, error):
        if isinstance(error, discord.Forbidden):
            await ctx.send(embed=ErrorEmbed(description='Error: Bot isn\'t allowed to do that (for some reason)'))
        elif isinstance(error, discord.HTTPException):
            await ctx.send(embed=ErrorEmbed(description='Error: Creating new role failed, please try again. '
                                                        'If the problem persists, contact the Council'))
        elif isinstance(error, discord.InvalidArgument):
            await ctx.send(embed=ErrorEmbed(description=f'Error: Invalid Argument {error}'))

    @adventure_commands.command(
        name="dm_add",
        description="Add a DM to an adventure. This command must be run in a channel of the adventure."
    )
    async def adventure_dm_add(self, ctx: ApplicationContext,
                               dm: Option(discord.Member, description="Player to add as a DM", required=True)):
        """
        Adds additional DM's to an existing adventure. This command must be run in a channel of the adventure
        they are being added to.

        :param ctx: Context
        :param dm: The DM to add to the adventure
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(embed=ErrorEmbed(description="No adventure associated with this channel"))
        elif dm.id in adventure.dms:
            return await ctx.respond(embed=ErrorEmbed(description="Error: Player already listed as a "
                                                                  "DM for this adventure"))
        elif ctx.author.id not in adventure.dms and not is_admin(ctx):
            return await ctx.respond(embed=ErrorEmbed(description="Error: You either need to be the DM for this "
                                                                  "adventure or Council to do this."))
        else:
            adventure.dms.append(dm.id)
            adventure_role = adventure.get_adventure_role(ctx)
            if adventure_role not in dm.roles:
                await dm.add_roles(adventure_role, reason=f"Creating adventure {adventure.name}")

            category = ctx.channel.category
            category_permissions = category.overwrites
            category_permissions[dm] = discord.PermissionOverwrite(manage_messages=True)

            await category.edit(overwrites=category_permissions)

            for c in category.channels:
                c_permissions = c.overwrites
                c_permissions[dm] = discord.PermissionOverwrite(manage_messages=True)
                await c.edit(overwrites=c_permissions)

            async with ctx.bot.db.acquire() as conn:
                await conn.execute(update_adventure(adventure))

        await ctx.respond(f"Welcome {dm.mention} to the {adventure.name} DM's")

    @adventure_commands.command(
        name="dm_remove",
        description="Removes a DM from an adventure. This command must be run in a channel of the adventure."
    )
    async def adventure_dm_remove(self, ctx: ApplicationContext,
                                  dm: Option(discord.Member, description="Player to remove as a DM", required=True)):
        """
        Removes a DM from an adventure. This command must be run in a channel of the adventure they are being
        removed from.

        :param ctx: Context
        :param dm: The DM to remove from the adventure
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif dm.id not in adventure.dms:
            return await ctx.respond(f"Error: Player not listed as a DM")
        elif len(adventure.dms) == 1:
            return await ctx.respond(f"Error: Adventure has only 1 DM, please add another before removing")
        elif ctx.author.id not in adventure.dms and not is_admin(ctx):
            return await ctx.respond(embed=ErrorEmbed(f"Error: You need to be the DM for this advernture or "
                                                      f"Council to do this."))
        else:
            adventure.dms.remove(dm.id)
            adventure_role = adventure.get_adventure_role(ctx)

            if adventure_role in dm.roles:
                await dm.remove_roles(adventure_role, reason=f"Removing player as DM from {adventure.name}")

            category = ctx.channel.category
            category_permissions = category.overwrites
            del category_permissions[dm]
            await category.edit(overwrites=category_permissions)

            for c in category.channels:
                c_permissions = c.overwrites
                del c_permissions[dm]
                await c.edit(overwrites=c_permissions)

            async with ctx.bot.db.acquire() as conn:
                await conn.execute(update_adventure(adventure))

        await ctx.respond(f"Removed {dm.mention} from {adventure.name} DM's")

    @adventure_commands.command(
        name="add",
        description="Adds a player to an adventure. This command must be run in a channel of the adventure."
    )
    async def adventure_add(self, ctx: ApplicationContext,
                            player_1: Option(discord.Member, description="Player to be added", required=True),
                            player_2: Option(discord.Member, description="Player to be added", required=False),
                            player_3: Option(discord.Member, description="Player to be added", required=False),
                            player_4: Option(discord.Member, description="Player to be added", required=False),
                            player_5: Option(discord.Member, description="Player to be added", required=False),
                            player_6: Option(discord.Member, description="Player to be added", required=False),
                            player_7: Option(discord.Member, description="Player to be added", required=False),
                            player_8: Option(discord.Member, description="Player to be added", required=False),
                            calc_tier: Option(bool, description="Whether to calculate tier when this command runs",
                                              required=False, default=True)):
        """
        Add a player or players to an adventure. This command must be run in a channel of the adventure they are being
        added to.

        :param ctx: Context
        :param player_1: Player to add to an adventure
        :param player_2: Player to add to an adventure
        :param player_3: Player to add to an adventure
        :param player_4: Player to add to an adventure
        :param player_5: Player to add to an adventure
        :param player_6: Player to add to an adventure
        :param player_7: Player to add to an adventure
        :param player_8: Player to add to an adventure
        :param calc_tier: Recalculate the tier on command run? Default=True
        """
        await ctx.defer()
        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        players = list(set(filter(
            lambda p: p is not None,
            [player_1, player_2, player_3, player_4, player_5, player_6, player_7, player_8]
        )))

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms:
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            adventure_role = adventure.get_adventure_role(ctx)
            for player in players:
                if adventure_role in player.roles:
                    await ctx.send(f"{player.mention} already in adventure '{adventure.name}'")
                else:
                    await player.add_roles(adventure_role, reason=f"{player.name} added to role {adventure_role.name} by"
                                                                  f"{ctx.author.name}")
                    await ctx.send(f"{player.mention} added to adventure '{adventure.name}'")

            # Tier Calculation
        if calc_tier:
            players = list(set(filter(lambda p: p.id not in adventure.dms,
                                      adventure_role.members)))
            characters = []
            for player in players:
                characters.append(await get_character(ctx.bot, player.id, ctx.guild_id))

            if len(characters) == 0:
                return await ctx.respond(f"Error: players don't have characters")

            avg_level = mean([c.get_level() for c in characters])

            tier = bisect.bisect([t.avg_level for t in list(ctx.bot.compendium.c_adventure_tier[0].values())],
                                 avg_level)

            adventure.tier = ctx.bot.compendium.get_object("c_adventure_tier", tier)

            async with ctx.bot.db.acquire() as conn:
                await conn.execute(update_adventure(adventure))

        await ctx.delete()

    @adventure_commands.command(
        name="remove",
        description="Removes a player from an adventure. This command must be run in a channel of the adventure."
    )
    async def adventure_remove(self, ctx: ApplicationContext,
                               player: Option(discord.Member, description="Player to be removed", required=True)):
        """
        Removes a player from an adventure. This command must be run in a channel of the adventure they are being
        removed from.

        :param ctx: Context
        :param player: Player to remove from the adventure
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms:
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            adventure_role = adventure.get_adventure_role(ctx)
            if adventure_role not in player.roles:
                return await ctx.respond(f"Error: {player.mention} does not have role '{adventure_role.mention}'")
            else:
                await player.remove_roles(adventure_role,
                                          reason=f"{player.name} removed from role {adventure_role.name}"
                                                 f" by {ctx.author.name}")
        await ctx.delete()

    @adventure_commands.command(
        name="close",
        descripion="Close out an adventure"
    )
    async def adventure_close(self, ctx: ApplicationContext,
                              role: Option(Role, description="Role of the adventure to close", required=False,
                                           default=None)):
        """
        Marks an adventure as closed, and removes the Role from players

        :param ctx:  Context
        :param role: Role of the adventure
        """

        if role is None:
            adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)
        else:
            adventure: Adventure = await get_adventure_from_role(ctx.bot, role.id)

        if adventure is None and role is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif adventure is None:
            return await ctx.respond(f"Error: No adventure found for {role.mention}.")
        elif ctx.author.id not in adventure.dms and not is_admin(ctx):
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            adventure_role = adventure.get_adventure_role(ctx)
            adventure.end_ts = datetime.utcnow()

            await ctx.respond(embed=AdventureCloseEmbed(ctx, adventure))

            for member in adventure_role.members:
                await member.remove_roles(adventure_role, reason=f"Adventure completed")

            async with ctx.bot.db.acquire() as conn:
                await conn.execute(update_adventure(adventure))

    @adventure_commands.command(
        name="status",
        description="Adventure status"
    )
    async def adventure_status(self, ctx: ApplicationContext,
                               role: Option(Role, description="Role of the adventure if not ran in an Adventure Channel",
                                            required=False, default=None)):

        if role is None:
            adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)
        else:
            adventure: Adventure = await get_adventure_from_role(ctx.bot, role.id)

        if adventure is None and role is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif adventure is None:
            return await ctx.respond(f"Error: No adventure found for {role.mention}.")

        return await ctx.respond(embed=AdventureStatusEmbed(ctx, adventure))

    @room_commands.command(
        name="add_room",
        description="Adds a channel to this adventure category."
    )
    async def room_add(self, ctx: ApplicationContext,
                       room_name: Option(str, description="The name of the new room. "
                                                          "Spaces will become dashes and forced lowercase",
                                         required=True)):
        """
        Adds a TextChannel to the adventure Category. This command must be run in the Category the channel is to be
        added to.

        :param ctx: Context
        :param room_name: Name of the room to add. This will automatically be formatted to Discord standards
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms:
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            category = ctx.channel.category
            new_room = await category.create_text_channel(room_name, reason=f"Additional adventure room created by "
                                                                            f"{ctx.author.name}")
            await ctx.respond(f"Room {new_room.mention} successfully created by {ctx.author.mention}")

    @room_add.error
    async def addroom_errors(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Error: Command cannot be used via private messages')
        log.error(error)

    @room_commands.command(
        name="rename",
        description="Changes the name of a room"
    )
    async def room_rename(self, ctx: ApplicationContext,
                          room_name: Option(str, description="Name to change the room to")):
        """
        Renames a TextChannel. This must be run in the room to be renamed.

        :param ctx: Context
        :param room_name: The name to change the TextChannel name to
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms:
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            await ctx.channel.edit(name=room_name)
            await ctx.respond(f"Room name changed to {ctx.channel.mention}")

    # TODO: Allow for posting options as well 'Open view', 'Close view', 'Open post', 'Close post', 'Open all', 'Close all'
    @room_commands.command(
        name="view",
        description="Open or close a channel for public viewing"
    )
    async def room_open(self, ctx: ApplicationContext,
                        view: Option(str, description="Open or close the room", choices=['open', 'close'],
                                     required=True),
                        allow_post: Option(bool, description="Whether to allow public posts", required=False,
                                           default=False)):
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms and not is_admin(ctx):
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            overwrites = ctx.channel.overwrites
            room_view = True if view.lower() == "open" else False
            if quester_role := discord.utils.get(ctx.guild.roles, name="Quester"):
                overwrites[quester_role] = discord.PermissionOverwrite(view_channel=room_view,
                                                                       send_messages=allow_post)
                await ctx.channel.edit(overwrites=overwrites)
                val = "closed" if view == "close" else "open"
                if allow_post:
                    await ctx.respond(f"{ctx.channel.mention} is now {val} and able to be posted in by the "
                                      f"{quester_role.mention} role")
                else:
                    await ctx.respond(f"{ctx.channel.mention} is now {val} to the {quester_role.mention} role")
            else:
                await ctx.respond("Couldn't find the @Quester role")

    @room_commands.command(
        name="move",
        description="Moves the current channel within the adventure category."
    )
    async def room_move(self, ctx: ApplicationContext,
                        position: Option(str, description="Where to move the room", required=True,
                                         choices=['top', 'up', 'down', 'bottom'])):
        """
        Moves the current TextChannel within the current Category
        :param ctx: Context
        :param position: Where to move the Textchannel
        """
        await ctx.defer()

        adventure: Adventure = await get_adventure(ctx.bot, ctx.channel.category_id)

        if adventure is None:
            return await ctx.respond(f"Error: No adventure associated with this channel")
        elif ctx.author.id not in adventure.dms:
            return await ctx.respond(f"Error: You are not a DM of this adventure")
        else:
            category = ctx.channel.category
            channels = category.channels
            old_position = channels.index(ctx.channel)

            match position.lower():
                case 'top':
                    if old_position == 0:
                        return await ctx.respond(f"Error: Channel position is already at top.")
                    else:
                        new_position = 0

                case 'up':
                    if old_position == 0:
                        return await ctx.respond(f"Error: Channel position is already at top.")
                    else:
                        new_position = old_position - 1
                case 'down':
                    if old_position == len(channels) - 1:
                        return await ctx.respond(f"Error: Channel already at the lowest position.")
                    else:
                        new_position = old_position + 1
                case 'bottom':
                    if old_position == len(channels) - 1:
                        return await ctx.respond(f"Error: Channel already at the lowest position.")
                    else:
                        new_position = len(channels) - 1

            channels.insert(new_position, channels.pop(old_position))

            for i, c in enumerate(channels):
                await c.edit(position=i)

            await ctx.respond(f"Channel {ctx.channel.mention} moved to position {new_position + 1} of {len(channels)}")
