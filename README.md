⚠️ Windows-only. Embedded/local use only.
⚠️ Ships MySQL 5.5 binaries for local embedded use
⚠️ Not intended for networked or production servers

# Q2MySQL55_Win_Local_Server

A lightweight, embedded-style **MySQL 5.5 server wrapper for Windows**, bundled inside your Python package.  
Ideal for desktop applications that require a private MySQL instance without requiring the user to install MySQL.

This library:

- Automatically finds `mysqld.exe` and `mysqladmin.exe` inside the package  
- Initializes the **data directory** on first run  
- Generates a minimal `my.ini`  
- Starts MySQL **in detached mode** (does not block Python)  
- Stops MySQL cleanly or forcefully  
- Requires **no admin rights**  
- Works only on **Windows**

---

## ✨ Features

- ✔️ Ships MySQL 5.5 internally  
- ✔️ Auto-creates `my.ini`  
- ✔️ Auto-initializes data directories (`mysql`, `performance_schema`)  
- ✔️ Non-blocking background server start  
- ✔️ Graceful stop using `mysqladmin`  
- ✔️ No external installation required

---

## 🚀 Quick Start

```python
from q2mysql55_win_local_server import Q2MySQL55_Win_Local_Server

DB_PATH = "test_mysql_data"
PORT = 3366

srv = Q2MySQL55_Win_Local_Server()
srv.start(PORT, DB_PATH)
print("Server started.")

# ... your logic ...

srv.stop()
print("Server stopped.")
```

---

## ⚙️ How It Works

### 1. Locating Binaries
The wrapper automatically resolves the folder `mysql55_files` using `importlib.resources`.

### 2. Data Directory Initialization
If missing, the following are copied from the embedded `data/` directory:

- `mysql/`
- `performance_schema/`

### 3. Configuration (`my.ini`)
A minimal config is created automatically in the data directory:

```ini
[mysqld]
port=...
basedir=...
datadir=...
character-set-server=utf8
default-storage-engine=myisam
skip-innodb
```

### 4. Starting the Server
Runs `mysqld.exe` in fully **detached mode** using:

- `DETACHED_PROCESS`
- `CREATE_NEW_PROCESS_GROUP`

This allows the MySQL process to continue running independently.

### 5. Stopping the Server
Shutdown sequence:

1. `mysqladmin --user=root --port=... shutdown`  
2. If server does not exit — terminate the process  
3. As a last resort — kill the process

---

## ⚠️ Requirements

- Windows 10 or later  
- Python 3.9+  
- Bundled MySQL 5.5 distribution in `mysql55_files`

---

## 🔒 Security Notes

- The server uses **root with no password** — do not expose it to any external network.
- Intended only for **local desktop applications**.

---

## 📄 License

MIT
