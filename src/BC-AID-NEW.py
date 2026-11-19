import cv2
import mediapipe as mp
import serial
import time
#import pyttsx3
import os
import numpy as np
from collections import deque
import statistics
import tkinter as tk
from threading import Thread

def send_gsm_alert():
    global arduino

    print("Sending GSM Alert...")

    arduino.write(b'E')
    arduino.flush()

    print("Sent to Arduino: E")

    # 🔥 Wait a bit for GSM to start responding
    time.sleep(2)

    # 🔥 Read GSM responses coming from Arduino
    start_time = time.time()
    while time.time() - start_time < 6:   # read for ~6 seconds
        if arduino.in_waiting:
            try:
                line = arduino.readline().decode(errors='ignore').strip()
                if line:
                    print("GSM:", line)
            except:
                pass

    # 🔥 Keep your original delay (IMPORTANT)
    time.sleep(6)

# ------------- TTS -------------
#tts = pyttsx3.init()
import threading
import queue

speech_queue = queue.Queue()

'''def speech_worker():
    engine = pyttsx3.init()
    while True:
        text = speech_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()
speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()
'''

def speak(text):
    global emergency_monitoring_enabled

    # 🚫 BLOCK SPEECH DURING EMERGENCY MODE
    if emergency_monitoring_enabled:
        print("Speech blocked (Emergency mode ON)")
        return

    try:
        os.system(
            f'powershell -Command "Add-Type -AssemblyName System.Speech; '
            f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            f'$speak.Speak(\'{text}\');"'
        )
    except Exception as e:
        print("Speech error:", e)

# ------------- Arduino Setup -------------
try:
    arduino = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)
except Exception as e:
    print(f"Error connecting to Arduino: {e}")
    arduino = None

def send_arduino(cmd_byte):
    global last_arduino_cmd_time
    now = time.time()

    if arduino is None:
        print(f"[SIM] Arduino command: {cmd_byte}")
        #last_arduino_cmd_time = now
        return
    if now - last_arduino_cmd_time >= ARDUINO_CMD_COOLDOWN:
        try:
            #arduino.write(cmd_byte if not isinstance(cmd_byte, str) else cmd_byte.encode())
            command = cmd_byte.decode() if isinstance(cmd_byte, bytes) else cmd_byte
            arduino.write((command + '\n').encode())   # ✅ newline IMPORTANT
            print("Sent to Arduino:", command)
            last_arduino_cmd_time = now
        except Exception as e:
            print("Arduino write error:", e)

# ------------- Parameters and States -------------
EAR_THRESHOLD = 0.42
EMERGENCY_EAR_THRESHOLD = 0.30
CONSEC_FRAMES_FOR_BLINK = 3
CONSEC_FRAMES_FOR_EMERGENCY = 65  # Approx 2 seconds at 30fps
DOUBLE_BLINK_MIN_GAP = 0.15
DOUBLE_BLINK_MAX_GAP = 0.8
BLINK_DEBOUNCE = 0.4
TOGGLE_COOLDOWN = 1.0
ARDUINO_CMD_COOLDOWN = 0.35

FACE_ON_THRESHOLD = 0.58
FACE_OFF_THRESHOLD = 0.42
FACE_CENTER_HISTORY = 5
EAR_HISTORY = 5

FAN_UP_THRESHOLD = 0.33
FAN_DOWN_THRESHOLD = 0.58
FAN_ON_CMD = b'2'
FAN_OFF_CMD = b'3'

last_spoken_option = None
system_initialized = False

EMERGENCY_ALERT_COOLDOWN = 20  # seconds
from collections import deque

gaze_history = deque(maxlen=9)
STABLE_GAZE_REQUIRED = 5
fan_state = False
led_state = False
blink_timestamps = deque(maxlen=4)
control_enabled = False
eye_closed_frames = 0
emergency_eye_frames = 0
last_blink_registered = 0.0
last_toggle_time = 0.0
last_arduino_cmd_time = 0.0
last_emergency_alert_time = 0.0

last_spoken_option = None

last_print_time = 0
PRINT_INTERVAL = 1.0   # seconds

# ------------- Communication options (TTS) -------------

options = [
    "I need water",
    "I am in pain",
    "Please call the nurse",
    "Please adjust my position",
    "I feel cold",
    "I feel difficulty in breathing"
]

current_option_index = 0
buttons = []

# Gaze + long blink
GAZE_SWITCH_COOLDOWN = 1.2      # seconds between selection moves
LONG_BLINK_SECONDS = 1.5

last_gaze_switch_time = 0.0
long_blink_active = False
long_blink_start_time = 0.0


# NEW: emergency mode flag
emergency_monitoring_enabled = False

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [263, 387, 385, 362, 380, 373]
INNER_BROW = [21, 22]
NOSE_TIP = 1
MOUTH_UPPER = 13
MOUTH_LOWER = 14

