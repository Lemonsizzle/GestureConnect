import webview
from threading import Thread
from app import socketio, app


def start_server():
    socketio.run(app, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    # Create a separate thread that will run your Flask app
    t = Thread(target=start_server)
    t.start()

    # Create a WebView window
    webview.create_window('My Flask App', 'http://localhost:5000')
    webview.start()
