CREATE TABLE comments (
    id NUMBER PRIMARY KEY,
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
CREATE SEQUENCE comment_seq START WITH 1 INCREMENT BY 1;
CREATE TRIGGER comment_trigger
BEFORE INSERT ON comments
FOR EACH ROW
BEGIN
    SELECT comment_seq.NEXTVAL INTO :NEW.id FROM dual;
END;
/
CREATE INDEX idx_comments_page_chart ON comments(page, chart_id);
