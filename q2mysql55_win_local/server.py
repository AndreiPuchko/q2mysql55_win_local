import subprocess
import os
import time
import shutil
import importlib.resources as resources
from pathlib import Path


class Q2MySQL55_Win_Local_Server:
    """
    Lightweight MySQL 5.5 wrapper (Windows only),
    automatically finds mysqld.exe & mysqladmin.exe in package,
    generates my.ini on first launch.
    """

    def __init__(self):
        self.process = None
        self.datadir = None
        self.port = None

        self.basedir = self._find_binaries_dir()
        self.mysqld = os.path.join(self.basedir, "bin/mysqld.exe")
        self.mysqladmin = os.path.join(self.basedir, "bin/mysqladmin.exe")

        if not os.path.exists(self.mysqld):
            raise FileNotFoundError(f"mysqld.exe not found in {self.basedir}/bin")

        if not os.path.exists(self.mysqladmin):
            raise FileNotFoundError(f"mysqladmin.exe not found in {self.basedir}/bin")

    def start(self, port: int, datadir: str):
        self.port = port
        self.datadir = os.path.realpath(datadir)
        self._check_datadir()

        # Ensure my.ini exists
        ini_path = self._generate_my_ini(self.datadir, self.port)
        args = [
            self.mysqld,
            f"--defaults-file={ini_path}",
            f"--basedir={self.basedir}",
            f"--datadir={self.datadir}",
            f"--port={self.port}",
            "--console",
        ]

        DETACHED_PROCESS = 0x00000008
        NEW_GROUP = 0x00000200
        creationflags = DETACHED_PROCESS | NEW_GROUP

        with open(os.devnull, "w") as fnull:
            self.process = subprocess.Popen(
                args,
                cwd=self.basedir,
                stdout=fnull,
                stderr=fnull,
                stdin=fnull,
                text=True,
                creationflags=creationflags,
                # shell=True,
            )

        # Wait for start
        for _ in range(50):  # ~5 seconds
            time.sleep(0.1)
            if self._is_running():
                return True

        raise RuntimeError("MySQL server failed to start.")

    def _check_datadir(self):
        os.makedirs(self.datadir, exist_ok=True)
        if not os.path.isdir(self.datadir):
            raise RuntimeError(f"Can't create MySQL datadir = {self.datadir}")
        if not os.path.isdir(f"{self.datadir}/mysql"):
            shutil.copytree(f"{self.basedir}/data/mysql", f"{self.datadir}/mysql")
        if not os.path.isdir(f"{self.datadir}/performance_schema"):
            shutil.copytree(f"{self.basedir}/data/performance_schema", f"{self.datadir}/performance_schema")

    def _is_running(self):
        return self.process is not None and self.process.poll() is None

    def _find_binaries_dir(self) -> str:
        try:
            if __package__:
                root = resources.files(__package__)
                return os.path.abspath(str(root / "mysql55_files"))
            else:
                return f"{os.path.dirname( __file__)}/mysql55_files"
        except Exception:
            import pkg_resources

            return os.path.abspath(pkg_resources.resource_filename(__package__, "mysql55_files"))

    def _generate_my_ini(self, path: str, port: int):
        ini_path = Path(path) / "my.ini"

        if ini_path.exists():
            return str(ini_path)
        basedir = self.basedir.replace("\\", "/")
        datadir = path.replace("\\", "/")
        content = f"""[mysqladmin]
user = "root"
port = {port}


[mysqld]
port={port}

basedir={basedir}
datadir={datadir}

skip-innodb

character-set-server=utf8
collation-server=utf8_general_ci

default-storage-engine=myisam

sql-mode="STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"

max_connections=100
query_cache_size=0
table_cache=256
tmp_table_size=34M
thread_cache_size=8
myisam_max_sort_file_size=100G
myisam_sort_buffer_size=67M
key_buffer_size=54M
read_buffer_size=64K
read_rnd_buffer_size=256K
sort_buffer_size=256K

max_allowed_packet=32M
"""

        ini_path.write_text(content.strip(), encoding="utf-8")
        return str(ini_path)

    def stop(self):
        if not self._is_running():
            return

        try:
            subprocess.run([self.mysqladmin, f"--port={self.port}", "--user=root", "shutdown"], timeout=3)
        except Exception:
            pass

        if self._is_running():
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

        self.process = None
        self.port = None
        self.datadir = None


def run_test():
    from q2db import Q2Db, Q2DbSchema

    DB_PATH = "test_mysql_data"
    PORT = 3366

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
