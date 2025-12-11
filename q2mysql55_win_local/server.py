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
        print(self.port)
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
            root = resources.files(__package__)
            return os.path.abspath(str(root / "mysql55_files"))
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


if __name__ == "__main__":
    import sys

    sys.path.append(f"{os.path.dirname(os.path.realpath(__file__))}/..")
    from dev import run_test

    run_test()
