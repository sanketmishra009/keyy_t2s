from dotenv import load_dotenv
import os
from langchain_community.utilities import SQLDatabase

load_dotenv()

TABLES = [
    "accelerated_reward_rules",
    "scraped_brand_offers",
    "bank_offers",
    "card_benefits_v7",
    "cards",
]

db = SQLDatabase.from_uri(
    os.getenv("DB_URL"),
    include_tables=TABLES,
    sample_rows_in_table_info=1,
)

if __name__ == "__main__":
    print(db.dialect, "\n", db.get_usable_table_names(), "\n", db.get_table_info())
