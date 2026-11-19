# Source Code

This folder contains the primary Python implementation of the GC-AID (Gesture-Controlled AI Assistant for Disabled Individuals) project.

The Python application acts as the central processing unit of the system, using computer vision techniques to interpret facial movements, eye gestures, and head position. Based on the detected actions, it performs corresponding operations such as home appliance control, communication assistance, and emergency alert generation.

## Main Functionalities

- **Facial Landmark Detection:** Uses MediaPipe Face Mesh to detect and analyze facial landmarks in real-time.
- **Blink Detection:** Identifies eye blinks and prolonged eye closures for command execution.
- **Gaze Tracking:** Detects gaze direction to navigate through predefined communication options.
- **Gesture-Based Home Automation:** Interprets facial and head movements to control connected devices.
- **Text-to-Speech Communication:** Converts selected sentences into speech to assist users with communication difficulties.
- **Emergency Detection:** Monitors facial indicators of distress and initiates emergency communication when required.
- **Serial Communication:** Communicates with the Arduino microcontroller to control connected hardware.
- **Emergency Notifications:** Integrates communication services to send emergency messages and initiate alerts.

## Technologies Used

- Python
- OpenCV
- MediaPipe
- NumPy
- PySerial
- Text-to-Speech (TTS)
- Twilio API

## System Operation

The application captures video through a webcam and continuously processes facial features. Detected gestures and movements are interpreted as user commands. These commands are then used to control home automation devices, navigate communication options, generate speech, or activate emergency notifications.

## File

- `BC-AID-NEW.py` – Main Python application containing the core logic for facial analysis, gesture recognition, communication, device control, and emergency functionality.

## Purpose

The source code forms the core of GC-AID, integrating computer vision, assistive communication, embedded hardware, and emergency response into a unified system designed to improve accessibility and independence for individuals with limited mobility.
