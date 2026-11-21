# GC-AID
### Gesture-Controlled AI Assistant for Assistive Living

A vision-based assistive system that enables individuals with disabilities to interact with their surroundings using facial gestures, gaze tracking, voice feedback, and gesture-based home automation.

---

##  Overview

GC-AID is an assistive technology project that combines computer vision and hardware automation to provide a hands-free interaction system.

The system uses a webcam to detect facial landmarks and interpret gestures such as blinking and eye movements. These gestures are converted into commands to control connected devices through an Arduino, while voice feedback and emergency communication provide additional assistance.

##  Features

- **Facial Landmark Detection:** Detects facial landmarks using MediaPipe Face Mesh.
- **Gaze Tracking:** Uses eye movements for interaction and navigation.
- **Blink Detection:** Recognizes blinking patterns as control commands.
- **Home Automation:** Controls connected devices such as LEDs and fans using facial gestures.
- **Voice Feedback:** Provides audio feedback through Text-to-Speech.
- **Emergency Communication:** Supports emergency notifications through Twilio integration.
- **Hardware Integration:** Connects Python-based computer vision with Arduino using serial communication.

##  System Architecture

```text
 Webcam
   │
   ▼
 OpenCV + MediaPipe
   │
   ▼
 Facial Landmark Detection
   │
   ▼
 Gesture & Gaze Recognition
   │
   ├──────────────► Text-to-Speech
   │
   ├──────────────► Emergency Communication
   │
   ▼
 Serial Communication
   │
   ▼
 Arduino UNO
   │
   ▼
 LEDs / Fan / Home Appliances
```

##  Technologies Used

**Software:** Python, OpenCV, MediaPipe, NumPy, PySerial, Text-to-Speech, Twilio

**Hardware:** Arduino UNO, Webcam, LED, DC Fan, Driver Circuit, Connecting Wires

##  Project Structure

```text
GC-AID/
├── Arduino/     # Arduino firmware
├── docs/        # Project report and development log
├── images/      # Project screenshots
├── src/         # Main Python application
├── test/        # Testing programs
└── README.md
```

##  Getting Started

### Requirements

- Python 3.x
- Arduino IDE
- Webcam
- Arduino UNO
- Required Python libraries

### Installation

Clone the repository:

```bash
git clone https://github.com/nizam-vyshnavi/GC-AID.git
cd GC-AID
```

Install the required libraries:

```bash
pip install opencv-python mediapipe numpy pyserial
```

Upload the Arduino code from the `Arduino/` folder to your Arduino UNO.

Connect the Arduino and configure the appropriate serial port in the Python application.

Run the main application:

```bash
python src/BC-AID-NEW.py
```

##  Project Demonstration

Screenshots of the project implementation and testing are available in the [`images`](images/) folder.

##  Documentation

Detailed project documentation, including the project report and development log, is available in the [`docs`](docs/) folder.

##  Future Scope

- Improved gesture recognition accuracy
- Additional gesture-based commands
- Integration with more home automation devices
- Improved gaze tracking
- Wireless communication
- Enhanced accessibility and user interface

##  Author

**Nizam Vyshnavi**  
[LinkedIn](linkedin.com/in/nizam-vyshnavi-589b60291)
---

If you find this project interesting, feel free to explore the repository!
