import oracledb
import pandas as pd

class OracleExcelTransfer:
    def __init__(self, src_config, dst_config, excel_path, excel_key, batch_size=100_000):
        self.src_conn = oracledb.connect(**src_config)
        self.dst_conn = oracledb.connect(**dst_config)
        self.batch_size = batch_size
        self.excel_df = pd.read_excel(excel_path)
        self.excel_key = excel_key

    def transfer_with_excel_join(self, src_table, join_key, dst_table=None, how='inner'):
        if dst_table is None:
            dst_table = src_table

        src_cursor = self.src_conn.cursor()
        dst_cursor = self.dst_conn.cursor()

        # Get column names dynamically from source
        src_cursor.execute(f"SELECT * FROM {src_table} WHERE ROWNUM = 1")
        col_names = [desc[0] for desc in src_cursor.description]

        # Insert placeholders
        placeholders = ", ".join([f":{i+1}" for i in range(len(col_names))])
        insert_sql = f"INSERT INTO {dst_table} ({', '.join(col_names)}) VALUES ({placeholders})"

        # Fetch data in batches
        src_cursor.execute(f"SELECT * FROM {src_table}")
        total_rows = 0

        while True:
            rows = src_cursor.fetchmany(self.batch_size)
            if not rows:
                break

            # Convert chunk to DataFrame
            chunk_df = pd.DataFrame(rows, columns=col_names)

            # Merge with Excel data
            merged_df = chunk_df.merge(self.excel_df, how=how, left_on=join_key, right_on=self.excel_key)

            # Insert merged data
            dst_cursor.executemany(insert_sql, merged_df.values.tolist())
            self.dst_conn.commit()

            total_rows += len(merged_df)
            print(f"[{src_table}] Processed & inserted {len(merged_df)} rows... Total: {total_rows}")

        src_cursor.close()
        dst_cursor.close()
        print(f"✅ Transfer complete for table: {src_table} ({total_rows} rows)")

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
    excel_path="lookup_data.xlsx",
    excel_key="Excel_Column_Name",
    batch_size=50_000
)

# Join source table column "CUSTOMER_ID" with Excel column "Excel_Column_Name"
transfer.transfer_with_excel_join("CUSTOMERS", join_key="CUSTOMER_ID", dst_table="CUSTOMERS_WITH_EXTRA")
transfer.close()
