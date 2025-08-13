import oracledb

class OracleTableTransfer:
    def __init__(self, src_config, dst_config, batch_size=100_000):
        self.src_conn = oracledb.connect(**src_config)
        self.dst_conn = oracledb.connect(**dst_config)
        self.batch_size = batch_size

    def transfer_table(self, src_table, dst_table=None):
        """Transfer a single table from source to destination."""
        if dst_table is None:
            dst_table = src_table  # default: same name
        
        src_cursor = self.src_conn.cursor()
        dst_cursor = self.dst_conn.cursor()

        # Get column names dynamically from source
        src_cursor.execute(f"SELECT * FROM {src_table} WHERE ROWNUM = 1")
        col_names = [desc[0] for desc in src_cursor.description]
        placeholders = ", ".join([f":{i+1}" for i in range(len(col_names))])
        insert_sql = f"INSERT INTO {dst_table} ({', '.join(col_names)}) VALUES ({placeholders})"

        # Now fetch and insert in chunks
        src_cursor.execute(f"SELECT * FROM {src_table}")
        total_rows = 0

        while True:
            rows = src_cursor.fetchmany(self.batch_size)
            if not rows:
                break

            dst_cursor.executemany(insert_sql, rows)
            self.dst_conn.commit()
            total_rows += len(rows)
            print(f"[{src_table}] Transferred {len(rows)} rows... Total: {total_rows}")

        src_cursor.close()
        dst_cursor.close()
        print(f"✅ Transfer complete for table: {src_table} ({total_rows} rows)")

    def transfer_multiple_tables(self, table_mapping):
        """
        table_mapping: dict where key=source table name, value=destination table name (or None for same name)
        Example: {"SOURCE_TABLE1": "TARGET_TABLE1", "SOURCE_TABLE2": None}
        """
        for src_table, dst_table in table_mapping.items():
            self.transfer_table(src_table, dst_table)

    def close(self):
        self.src_conn.close()
        self.dst_conn.close()



import oracledb
from concurrent.futures import ProcessPoolExecutor, as_completed

def transfer_single_table(src_config, dst_config, table_pair, batch_size):
    """Worker function to transfer one table in chunks."""
    src_table, dst_table = table_pair
    if dst_table is None:
        dst_table = src_table

    src_conn = oracledb.connect(**src_config)
    dst_conn = oracledb.connect(**dst_config)
    src_cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()

    # Get column names dynamically
    src_cursor.execute(f"SELECT * FROM {src_table} WHERE ROWNUM = 1")
    col_names = [desc[0] for desc in src_cursor.description]
    placeholders = ", ".join([f":{i+1}" for i in range(len(col_names))])
    insert_sql = f"INSERT INTO {dst_table} ({', '.join(col_names)}) VALUES ({placeholders})"

    # Fetch and insert in chunks
    src_cursor.execute(f"SELECT * FROM {src_table}")
    total_rows = 0
    while True:
        rows = src_cursor.fetchmany(batch_size)
        if not rows:
            break
        dst_cursor.executemany(insert_sql, rows)
        dst_conn.commit()
        total_rows += len(rows)

    src_cursor.close()
    dst_cursor.close()
    src_conn.close()
    dst_conn.close()

    return src_table, dst_table, total_rows


class ParallelOracleTransfer:
    def __init__(self, src_config, dst_config, batch_size=100_000, max_workers=4):
        self.src_config = src_config
        self.dst_config = dst_config
        self.batch_size = batch_size
        self.max_workers = max_workers

    def transfer_tables(self, table_mapping):
        """
        table_mapping: dict {source_table: destination_table or None}
        """
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for table_pair in table_mapping.items():
                futures.append(
                    executor.submit(
                        transfer_single_table,
                        self.src_config,
                        self.dst_config,
                        table_pair,
                        self.batch_size
                    )
                )

            for future in as_completed(futures):
                src_table, dst_table, total_rows = future.result()
                print(f"✅ {src_table} → {dst_table}: {total_rows} rows transferred.")

src_config = {
    "user": "src_user",
    "password": "src_pass",
    "dsn": "src_host:1521/src_service"
}

dst_config = {
    "user": "dst_user",
    "password": "dst_pass",
    "dsn": "dst_host:1521/dst_service"
}

transfer = OracleTableTransfer(src_config, dst_config, batch_size=50_000)

# Transfer multiple tables with different names
tables_to_transfer = {
    "CUSTOMERS": "CUSTOMERS_BACKUP",
    "ORDERS": None,  # same name in destination
    "PRODUCTS": "PRODUCTS_2025"
}

transfer.transfer_multiple_tables(tables_to_transfer)
transfer.close()

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    src_config = {
        "user": "src_user",
        "password": "src_pass",
        "dsn": "src_host:1521/src_service"
    }

    dst_config = {
        "user": "dst_user",
        "password": "dst_pass",
        "dsn": "dst_host:1521/dst_service"
    }

    tables_to_transfer = {
        "CUSTOMERS": "CUSTOMERS_BACKUP",
        "ORDERS": None,  # same table name in destination
        "PRODUCTS": "PRODUCTS_2025"
    }

    transfer = ParallelOracleTransfer(src_config, dst_config, batch_size=50_000, max_workers=3)
    transfer.transfer_tables(tables_to_transfer)
