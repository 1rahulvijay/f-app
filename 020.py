import oracledb
import pandas as pd

class OracleExcelTransfer:
    def __init__(self, src_config, dst_config, excel_path, excel_key, batch_size=100_000):
        self.src_conn = oracledb.connect(**src_config)
        self.dst_conn = oracledb.connect(**dst_config)
        self.batch_size = batch_size
        self.excel_df = pd.read_excel(excel_path)
        self.excel_key = excel_key

    def _table_exists(self, conn, table_name):
        """Check if a table exists in Oracle."""
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", [table_name.upper()])
        exists = cur.fetchone()[0] > 0
        cur.close()
        return exists

    def _create_table_from_columns(self, table_name, columns):
        """Create a table in the destination DB based on column names (all VARCHAR2 by default)."""
        col_defs = [f"{col} VARCHAR2(4000)" for col in columns]
        create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        cur = self.dst_conn.cursor()
        cur.execute(create_sql)
        self.dst_conn.commit()
        cur.close()
        print(f"📦 Created table {table_name} with columns: {', '.join(columns)}")

    def transfer_query_with_excel_join(self, query, join_key, dst_table, how='inner'):
        src_cursor = self.src_conn.cursor()
        dst_cursor = self.dst_conn.cursor()

        # Run the query with limit to get column names
        src_cursor.execute(f"SELECT * FROM ({query}) WHERE ROWNUM = 1")
        col_names = [desc[0] for desc in src_cursor.description]

        # Create table in destination if it doesn't exist
        if not self._table_exists(self.dst_conn, dst_table):
            self._create_table_from_columns(dst_table, col_names)

        # Prepare insert SQL
        placeholders = ", ".join([f":{i+1}" for i in range(len(col_names))])
        insert_sql = f"INSERT INTO {dst_table} ({', '.join(col_names)}) VALUES ({placeholders})"

        # Execute full query for batch processing
        src_cursor.execute(query)
        total_rows = 0

        while True:
            rows = src_cursor.fetchmany(self.batch_size)
            if not rows:
                break

            chunk_df = pd.DataFrame(rows, columns=col_names)

            # Merge with Excel data
            merged_df = chunk_df.merge(self.excel_df, how=how, left_on=join_key, right_on=self.excel_key)

            # Insert merged data
            dst_cursor.executemany(insert_sql, merged_df[col_names].values.tolist())
            self.dst_conn.commit()

            total_rows += len(merged_df)
            print(f"[Query] Inserted {len(merged_df)} rows... Total: {total_rows}")

        src_cursor.close()
        dst_cursor.close()
        print(f"✅ Transfer complete. Total rows inserted: {total_rows}")

    def close(self):
        self.src_conn.close()
        self.dst_conn.close()


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

transfer = OracleExcelTransfer(
    src_config,
    dst_config,
    excel_path="mapping.xlsx",
    excel_key="MAP_KEY",  # column in Excel to join
    batch_size=50_000
)

query = """
SELECT c.customer_id, c.name, o.order_total
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= DATE '2025-01-01'
"""

transfer.transfer_query_with_excel_join(
    query=query,
    join_key="CUSTOMER_ID",  # join column in query result
    dst_table="CUSTOMER_ORDERS_WITH_MAPPING",
    how="outer"  # keep all rows from both query and Excel
)

transfer.close()
