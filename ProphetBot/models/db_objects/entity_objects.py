import math
import datetime
import calendar
from typing import List
import discord
from ProphetBot.models.db_objects.category_objects import *


class PlayerCharacterClass(object):
    character_id: int
    primary_class: CharacterClass
    subclass: CharacterSubclass
    active: bool

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_formatted_class(self):
        if self.subclass is not None:
            return f"{self.subclass.value} {self.primary_class.value}"
        else:
            return f"{self.primary_class.value}"


class PlayerCharacter(object):
    # Attributes based on queries: total_level, div_gold, max_gold, div_xp, max_xp, l1_arena, l2_arena, l1_rp, l2_rp
    player_id: int
    guild_id: int
    name: str
    race: CharacterRace
    subrace: CharacterSubrace
    xp: int
    div_xp: int
    gold: int
    div_gold: int
    active: bool
    faction: Faction
    reroll: bool

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_level(self):
        level = math.ceil((self.xp + 1) / 1000)
        return level if level <= 20 else 20

    def get_member(self, ctx: ApplicationContext) -> discord.Member:
        return discord.utils.get(ctx.guild.members, id=self.player_id)

    def get_member_mention(self, ctx: ApplicationContext):
        try:
            name = discord.utils.get(ctx.guild.members, id=self.player_id).mention
            pass
        except:
            name = f"Player {self.player_id} not found on this server for character {self.name}"
            pass
        return name

    def mention(self) -> str:
        return f"<@{self.player_id}>"

    def get_formatted_race(self):
        if self.subrace is not None:
            return f"{self.subrace.value} {self.race.value}"
        else:
            return f"{self.race.value}"


class PlayerGuild(object):
    id: int
    max_level: int
    server_xp: int
    weeks: int
    week_xp: int
    xp_adjust: int
    max_reroll: int
    greeting: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_reset_day(self):
        if hasattr(self, "reset_day"):
            weekDays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
            return weekDays[self.reset_day]

    def get_next_reset(self):
        if self.reset_hour is not None:
            now = datetime.datetime.utcnow()
            day_offset = (self.reset_day - now.weekday() + 7) % 7
            test = now - datetime.timedelta(days=6)

            run_date = now + datetime.timedelta(days=day_offset)

            if (self.reset_hour < now.hour and run_date <= now) \
                    or (run_date < (self.last_reset + datetime.timedelta(days=6))):
                run_date += datetime.timedelta(days=7)

            dt = calendar.timegm(
                datetime.datetime(run_date.year, run_date.month, run_date.day, self.reset_hour, 0, 0).utctimetuple())

            return dt
        else:
            return None

    def get_last_reset(self):
        return calendar.timegm(self.last_reset.utctimetuple())

    def get_xp_goal(self, total: int, inactive: List[PlayerCharacter] | None) -> int:
        in_count = 0 if inactive is None else len(inactive)
        return ((self.max_level + 1) * (total - in_count)) * self.xp_adjust

    def get_xp_percent(self, total: int, inactive: List[PlayerCharacter | None]) -> float:
        return round((self.total_xp() / self.get_xp_goal(total, inactive)) * 100,2)

    def get_xp_float(self, total: int, inactive: List[PlayerCharacter] | None) -> float:
        return round((self.total_xp() / self.get_xp_goal(total, inactive)), 2)
    def total_xp(self) -> int:
        return self.week_xp + self.server_xp




class Adventure(object):
    guild_id: int
    name: str
    role_id: int
    dms: List[int]
    tier: AdventureTier
    category_channel_id: int
    ep: int

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_adventure_role(self, ctx: ApplicationContext) -> Role:
        return discord.utils.get(ctx.guild.roles, id=self.role_id)


class DBLog(object):
    author: int
    xp: int
    server_xp: int
    gold: int
    character_id: int
    activity: Activity
    notes: str
    shop_id: int | None
    adventure_id: int | None
    invalid: bool

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_author(self, ctx: ApplicationContext) -> discord.Member | None:
        return discord.utils.get(ctx.guild.members, id=self.author)


class Arena(object):
    channel_id: int
    role_id: int
    host_id: int
    tier: ArenaTier
    completed_phases: int

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_role(self, ctx: ApplicationContext | discord.Interaction) -> Role:
        return discord.utils.get(ctx.guild.roles, id=self.role_id)

    def get_host(self, ctx: ApplicationContext | discord.Interaction) -> discord.Member:
        return discord.utils.get(ctx.guild.members, id=self.host_id)


class Shop(object):
    guild_id: int
    name: str
    type: ShopType
    owner_id: int
    channel_id: int
    shelf: int
    network: int
    mastery: int
    seeks_remaining: int
    max_cost: int | None
    seek_roll: str | None
    inventory_rolled: bool
    active: bool

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_owner(self, ctx: ApplicationContext | discord.Interaction) -> discord.Member:
        return discord.utils.get(ctx.guild.members, id=self.owner_id)
