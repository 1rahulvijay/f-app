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
