
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import json

# Initialize mediapipe hand detector
mp_hands = mp.solutions.hands
hand_detector = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)
mp_drawing = mp.solutions.drawing_utils





# Screen size


screen_width, screen_height = pyautogui.size()

# Smoothing factor for cursor movement
smoothening = 5
prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0

# Scroll sensitivity







scroll_speed = 50

# Configuration for low resource mode
low_resource_mode = False

# Function to load settings
def load_settings():
    global smoothening, scroll_speed
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            smoothening = settings.get('smoothing', 5)
            scroll_speed = settings.get('scroll_sensitivity', 50)
    except FileNotFoundError:
        pass

# Function to save settings
def save_settings():
    settings = {
        'smoothing': smoothening,
        'scroll_sensitivity': scroll_speed
    }
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

# Load saved settings on startup
load_settings()

# Capture video from webcam
cap = cv2.VideoCapture(0)
p_time = 0  # Used for calculating FPS

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process hand landmarks
    output = hand_detector.process(rgb_frame)
    hands = output.multi_hand_landmarks

    # Drawing landmarks and detecting gestures
    if hands:
        # Use the first hand for controlling the mouse (can be modified for multi-hand control)
        controlling_hand = hands[0]
        mp_drawing.draw_landmarks(frame, controlling_hand, mp_hands.HAND_CONNECTIONS)
        landmarks = controlling_hand.landmark

        # Coordinates of fingertips
        thumb_tip = landmarks[4]
        index_finger_tip = landmarks[8]
        middle_finger_tip = landmarks[12]
        ring_finger_tip = landmarks[16]
        pinky_tip = landmarks[20]

        # Convert the landmark positions to pixel values on the screen
        thumb_x = int(thumb_tip.x * frame_width)
        thumb_y = int(thumb_tip.y * frame_height)
        index_x = int(index_finger_tip.x * frame_width)
        index_y = int(index_finger_tip.y * frame_height)
        middle_x = int(middle_finger_tip.x * frame_width)
        middle_y = int(middle_finger_tip.y * frame_height)
        ring_x = int(ring_finger_tip.x * frame_width)
        ring_y = int(ring_finger_tip.y * frame_height)
        pinky_x = int(pinky_tip.x * frame_width)
        pinky_y = int(pinky_tip.y * frame_height)

        # Convert to screen coordinates for mouse control
        screen_index_x = np.interp(index_finger_tip.x * frame_width, (0, frame_width), (0, screen_width))
        screen_index_y = np.interp(index_finger_tip.y * frame_height, (0, frame_height), (0, screen_height))

        # Adjust smoothing dynamically based on speed of hand movement
        movement_speed = np.sqrt((screen_index_x - prev_x) ** 2 + (screen_index_y - prev_y) ** 2)
        dynamic_smoothing = np.interp(movement_speed, [0, 100], [15, 5])
        curr_x = prev_x + (screen_index_x - prev_x) / dynamic_smoothing
        curr_y = prev_y + (screen_index_y - prev_y) / dynamic_smoothing

        # Move the cursor
        pyautogui.moveTo(curr_x, curr_y)

        # Update previous coordinates
        prev_x, prev_y = curr_x, curr_y

        # Draw circles on fingertips
        cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 0, 0), cv2.FILLED)
        cv2.circle(frame, (index_x, index_y), 10, (0, 255, 0), cv2.FILLED)
        cv2.circle(frame, (middle_x, middle_y), 10, (0, 0, 255), cv2.FILLED)
        cv2.circle(frame, (ring_x, ring_y), 10, (255, 255, 0), cv2.FILLED)
        cv2.circle(frame, (pinky_x, pinky_y), 10, (255, 0, 255), cv2.FILLED)

        # **Left Click Gesture** - Index and Thumb close together
        if abs(index_y - thumb_y) < 20:
            cv2.putText(frame, 'Left Click', (index_x, index_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            pyautogui.click()  # Left click

        # **Right Click Gesture** - Middle Finger and Thumb close together
        if abs(middle_y - thumb_y) < 20:
            cv2.putText(frame, 'Right Click', (middle_x, middle_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            pyautogui.click(button='right')  # Right click

        # **Enter Key Gesture** - Thumb and Pinky Finger close together
        if abs(thumb_y - pinky_y) < 20:
            cv2.putText(frame, 'Enter', (thumb_x, thumb_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            pyautogui.press('enter')  # Press Enter key

        # **Scroll Up Gesture** - Thumb higher than Ring Finger with a pinch gesture
        if abs(thumb_y - ring_y) < 30 and thumb_y < ring_y:
            pyautogui.scroll(scroll_speed)  # Scroll up
            cv2.putText(frame, 'Scroll Up', (thumb_x, thumb_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # **Scroll Down Gesture** - Thumb lower than Ring Finger with a pinch gesture
        elif abs(thumb_y - ring_y) < 30 and thumb_y > ring_y:
            pyautogui.scroll(-scroll_speed)  # Scroll down
            cv2.putText(frame, 'Scroll Down', (thumb_x, thumb_y - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # Display FPS (Frames Per Second)
    c_time = time.time()
    fps = 1 / (c_time - p_time)
    p_time = c_time
    cv2.putText(frame, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 2)

    # Instructions for exiting
    cv2.putText(frame, 'Press "q" to Quit', (20, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Show the final frame
    cv2.imshow('Virtual Mouse AI', frame)

    # Toggle low resource mode
    if low_resource_mode:
        time.sleep(0.05)  # Limit frame rate to reduce resource usage

    # Break the loop if 'q' is pressed
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Save settings on exit
save_settings()

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
