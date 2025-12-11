import os
import time
from q2db import Q2Db, Q2DbSchema
from q2mysql55_win_local.server import Q2MySQL55_Win_Local_Server

DB_PATH = "test_mysql_data"
PORT = 3366


def run_test():
    print("=== 1) First run: starting MySQL server ===")
    srv = Q2MySQL55_Win_Local_Server()
    srv.start(PORT, DB_PATH)
    print("Server started.")

    # Connect using q2db
    print("Connecting with q2db...")
    database = Q2Db(
        db_engine_name="mysql", host="127.0.0.1", port=PORT, user="root", password="", database_name="testdb"
    )

    schema = Q2DbSchema()

    schema.add(table="topic_table", column="uid", datatype="int", datalen=9, pk=True)
    schema.add(table="topic_table", column="name", datatype="varchar", datalen=100)

    schema.add(table="message_table", column="uid", datatype="int", datalen=9, pk=True)
    schema.add(table="message_table", column="message", datatype="varchar", datalen=100)
    schema.add(
        table="message_table", column="parent_uid", to_table="topic_table", to_column="uid", related="name"
    )
    database.set_schema(schema)
    print("Inserting test rows...")
    for _ in range(4):
        database.insert("topic_table", {"name": f"topic {database.table('topic_table').row_count()}"})

    # import time

    # try:
    #     while True:
    #         print("Server is running... Ctrl+C to stop")
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\nExit by Ctrl+C")

    print("Stopping server...")
    srv.stop()
    print("Server stopped.")

    # SECOND START — verify persistence

    srv2 = Q2MySQL55_Win_Local_Server()
    srv2.start(PORT, DB_PATH)
    print("Server started.")

    print("\n=== 2) Second run: starting MySQL server again ===")
    database = Q2Db(
        db_engine_name="mysql", host="127.0.0.1", port=PORT, user="root", password="", database_name="testdb"
    )

    cursor = database.cursor("select * from topic_table")

    for x in cursor.records():
        print(x)

    print("Stopping second server...")
    srv2.stop()
    print("Test finished.")


if __name__ == "__main__":
    run_test()
