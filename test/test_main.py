import backend.db_sql as db_sql


def test_table_creation():
    db_sql.create_table()
    # You could query the table and assert it exists (mocked DB in real CI)
