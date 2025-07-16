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
