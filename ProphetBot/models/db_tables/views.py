import sqlalchemy as sa
from sqlalchemy import Column, Integer
from ProphetBot.models.db_tables.base import metadata


level_distribution_table = sa.Table(
    "Level Distribution",
    metadata,
    Column("Level", Integer, nullable=False),
    Column("#", Integer, nullable=False, default=0)
)
