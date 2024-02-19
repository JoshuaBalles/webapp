# Livestock-Learner Web Application (temporary title)

## For: Design of Deep Learning-Based Multi-Object Weight Estimation for Livestock Management

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python**: You must have Python 3.10.11 installed on your machine. If you have multiple versions of Python installed, make sure Python 3.10.11 is set as the primary version in your system's environment path.

## Installation

Follow these steps to get your development environment set up:

1. **Clone the repository**

   ```bash
   git clone <repository link>
   ```

2. **Navigate to the repository directory**

   ```bash
   cd <repository directory>
   ```

3. **Create a Python virtual environment**

   ```bash
   python -m venv .venv
   ```

4. **Activate the virtual environment**

   - On Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - On Unix or MacOS:

     ```bash
     source .venv/bin/activate
     ```

5. **Install the required dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To use the webapp, follow these steps:

1. **Start the application**

   ```bash
   python -m app
   ```

2. **Capture Image**

   - Press the `Capture` button within the webapp to take an image of the current frame.
   - The application will run YOLO inference on the captured image.
   - Results will be saved in the `outputs` folder.
