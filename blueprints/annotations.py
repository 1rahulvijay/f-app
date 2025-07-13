from flask import Blueprint, jsonify, request
from flask_socketio import emit
from .. import db, socketio, logger
from ..models.comment import Comment

annotations_bp = Blueprint('annotations', __name__)

@socketio.on('connect', namespace='/annotations')
def handle_connect():
    logger.info("Client connected to /annotations namespace")

@annotations_bp.route('/api/annotations', methods=['GET', 'POST'])
def handle_comments():
    try:
        if request.method == 'POST':
            data = request.json
            if not all(key in data for key in ['chart_id', 'page', 'text']):
                return jsonify({"error": "Missing required fields: chart_id, page, text"}), 400
            if len(data['text'].strip()) == 0:
                return jsonify({"error": "Comment text cannot be empty"}), 400
            if len(data['text']) > 500:
                return jsonify({"error": "Comment text is too long (max 500 characters)"}), 400
            comment = Comment(
                chart_id=data['chart_id'],
                page=data['page'],
                text=data['text'].strip(),
                user=data.get('user', 'Anonymous')[:100],
                reason=data.get('reason'),
                exclusion=data.get('exclusion'),
                why=data.get('why'),
                quick_fix=data.get('quick_fix'),
                to_do=data.get('to_do')
            )
            db.session.add(comment)
            db.session.commit()
            socketio.emit('new_comment', {
                'id': comment.id,
                'chart_id': comment.chart_id,
                'page': comment.page,
                'text': comment.text,
                'user': comment.user,
                'reason': comment.reason,
                'exclusion': comment.exclusion,
                'why': comment.why,
                'quick_fix': comment.quick_fix,
                'to_do': comment.to_do,
                'created_at': comment.created_at.isoformat()
            }, namespace='/annotations')
            return jsonify({"message": "Comment added successfully", "id": comment.id}), 201

        page = request.args.get('page', '/')
        chart_id = request.args.get('chart_id')
        if not chart_id:
            return jsonify({"error": "chart_id is required"}), 400
        comments = Comment.query.filter_by(page=page, chart_id=chart_id).all()
        return jsonify([{
            'id': c.id,
            'chart_id': c.chart_id,
            'page': c.page,
            'text': c.text,
            'user': c.user,
            'reason': c.reason,
            'exclusion': c.exclusion,
            'why': c.why,
            'quick_fix': c.quick_fix,
            'to_do': c.to_do,
            'created_at': c.created_at.isoformat()
        } for c in comments])
    except Exception as e:
        logger.error(f"Error handling comments: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to handle comments"}), 500
