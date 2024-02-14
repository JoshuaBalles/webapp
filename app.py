from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
from threading import Thread, Event
import os
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

stop_event = Event()
camera = None


# Initialize the camera when the application starts
def init_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


# Save the current frame asynchronously
def save_current_frame(frame):
    if not os.path.exists("inputs"):
        os.makedirs("inputs")
    timestamp = datetime.now().strftime("%H-%M-%S-%d-%m-%Y")
    filename = f"inputs/{timestamp}.jpg"
    cv2.imwrite(filename, frame)


latest_frame = None


# Capture frames from the camera and emit them to clients
def capture_frames():
    global latest_frame
    init_camera()

    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    socketio.emit("video_resolution", {"width": width, "height": height})

    frame_skip = 2

    try:
        while not stop_event.is_set():
            for _ in range(frame_skip):
                camera.grab()
            success, frame = camera.read()
            if not success:
                break

            latest_frame = frame
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            _, buffer = cv2.imencode(".jpg", frame, encode_param)
            socketio.emit("video_frame", buffer.tobytes())
    except Exception as e:
        print(f"Error capturing video: {e}")


# Start capturing frames
def start_capture():
    stop_event.clear()
    Thread(target=capture_frames).start()


# Stop capturing frames and release the camera resource
def stop_capture():
    stop_event.set()
    if camera is not None:
        camera.release()


@app.route("/")
def home():
    return render_template("index.html")


# Event handler to start video capture
@socketio.on("start_video")
def handle_start_video():
    start_capture()


# Event handler to capture a single image
@socketio.on("capture_image")
def handle_capture_image():
    if latest_frame is not None:
        Thread(target=save_current_frame, args=(latest_frame,)).start()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True)
