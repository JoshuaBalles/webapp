from flask import (Flask, render_template)  # Import Flask to create a web server and render_template to serve HTML files
from flask_socketio import (SocketIO)  # Import SocketIO for real-time communication between the server and clients
from threading import (Thread, Event)  # Import Thread for parallel execution and Event for thread synchronization
from datetime import datetime  # Import datetime to generate timestamps
from ultralytics import YOLO  # Import YOLO model from ultralytics for object detection
import cv2  # Import OpenCV for image and video processing
import os  # Import os for file and directory operations

app = Flask(__name__)  # Initialize a Flask application
socketio = SocketIO(app)  # Wrap the Flask app with SocketIO for real-time capabilities

stop_event = Event()  # Create an event to signal when to stop the video capture thread
camera = (None)  # Initialize camera variable to None, to be set when the camera is initialized


# Function to initialize the camera
def init_camera():
    global camera  # Access the global camera variable
    if camera is None:  # Check if the camera has not been initialized
        camera = cv2.VideoCapture(0)  # Open the default camera


# Function to save the current frame and process it with YOLO
def save_current_frame(frame):
    if not os.path.exists("inputs"):  # Check if the 'inputs' directory doesn't exist
        os.makedirs("inputs")  # Create the 'inputs' directory

    timestamp = datetime.now().strftime("%H-%M-%S-%d-%m-%Y")  # Generate a timestamp for the filename
    filename = f"{timestamp}.jpg"  # Create a filename with the timestamp
    input_path = f"inputs/{filename}"  # Define the full path for the input image
    cv2.imwrite(input_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])  # Save the frame to the 'inputs' directory with JPEG quality set to 100

    model = YOLO("best.pt")  # Initialize the YOLO model with the specified weights
    results = model(input_path)  # Perform object detection on the input image

    if not os.path.exists("outputs"):  # Check if the 'outputs' directory doesn't exist
        os.makedirs("outputs")  # Create the 'outputs' directory

    # Assuming the results contain multiple objects, iterate through them
    for r in results:
        im_array = r.plot()  # Generate an annotated image with the detection results
        output_path = f"outputs/{filename}"  # Define the full path for the output image
        cv2.imwrite(output_path, im_array)  # Save the annotated image to the 'outputs' directory


latest_frame = None  # Variable to hold the most recent frame captured from the camera


# Function to capture frames from the camera and emit them to the clients
def capture_frames():
    global latest_frame  # Access the global latest_frame variable
    init_camera()  # Initialize the camera

    # Get the frame dimensions from the camera for the client's video resolution
    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    socketio.emit("video_resolution", {"width": width, "height": height})  # Emit the video resolution to clients

    frame_skip = 2  # Number of frames to skip between captures to reduce load

    try:
        while not stop_event.is_set():  # Loop until the stop event is signaled
            for _ in range(frame_skip):  # Skip the specified number of frames
                camera.grab()
            success, frame = camera.read()  # Read the next frame from the camera
            if (not success):  # If the frame could not be read successfully, exit the loop
                break

            latest_frame = frame  # Update the latest_frame with the current frame
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]  # Set JPEG quality for encoding the frame
            _, buffer = cv2.imencode(".jpg", frame, encode_param)  # Encode the frame as JPEG
            socketio.emit("video_frame", buffer.tobytes())  # Emit the encoded frame to clients
    except Exception as e:
        print(f"Error capturing video: {e}")  # Print any errors that occur during video capture


# Function to start the video capture in a separate thread
def start_capture():
    stop_event.clear()  # Clear the stop event in case it was set previously
    Thread(
        target=capture_frames
    ).start()  # Start the capture_frames function in a new thread


# Function to stop video capture and release the camera resource
def stop_capture():
    stop_event.set()  # Set the stop event to signal the capture_frames thread to stop
    if camera is not None:  # If the camera has been initialized
        camera.release()  # Release the camera resource


# Flask route for the home page
@app.route("/")
def home():
    return render_template("index.html")  # Serve the index.html file as the home page


# SocketIO event handler to start video capture
@socketio.on("start_video")
def handle_start_video():
    start_capture()  # Call the start_capture function


# SocketIO event handler to capture a single image
@socketio.on("capture_image")
def handle_capture_image():
    if latest_frame is not None:  # If there is a latest frame available
        # Start the save_current_frame function in a new thread, passing the latest frame
        Thread(target=save_current_frame, args=(latest_frame,)).start()


# Main entry point for the Flask application
if __name__ == "__main__":
    socketio.run(
        app, host="0.0.0.0", debug=True
    )  # Run the Flask app with SocketIO on host 0.0.0.0
