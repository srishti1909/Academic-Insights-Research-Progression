import pandas as pd
from sqlalchemy import create_engine, text, exc
from config.mysql_config import MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_DB_NAME, MYSQL_HOST, MYSQL_PORT

db_url = f"mysql+mysqlconnector://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}"

mysql_engine = create_engine(db_url)


def get_top_keywords_by_university(university_name) -> pd.DataFrame:
    query = """
            SELECT k.name AS keyword, SUM(fk.score) AS total_score
            FROM keyword k
            JOIN faculty_keyword fk ON k.id = fk.keyword_id
            JOIN faculty f ON fk.faculty_id = f.id
            JOIN university u ON f.university_id = u.id
            WHERE u.name = :university_name
            GROUP BY k.name
            ORDER BY total_score DESC
            LIMIT 10
        """
    with mysql_engine.connect() as conn:
        data = pd.read_sql_query(text(query), conn, params={"university_name": university_name})
    return data


def update_university_rank(university_id, rank, connection):
    try:
        query = f"UPDATE university SET university_rank = {rank} WHERE id = {university_id}"
        connection.execute(text(query))
    except exc.SQLAlchemyError:
        raise
