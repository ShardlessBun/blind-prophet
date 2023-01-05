from marshmallow import Schema, fields, post_load

from ProphetBot.models.db_objects.category_objects import *


class RaritySchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)
    abbreviation = fields.List(fields.String, data_key="abbreviation", required=True)
    seek_dc = fields.Integer(data_key="seek_dc", required=True)
    @post_load
    def make_c_rarity(self, data, **kwargs):
        return Rarity(**data)


class BlacksmithTypeSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_blacksmith_type(self, data, **kwargs):
        return BlacksmithType(**data)


class ConsumableTypeSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_consumable_type(self, data, **kwargs):
        return ConsumableType(**data)


class MagicSchoolSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_magic_school(self, data, **kwargs):
        return MagicSchool(**data)


class CharacterClassSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_character_class(self, data, **kwargs):
        return CharacterClass(**data)


class CharacterSubclassSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    parent = fields.Integer(data_key="parent", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_character_subclass(self, data, **kwargs):
        return CharacterSubclass(**data)


class CharacterRaceSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_character_race(self, data, **kwargs):
        return CharacterRace(**data)


class CharacterSubraceSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    parent = fields.Integer(data_key="parent", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_character_subrace(self, data, **kwargs):
        return CharacterSubrace(**data)


class GlobalModifierSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)
    adjustment = fields.Float(data_key="adjustment", required=True)
    max = fields.Integer(data_key="max", required=True)

    @post_load
    def make_c_global_modifier(self, data, **kwargs):
        return GlobalModifier(**data)


class HostStatusSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_host_status(self, data, **kwargs):
        return HostStatus(**data)


class ArenaTierSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    avg_level = fields.Integer(data_key="avg_level", required=True)
    max_phases = fields.Integer(data_key="max_phases", required=True)

    @post_load
    def make_c_arena_tier(self, data, **kwargs):
        return ArenaTier(**data)


class AdventureTierSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    avg_level = fields.Integer(data_key="avg_level", required=True)

    @post_load
    def make_c_adventure_tier(self, data, **kwargs):
        return AdventureTier(**data)


class ShopTypeSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)
    synonyms = fields.List(fields.String, data_key="synonyms", required=False, default=[])
    tools = fields.List(fields.String, data_key="tools", required=False, default=[])

    @post_load
    def make_c_shop_type(self, data, **kwargs):
        return ShopType(**data)


class ActivitySchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)
    ratio = fields.Float(data_key="ratio", required=False, allow_none=True)
    diversion = fields.Boolean(data_key="diversion", required=True)

    @post_load
    def make_c_activity(self, data, **kwargs):
        return Activity(**data)


class FactionSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_faction(self, data, **kwargs):
        return Faction(**data)


class DashboardTypeSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    value = fields.String(data_key="value", required=True)

    @post_load
    def make_c_dashboard_type(self, data, **kwargs):
        return DashboardType(**data)


class LevelCapsSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    max_gold = fields.Integer(data_key="max_gold", required=True)
    max_xp = fields.Integer(data_key="max_xp", required=True)

    @post_load
    def make_level_caps(self, data, **kwargs):
        return LevelCaps(**data)


class AdventureRewardsSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    ep = fields.Integer(data_key="ep", required=True)
    tier = fields.Integer(data_key="tier", required=True)
    rarity = fields.Integer(data_key="rarity", required=False, allow_none=True)

    @post_load
    def make_adventure_reward(self, data, **kwargs):
        return AdventureRewards(**data)


class ShopTierSchema(Schema):
    id = fields.Integer(data_key="id", required=True)
    rarity = fields.Integer(data_key="rarity", required=True)

    @post_load
    def make_shop_tier(self, data, **kwargs):
        return ShopTier(**data)
