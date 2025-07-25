from datetime import datetime
from __init__ import db

class Comment(db.Model):
    __tablename__ = 'ICM_COMMENTS'
    __table_args__ = {'schema': 'DGM'}

    id = db.Column(db.Integer, primary_key=True)
    chart_id = db.Column(db.String(50), nullable=False)
    page = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    user = db.Column(db.String(100), default='Anonymous')
    reason = db.Column(db.Text)
    exclusion = db.Column(db.Text)
    why = db.Column(db.Text)
    quick_fix = db.Column(db.Text)
    to_do = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
