import cv2
import mediapipe as mp
import math
import pygame
import numpy as np



pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

def make_tone(freq, duration=0.1, volume=0.3):
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = (np.sin(2 * np.pi * freq * t) * volume * 32767).astype(np.int16)
    wave = np.ascontiguousarray(wave)
    sound = pygame.sndarray.make_sound(wave)
    return sound

current_sound = None

def distance_3d(point1, point2):
    return math.sqrt(
        (point1.x - point2.x)**2 +
        (point1.y - point2.y)**2 +
        (point1.z - point2.z)**2
    )

mp_hands = mp.solutions.hands

mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            thumb_tip = hand.landmark[4]
            index_tip = hand.landmark[8]

            # calculate distance between thumb tip and index tip
            dist = distance_3d(thumb_tip, index_tip)
            # freq = int(200 + (1 - dist) * 800)

            min_d = 0.03
            max_d = 0.3

            t = (dist - min_d) / (max_d - min_d)
            t = max(0.0, min(1.0, t))
            freq = int(200 + t * 800)

            if current_sound:
                current_sound.stop()
            current_sound = make_tone(freq)
            current_sound.play()

            # if dist < 0.05:
            #     print("PERFECT")
            # else:
            #     print("nothing special...")

            # print(f"DISTANCE BETWEEN THE 2 FINGERS: {dist}")
            

            for i, lm in enumerate(hand.landmark):
                h, w, _ = frame.shape
                px, py = int(lm.x * w), int(lm.y * h)
                # print(f"Point {i}: pixel ({px}, {py}), depth z={lm.z:.3f}")

    cv2.imshow("Hand Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
