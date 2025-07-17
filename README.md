project/
├── app.py
├── __init__.py
├── blueprints/
│   ├── annotations.py
│   ├── dashboard.py
├── models/
│   ├── comments.py
├── static/
│   ├── dashboard.js


CREATE TABLE DGM.ICM_COMMENTS (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id VARCHAR2(50) NOT NULL,
    page VARCHAR2(50) NOT NULL,
    text CLOB NOT NULL,
    user VARCHAR2(100) DEFAULT 'Anonymous',
    reason CLOB,
    exclusion CLOB,
    why CLOB,
    quick_fix CLOB,
    to_do CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT SELECT, INSERT, UPDATE, DELETE ON DGM.ICM_COMMENTS TO dgm_user;



CREATE SEQUENCE DGM.ICM_COMMENTS_SEQ START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER DGM.ICM_COMMENTS_TRG
BEFORE INSERT ON DGM.ICM_COMMENTS
FOR EACH ROW
BEGIN
    :NEW.id := DGM.ICM_COMMENTS_SEQ.NEXTVAL;
END;
/

id = db.Column(db.Integer, primary_key=True, autoincrement=False)



import cx_Oracle

# Get 3000 IDs from PROD
prod_conn = cx_Oracle.connect(user="prod_user", password="prod_pass", dsn="prod_dsn")
with prod_conn.cursor() as cur:
    cur.execute("SELECT id FROM prod_table")
    ids_to_exclude = [row[0] for row in cur.fetchall()]
prod_conn.close()

# Load SQL file
with open("sum_excluding_ids.sql", "r") as f:
    sql_template = f.read()

# Generate the CTE for excluded IDs (using bind variables)
cte_rows = "\nUNION ALL\n".join([f"SELECT :{i+1} AS id FROM dual" for i in range(len(ids_to_exclude))])
excluded_ids_cte = f"WITH excluded_ids AS (\n{cte_rows}\n)"

# Replace placeholder in SQL file
final_sql = sql_template.replace("__EXCLUDED_IDS_CTE__", excluded_ids_cte)

# Execute in DEV
dev_conn = cx_Oracle.connect(user="dev_user", password="dev_pass", dsn="dev_dsn")
with dev_conn.cursor() as cur:
    cur.execute(final_sql, ids_to_exclude)
    sum_col1, sum_col2 = cur.fetchone()
    print("Sum of col1:", sum_col1)
    print("Sum of col2:", sum_col2)
dev_conn.close()
