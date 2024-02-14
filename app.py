from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
from threading import Thread, Event

app = Flask(__name__)
socketio = SocketIO(app)

stop_event = Event()


def capture_frames():
    camera = cv2.VideoCapture(0)  # Use 0 for the default webcam

    # Optional: Adjust default resolution
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Emit the resolution to the frontend
    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    socketio.emit("video_resolution", {"width": width, "height": height})

    frame_skip = 2  # Skip every 'n' frames to reduce load (0 = no skip)

    try:
        while not stop_event.is_set():
            for _ in range(frame_skip):
                camera.grab()

            success, frame = camera.read()
            if not success:
                break

            # Adjust JPEG quality here (1-100, higher means better quality)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            _, buffer = cv2.imencode(".jpg", frame, encode_param)

            socketio.emit("video_frame", buffer.tobytes())
    except Exception as e:
        print(f"Error capturing video: {e}")
    finally:
        camera.release()


def start_capture():
    stop_event.clear()
    Thread(target=capture_frames).start()


def stop_capture():
    stop_event.set()


@app.route("/")
def home():
    return render_template("index.html")


@socketio.on("start_video")
def handle_start_video():
    start_capture()


if __name__ == "__main__":
    socketio.run(app, debug=True)
