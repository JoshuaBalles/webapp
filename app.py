from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2

app = Flask(__name__)
socketio = SocketIO(app)


def capture_frames():
    camera = cv2.VideoCapture(0)  # Use 0 for the default webcam
    # Get the default resolutions
    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # Emit the resolution to the frontend
    socketio.emit("video_resolution", {"width": width, "height": height})

    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                _, buffer = cv2.imencode(".jpg", frame)
                socketio.emit("video_frame", buffer.tobytes())
    except Exception as e:
        print(f"Error capturing video: {e}")
    finally:
        camera.release()


@app.route("/")
def home():
    return render_template("index.html")


@socketio.on("start_video")
def handle_start_video():
    capture_frames()


if __name__ == "__main__":
    socketio.run(app, debug=True)