face_center_history = deque(maxlen=FACE_CENTER_HISTORY)
ear_history = deque(maxlen=EAR_HISTORY)

def euclidean_dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def eye_aspect_ratio(landmarks, eye_indices, frame_w, frame_h):
    pts = []
    for idx in eye_indices:
        lm = landmarks.landmark[idx]
        pts.append((lm.x * frame_w, lm.y * frame_h))
    p1 = pts[1]
    p2 = pts[2]
    p3 = pts[4]
    p4 = pts[5]
    p5 = pts[0]
    p6 = pts[3]
    vertical1 = euclidean_dist(p2, p4)
    vertical2 = euclidean_dist(p1, p3)
    horizontal = euclidean_dist(p5, p6) + 1e-6
    return (vertical1 + vertical2) / (2.0 * horizontal)

def brow_furrow(landmarks, frame_w, frame_h):
    brow_left = landmarks.landmark[INNER_BROW[0]]
    brow_right = landmarks.landmark[INNER_BROW[1]]
    p1 = (brow_left.x * frame_w, brow_left.y * frame_h)
    p2 = (brow_right.x * frame_w, brow_right.y * frame_h)
    return euclidean_dist(p1, p2)

def mouth_opening(landmarks, frame_w, frame_h):
    upper = landmarks.landmark[MOUTH_UPPER]
    lower = landmarks.landmark[MOUTH_LOWER]
    return abs(upper.y - lower.y) * frame_h

def is_face_forward(landmarks, frame_w, frame_h, threshold=0.12):
    left_eye_y = landmarks.landmark[33].y * frame_h
    right_eye_y = landmarks.landmark[263].y * frame_h
    return abs(left_eye_y - right_eye_y) < (frame_h * threshold)

