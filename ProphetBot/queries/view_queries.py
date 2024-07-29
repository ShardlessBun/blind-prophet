from sqlalchemy.sql.selectable import FromClause
from ProphetBot.models.db_tables import *

def get_level_distribution_query() -> FromClause:
    return level_distribution_table.select()