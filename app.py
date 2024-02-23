from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Thread, Event
from datetime import datetime
import cv2
import os
from ultralytics import YOLO

app = Flask(__name__)
socketio = SocketIO(app)  # Initialize Flask-SocketIO

stop_event = Event()  # Event to control the stop of the video capturing thread
camera = None  # Global variable for the camera object
latest_frame = None  # To store the most recent frame captured
model = YOLO("best.pt")  # Load the YOLO model once

def init_camera():
    global camera
    # Initialize the camera object only if it hasn't been initialized before
    if camera is None:
        camera = cv2.VideoCapture(0)  # 0 for the default camera

# Create 'outputs' directory to store output images
if not os.path.exists("outputs"):
    os.makedirs("outputs")

def process_frame(frame):
    global model
    results = model(frame)  # Perform object detection on the frame

    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%H-%M-%S-%d-%m-%Y")
    filename = f"{timestamp}.jpg"
    output_path = f"outputs/{filename}"

    # Process each detection result
    for r in results:
        # Plot detection results on the frame
        im_array = r.plot()
        # Save the annotated frame as an image
        cv2.imwrite(output_path, im_array)

def capture_frames():
    global latest_frame
    init_camera()

    # Retrieve video frame width and height and emit to the client-side for appropriate display
    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    socketio.emit("video_resolution", {"width": width, "height": height})

    frame_skip = 2  # Number of frames to skip between processing to reduce workload

    try:
        while not stop_event.is_set():  # Loop until the stop event is triggered
            for _ in range(frame_skip):  # Skip specified number of frames
                camera.grab()
            success, frame = camera.read()
            if not success:
                break  # Exit loop if unable to read from camera

            latest_frame = frame  # Update the global latest_frame
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]  # JPEG quality for the frame encoding
            _, buffer = cv2.imencode(".jpg", frame, encode_param)  # Encode the frame as JPEG
            socketio.emit("video_frame", buffer.tobytes())  # Emit the encoded frame over SocketIO
    except Exception as e:
        print(f"Error capturing video: {e}")  # Log any errors during video capture
    finally:
        if camera is not None:
            camera.release()  # Ensure camera resource is released

def start_capture():
    stop_event.clear()  # Ensure the stop event is cleared before starting capture
    Thread(target=capture_frames).start()  # Start the frame capture in a separate thread

def stop_capture():
    stop_event.set()  # Set the stop event to stop the video capture loop
    if camera is not None:
        camera.release()  # Release the camera resource

@app.route("/")
def home():
    # Render the main page template
    return render_template("index.html")

@socketio.on("start_video")
def handle_start_video():
    start_capture()  # Start video capture when a "start_video" event is received from the client

@socketio.on("capture_image")
def handle_capture_image():
    # Process the latest frame for object detection when "capture_image" event is received
    if latest_frame is not None:
        Thread(target=process_frame, args=(latest_frame,)).start()

if __name__ == "__main__":
    socketio.run(app, debug=True)  # Start the Flask-SocketIO server