def estimate_gaze_direction(frame, landmarks, frame_w, frame_h):
    """
    Returns 'LEFT', 'RIGHT' or 'CENTER' based on approximate pupil position.
    Very simple heuristic: looks at vertical strips in the eye region.
    """

    def eye_roi(eye_indices):
        xs, ys = [], []
        for idx in eye_indices:
            lm = landmarks.landmark[idx]
            xs.append(int(lm.x * frame_w))
            ys.append(int(lm.y * frame_h))
        x_min, x_max = max(min(xs) - 3, 0), min(max(xs) + 3, frame_w - 1)
        y_min, y_max = max(min(ys) - 3, 0), min(max(ys) + 3, frame_h - 1)
        return x_min, y_min, x_max, y_max

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Left eye ROI
    lx1, ly1, lx2, ly2 = eye_roi(LEFT_EYE)
    left_eye_img = gray[ly1:ly2, lx1:lx2]

    # Right eye ROI
    rx1, ry1, rx2, ry2 = eye_roi(RIGHT_EYE)
    right_eye_img = gray[ry1:ry2, rx1:rx2]

    def eye_position(eye_img):
        if eye_img.size == 0:
            return "CENTER"
        eye_img = cv2.resize(eye_img, (60, 30))
        _, th = cv2.threshold(eye_img, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        h, w = th.shape
        left_part = th[:, 0:w//3]
        center_part = th[:, w//3:2*w//3]
        right_part = th[:, 2*w//3:w]

        left_val = np.sum(left_part)
        center_val = np.sum(center_part)
        right_val = np.sum(right_part)

        if left_val > center_val and left_val > right_val:
            return "LEFT"
        elif right_val > center_val and right_val > left_val:
            return "RIGHT"
        else:
            return "CENTER"

    pos_left = eye_position(left_eye_img)
    pos_right = eye_position(right_eye_img)

    if pos_left == pos_right:
        return pos_left
    return "CENTER"

def highlight_selected():
    global buttons, current_option_index

    for i, btn in enumerate(buttons):
        if i == current_option_index:
            btn.config(bg="yellow", fg="black")
        else:
            btn.config(bg="gray20", fg="white")

def start_ui():
    global root, buttons

    root = tk.Tk()
    root.title("GC-AID Communication Panel")
    root.geometry("600x450")
    root.configure(bg="black")

    title = tk.Label(
        root,
        text="Patient Communication",
        font=("Arial", 20, "bold"),
        bg="black",
        fg="white"
    )
    title.pack(pady=15)

    buttons = []
    
    frame = tk.Frame(root, bg="black")
    frame.pack(pady=20)

    buttons = []

    cols = 3   # number of columns
    rows = 2   # since you have 6 options

    for index, text in enumerate(options):
        btn = tk.Label(
            frame,
            text=text,
            font=("Arial", 13, "bold"),
            bg="gray20",
            fg="white",
            width=25,
            height=3,
            relief="raised",
            bd=3
        )

        row = index // cols
        col = index % cols

        btn.grid(row=row, column=col, padx=15, pady=15)
        buttons.append(btn)

    highlight_selected()
    root.mainloop()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
cap = cv2.VideoCapture(0)
ui_thread = Thread(target=start_ui)
ui_thread.daemon = True
ui_thread.start()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        frame_h, frame_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        now = time.time()
        blink_text = f"BlinkCount: {len(blink_timestamps)}"
        control_status_text = "Control: ON" if control_enabled else "Control: OFF"

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]

            if not is_face_forward(landmarks, frame_w, frame_h):
                eye_closed_frames = 0
                cv2.putText(frame, "Turn face forward for blink control", (30, frame_h - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 80, 255), 2)
                cv2.imshow("BC-AID Home Automation", frame)

                # KEY HANDLING EVEN WHEN FACE NOT FORWARD
                key = cv2.waitKey(1) & 0xFF
                if key == ord('e'):
                    emergency_monitoring_enabled = not emergency_monitoring_enabled
                    print("Emergency monitoring:", emergency_monitoring_enabled)
                if key == 27:
                    break
                continue

            # Feature extraction
            ear_left = eye_aspect_ratio(landmarks, LEFT_EYE, frame_w, frame_h)
            ear_right = eye_aspect_ratio(landmarks, RIGHT_EYE, frame_w, frame_h)
            ear_avg = (ear_left + ear_right) / 2.0
            ear_history.append(ear_avg)
            ear_smoothed = statistics.median(ear_history)
            brow_dist = brow_furrow(landmarks, frame_w, frame_h)
            mouth_dist = mouth_opening(landmarks, frame_w, frame_h)

            #print(f"EAR: {ear_smoothed:.3f}, BrowDist: {brow_dist:.1f}, MouthDist: {mouth_dist:.1f}, "
                  #f"EmergMode: {emergency_monitoring_enabled}")
            
            # --- Gaze estimation and option navigation ---
            gaze_dir = estimate_gaze_direction(frame, landmarks, frame_w, frame_h)
            gaze_history.append(gaze_dir)

            stable_gaze = None

            if gaze_history.count("LEFT") >= STABLE_GAZE_REQUIRED:
                stable_gaze = "LEFT"
            elif gaze_history.count("RIGHT") >= STABLE_GAZE_REQUIRED:
                stable_gaze = "RIGHT"
            #print("Gaze detected:", gaze_dir)

            if now - last_print_time >= PRINT_INTERVAL:
                print("\n--- STATUS UPDATE ---")
                print(f"EAR: {ear_smoothed:.3f}")
                print(f"BrowDist: {brow_dist:.1f}")
                print(f"MouthDist: {mouth_dist:.1f}")
                print(f"Gaze: {gaze_dir}")
                print(f"Emergency Mode: {emergency_monitoring_enabled}")
                print(f"Selected Option: {options[current_option_index]}")

                last_print_time = now
            cv2.putText(frame, f"Gaze: {gaze_dir}", (30, 220),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            #global last_gaze_switch_time, current_option_index
            if not long_blink_active:
                if stable_gaze and (now - last_gaze_switch_time > GAZE_SWITCH_COOLDOWN):

                    #previous_index = current_option_index

                    if stable_gaze == "LEFT":
                        current_option_index = (current_option_index - 1) % len(options)

                    elif stable_gaze == "RIGHT":
                        current_option_index = (current_option_index + 1) % len(options)

                    # Update UI safely
                    if 'root' in globals() and root is not None:
                        root.after(0, highlight_selected)
                    
                    # 🟢 Speak ONLY if index actually changed AND system initialized (prevents startup speech)
                    '''if (system_initialized and 
                        current_option_index != previous_index and
                        options[current_option_index] != last_spoken_option):  # Prevent repeats
                        
                        speak(options[current_option_index])
                        last_spoken_option = options[current_option_index]  # Track last spoken
                    '''
                    #system_initialized = True  # Set after first valid switch
                    last_gaze_switch_time = now
                    gaze_history.clear()  # Reset history after action
                            

            # Emergency detection ONLY if monitoring enabled
            if emergency_monitoring_enabled:
                emergency_detected = False
                if ear_smoothed < EMERGENCY_EAR_THRESHOLD:
                    emergency_eye_frames += 1
                else:
                    emergency_eye_frames = 0
                if emergency_eye_frames >= CONSEC_FRAMES_FOR_EMERGENCY:
                    emergency_detected = True
                if brow_dist < 32:
                    emergency_detected = True
                if mouth_dist > 10:
                    emergency_detected = True
                if emergency_detected and (now - last_emergency_alert_time > EMERGENCY_ALERT_COOLDOWN):
                    print("EMERGENCY Detected! Sending alerts...")
                    last_emergency_alert_time = now
                    send_gsm_alert()
            else:
                emergency_eye_frames = 0  # reset when not monitoring

            # Blink detection gated by face forward
            if ear_smoothed < EAR_THRESHOLD:
                eye_closed_frames += 1
            else:
                if eye_closed_frames >= CONSEC_FRAMES_FOR_BLINK:
                    if now - last_blink_registered > BLINK_DEBOUNCE:
                        blink_timestamps.append(now)
                        last_blink_registered = now
                        if len(blink_timestamps) >= 2:
                            t1 = blink_timestamps[-2]
                            t2 = blink_timestamps[-1]
                            gap = t2 - t1
                            if DOUBLE_BLINK_MIN_GAP <= gap <= DOUBLE_BLINK_MAX_GAP:
                                if now - last_toggle_time >= TOGGLE_COOLDOWN:
                                    control_enabled = not control_enabled
                                    last_toggle_time = now
                                    blink_timestamps.clear()
                                    if control_enabled:
                                        speak("Light and Fan control ON")
                                        print("Light and Fan control enabled")
                                        if led_state:
                                            send_arduino(b'1')
                                        if fan_state:
                                            send_arduino(FAN_ON_CMD)
                                    else:
                                        speak("Light and Fan control OFF")
                                        print("Light and Fan control disabled")
                            else:
                                if gap < DOUBLE_BLINK_MIN_GAP:
                                    blink_timestamps.pop(-2)
                                elif gap > DOUBLE_BLINK_MAX_GAP:
                                    blink_timestamps.clear()
                                    blink_timestamps.append(t2)
                eye_closed_frames = 0
            
            # --- Long blink detection (3 seconds) for option selection ---
            #global long_blink_active, long_blink_start_time
            # --- Improved Long Blink Detection ---
            # --- Clean Long Blink Detection ---
            # --- Clean Repeatable Long Blink Detection ---

            if ear_smoothed < EAR_THRESHOLD:

                # If eyes just closed → start timer
                if not long_blink_active:
                    long_blink_active = True
                    long_blink_start_time = now

                # If eyes still closed → check duration
                elif long_blink_active and (now - long_blink_start_time >= LONG_BLINK_SECONDS):
                    
                    selected_sentence = options[current_option_index]
                    print("Selected:", selected_sentence)
                    if not emergency_monitoring_enabled:
                        speak(selected_sentence)

                    # Prevent repeated speaking while still closed
                    long_blink_active = False
                    long_blink_start_time = 0
                    gaze_history.clear()  # prevent immediate shift


            else:
                # Eyes opened again → reset completely
                if long_blink_active:
                    long_blink_active = False
                    long_blink_start_time = 0


            
            # Device controls only if control enabled
            if control_enabled:
                left_x = landmarks.landmark[33].x
                right_x = landmarks.landmark[263].x
                face_center = (left_x + right_x) / 2.0
                face_center_history.append(face_center)
                face_center_smoothed = sum(face_center_history) / len(face_center_history)
                cv2.putText(frame, f"FaceCenter:{face_center_smoothed:.3f}", (30, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                if face_center_smoothed > FACE_ON_THRESHOLD and not led_state:
                    send_arduino(b'1')
                    led_state = True
                    print("Light ON")
                elif face_center_smoothed < FACE_OFF_THRESHOLD and led_state:
                    send_arduino(b'0')
                    led_state = False
                    print("Light OFF")
                nose_y = landmarks.landmark[NOSE_TIP].y
                if not fan_state and nose_y < FAN_UP_THRESHOLD:
                    send_arduino(FAN_ON_CMD)
                    fan_state = True
                    print("Fan ON (head up)")
                elif fan_state and nose_y > FAN_DOWN_THRESHOLD:
                    send_arduino(FAN_OFF_CMD)
                    fan_state = False
                    print("Fan OFF (head down)")
                cv2.putText(frame, f"Fan:{'ON' if fan_state else 'OFF'}", (30, 190),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 250), 2)
            else:
                cv2.putText(frame, "Fan:---", (30, 190),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        else:
            if control_enabled:
                control_enabled = False
                speak("Light and Fan control OFF")
                print("Light and Fan control disabled (no face)")

        cv2.putText(frame, blink_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0) if control_enabled else (0, 0, 255), 2)
        cv2.putText(frame, control_status_text, (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0) if control_enabled else (0, 0, 255), 2)

        # Show emergency mode on screen
        cv2.putText(frame, f"EmergMode: {'ON' if emergency_monitoring_enabled else 'OFF'}",
                    (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 255) if emergency_monitoring_enabled else (150, 150, 150), 2)
        
                # --- Draw communication options on screen ---
        y0 = 260
        


        cv2.imshow("BC-AID Home Automation", frame)
        

        # Global key handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('e'):
            emergency_monitoring_enabled = not emergency_monitoring_enabled
            print("Emergency monitoring:", emergency_monitoring_enabled)
        if key == 27:
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()
