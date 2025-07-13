from . import create_app

if __name__ == "__main__":
    app, socketio, logger, engines = create_app()
    # For development only; use Gunicorn in production
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)
