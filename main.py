import cv2
import mediapipe as mp
import math
import pygame
import numpy as np
import serial
import time


ser = serial.Serial("/dev/ttyACM0", 9600)
time.sleep(2)
# dist_sonar = float(ser.readline().decode("utf-8").strip())
dist_sonar = 50



pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
touching = False


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

def calc_dist_coeff(dist_cm):
    min_dist = 0
    max_dist = 70
    return (1 - (dist_cm / (max_dist - min_dist)))


mp_hands = mp.solutions.hands

mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

while dist_sonar > 15:
    print(f"Distance: {dist_sonar}")
    try:
        dist_sonar = float(ser.readline().decode("utf-8").strip())
        coeff = calc_dist_coeff(dist_sonar)
        print(f"Coeff: {coeff}")
    except ValueError:
        pass

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]
    # print(f"FRAME COORDS: height:{frame_height}, width:{frame_width}")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    try:
        dist_sonar = float(ser.readline().decode("utf-8").strip())
        print(f"DISTANCE: {dist_sonar}")
    except ValueError:
        pass
    coeff = calc_dist_coeff(dist_sonar)
    print(f"COEFF: {coeff}")
    # no1 = max(int(200 * coeff), 10)
    no1 = 40
    no2 = max(int(600 * coeff), 35)
    corner_sq1: tuple = (no1, no1)
    corner_sq2: tuple = (no1, no2)
    corner_sq3: tuple = (no2, no2)
    corner_sq4: tuple = (no2, no1)
    ccolor = (255, 70, 20)
    if not touching:
        cv2.line(frame, corner_sq1, corner_sq2, ccolor, 5)
        cv2.line(frame, corner_sq2, corner_sq3, ccolor, 5)
        cv2.line(frame, corner_sq3, corner_sq4, ccolor, 5)
        cv2.line(frame, corner_sq4, corner_sq1, ccolor, 5)
    


    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)      

            thumb_tip = hand.landmark[4]
            thumb_tip_x = thumb_tip.x*frame_width
            thumb_tip_y = thumb_tip.y*frame_height

            index_tip = hand.landmark[8]
            index_tip_x = index_tip.x*frame_width
            index_tip_y = index_tip.y*frame_height
            
            
            pinky_tip = hand.landmark[20]
            pinky_tip_x = pinky_tip.x*frame_width
            pinky_tip_y = pinky_tip.y*frame_height
            
            wrist = hand.landmark[0]
            wrist_x = wrist.x*frame_width
            wrist_y = wrist.y*frame_height


            # ok as first test lets just do the coords track fingers only while theyre touching each other

            dist_pinky_index = distance_3d(thumb_tip, index_tip)
            # need to define a radius that will be the "hitbox" of the 2 touching fingers.
            # when they touch, im thinking the middle should be just one coord minus the other coord to get the distance and divide by 2.
            # this distance divided by 2 will still neeed to be located but thats the first step.
            dist_to_circle_center = dist_pinky_index / 2
            # now we have a variable that is the distance from one finger to the middle. Need to get the direction to, hmm.
            # lets try just adding this to one of the fingers, maybe itll work
            center_x = int(index_tip_x + dist_to_circle_center)
            center_y = int(index_tip_y + dist_to_circle_center)
            center_z = int(index_tip.z)
            

            # print(f"DIST PINKY INDEX: {dist_pinky_index}")
            touching_top_brdr = False
            touching_bottom_brdr = False
            touching_left_brdr = False
            touching_right_brdr = False
            touching_square = touching_top_brdr or touching_bottom_brdr or touching_left_brdr or touching_right_brdr
            if dist_pinky_index > 0.1:
                touching = False
            else:
                center = (int(center_x), int(center_y))
                # print(f"THIS THIS: center_y: {type(center_y)}\ndist_to_cricel_Center: {dist_to_circle_center}\ncenter: {center}")
            # center_z = index_tip_z + dist_to_circle_center
            
                cv2.circle(frame, center, 25, ccolor, -1)

            # perfect so that's the hitbox, will later make non-colored by simply removing the drawn circle
            
            # now its time to get every single point of this square. So we have its 4 corners in absolute coords.
            # instead of collecting points, lets just do  a conditional.
            # draw basically a capsule around the square's sides to give a margin to grab
            # if fingers x is more than no1 - 5 and less than no1 + 5 .....
                radius = 30
                # print(f"no1 - radius {no1 - radius}")
                # print(f"center[0]: {center[0]}")
                # print(f"center[1]: {center[1]}")
                # print(f"no1 + radius: {no1 + radius}")
                # print(f"no2 - radius: {no2 - radius}")
                # print(f"no2 + radius: {no2 + radius}")
                above_top_brdr = center[1] > no1 + radius
                below_top_brdr = center[1] < no1 - radius
                above_bottom_brdr = center[1] > no2 + radius
                below_bottom_brdr = center[1] < no2 - radius

                left_of_left_brdr = center[0] < no1 - radius
                right_of_left_brdr = center[0] > no1 + radius

                left_of_right_brdr = center[0] < no2 - radius
                right_of_right_brdr = center[0] > no2 + radius

                touching_top_brdr = not above_top_brdr and not below_top_brdr and no1 < center[0] < no2
                touching_bottom_brdr = not above_bottom_brdr and not below_bottom_brdr and no1 < center[0] < no2
                touching_left_brdr = not left_of_left_brdr and not right_of_left_brdr and no1 < center[1] < no2
                touching_right_brdr = not left_of_right_brdr and not right_of_right_brdr and no1 < center[1] < no2

                

                if touching_top_brdr or touching_bottom_brdr or touching_left_brdr or touching_right_brdr:
                    touching = True
                    # while dist < 0.07:

                    # means center is there!
                    # print("grabbed!!!!!!!!!!!!!")
                if touching:
                    ccolor = (0, 0, 255)

                    # ok so while this is doing, the square will be dragged. So the corners' coordinates will be changing
                    # by the amount that the index finger moves. hmm
                    # instead of the amount, just take the center coord and basically just add delta x and delta y to coords
                    # delta_center_x = corner_sq1[0] - center[0] 
                    # delta_center_y = 
                    # lieciama taska reikia basically prigluinti prie centro coordinaciu. Hmmmmm.
                    # pabandom is pradziu tiesiog corner prigluinti, bus paprastesne pradzia
                    prev_state_corner_sq1 = corner_sq1
                    corner_sq1 = center
                    delta_x = prev_state_corner_sq1[0] - corner_sq1[0]
                    delta_y = prev_state_corner_sq1[1] - corner_sq1[1]
                    # print(f"cornersq[0]: {corner_sq2[0]}")
                    # print(f"deltax: {delta_x}")

                    corner_sq2 = (corner_sq2[0] - delta_x, corner_sq2[1] - delta_y)

                    corner_sq3 = (corner_sq3[0] - delta_x, corner_sq3[1] - delta_y)

                    corner_sq4 = (corner_sq4[0] - delta_x, corner_sq4[1] - delta_y)
                    cv2.line(frame, corner_sq1, corner_sq2, ccolor, 5)
                    cv2.line(frame, corner_sq2, corner_sq3, ccolor, 5)
                    cv2.line(frame, corner_sq3, corner_sq4, ccolor, 5)
                    cv2.line(frame, corner_sq4, corner_sq1, ccolor, 5)

                




            # if dist_pinky_index < 0.05:
            #     corner1: tuple = (int(thumb_tip_x), int(thumb_tip_y))
            #     corner2: tuple = (int(index_tip_x), int(index_tip_y))
            #     corner3: tuple =(int(thumb_tip_x* 0.5), int(thumb_tip_y* 0.5))
            #     corner4: tuple = (int(index_tip_x * 0.5), int(index_tip_y * 0.5))
            #     color: tuple = (255, 0, 0)
            #     # line between the 2 fingers
            #     cv2.line(frame, (int(thumb_tip_x), int(thumb_tip_y)), (int(index_tip_x), int(index_tip_y)), (255, 0, 0), 5)
                
            #     # another line, not between fingers
            #     cv2.line(frame, (int(thumb_tip_x* 0.5), int(thumb_tip_y* 0.5)), (int(index_tip_x * 0.5), int(index_tip_y * 0.5)), (255, 0, 0), 5)

            #     # line from thumb to another line
            #     cv2.line(frame, (int(thumb_tip_x), int(thumb_tip_y)), (int(thumb_tip_x* 0.5), int(thumb_tip_y * 0.5)), (255, 0, 0), 5)

            #     # line from index to another line
            #     cv2.line(frame, (int(index_tip_x*0.5), int(index_tip_y*0.5)), (int(index_tip_x), int(index_tip_y)), (255, 0, 0), 5)

            #     # calculate distance between thumb tip and index tip
            #     # normalized_dist = round(dist, 1)
            #     # freq = int(200 + (1 - dist) * 800)
            # else:
            #     try:
            #         cv2.line(frame, corner1, corner2, color, 5)
            #         cv2.line(frame, corner2, corner3, color, 5)
            #         cv2.line(frame, corner3, corner4, color, 5)
            #         cv2.line(frame, corner4, corner1, color, 5)
            #     except NameError:
            #         pass






            # amazing, it works. This means that now we can try placing a square and then moving it when pinching!
            # step 1 - add a square.



            # perfect, we have a square. Now, a conditional
             


            dist = distance_3d(thumb_tip, index_tip)
            min_d = 0.03
            max_d = 0.3

            t = (dist - min_d) / (max_d - min_d)
            t = max(0.0, min(1.0, t))
            dist_pinky_wrist = distance_3d(pinky_tip, wrist)
            if dist_pinky_wrist < 0.15:
                freq = int(100 + t * 400)
            else:
                freq = int(500 + t * 2000)

            # if current_sound:
            #     current_sound.stop()
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
