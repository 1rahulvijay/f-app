from .. import db
from sqlalchemy.sql import func

class Comment(db.Model):
    __tablename__ = 'comments'
    __table_args__ = {'extend_existing': True}  # Allow redefinition of table

    id = db.Column(db.Integer, primary_key=True)
    chart_id = db.Column(db.String(50), nullable=False)
    page = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)  # Maps to Oracle CLOB
    user = db.Column(db.String(100), default='Anonymous')
    reason = db.Column(db.Text)  # Maps to Oracle CLOB
    exclusion = db.Column(db.Text)  # Maps to Oracle CLOB
    why = db.Column(db.Text)  # Maps to Oracle CLOB
    quick_fix = db.Column(db.Text)  # Maps to Oracle CLOB
    to_do = db.Column(db.Text)  # Maps to Oracle CLOB
    created_at = db.Column(db.DateTime, default=func.current_timestamp())
