import asyncio
from pynput import keyboard
from mavsdk import System
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import time
import asyncio
import numpy as np
from mediapipe.framework.formats import landmark_pb2
from threading import Thread

velocity = None

roll = ""
pitch = ""
throttle = ""
yaw = ""

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

model_path = '/home/ryanli/PycharmProjects/UAV-Gesture-Recognization/Google-Gesture-Recognition/gesture_recognizer.task'

# STEP 2: Create an GestureRecognizer object.
base_options = python.BaseOptions(model_asset_path=model_path)
VisionRunningMode = mp.tasks.vision.RunningMode
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
GestureRecognizer = mp.tasks.vision.GestureRecognizer

scale = 1.0
fps = 30.0

cap = cv2.VideoCapture(0)
cap.set(3, int(256.0 * scale))
cap.set(4, int(144.0 * scale))
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

options = vision.GestureRecognizerOptions(
    base_options=base_options)

def parse_gesture(gesture_object):
    if gesture_object.category_name == "Open_Palm":
        send_command("ascend")
    elif gesture_object.category_name == "Closed_Fist":
        send_command("descend")
    elif gesture_object.category_name == "Victory":
        send_command("hover")
    else:
        print("Not Recognized as Command")

def send_command(command):
    global roll, pitch, throttle, yaw
    try:
        if command == 'forward':
            print("moving forwards")
            roll = 0.0
            pitch = 0.5
            throttle = 0.5
            yaw = 0.0
        elif command == 'left':
            print("moving left")
            roll = -0.5
            pitch = 0.0
            throttle = 0.5
            yaw = 0.0
        elif command == 'backward':
            print("moving backwards")
            roll = 0.0
            pitch = -0.5
            throttle = 0.5
            yaw = 0.0
        elif command == 'right':
            print("moving right")
            roll = 0.5
            pitch = 0.0
            throttle = 0.5
            yaw = 0.0
        elif command == 'ascend':
            print("ascending")
            roll = 0.0
            pitch = 0.0
            throttle = 0.7
            yaw = 0.0
        elif command == 'descend':
            print("descending")
            roll = 0.0
            pitch = 0.0
            throttle = 0.2
            yaw = 0.0
        elif command == 'hover':
            print("hovering until further command")
            roll = 0.0
            pitch = 0.0
            throttle = 0.5
            yaw = 0.0
        else:
            print("command '" + str(command) + "' received, reset speed")
            roll = 0.0
            pitch = 0.0
            throttle = 0.5
            yaw = 0.0
    except:
        print("failed to recognize command: " + str(command))


async def main():
    """Main function to connect to the drone and input manual controls"""
    global roll, pitch, yaw, throttle
    # Connect to the Simulation
    drone = System()
    await drone.connect(system_address="udp://:14540")

    # This waits till a mavlink based drone is connected
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    # Checking if Global Position Estimate is ok
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position state is good enough for flying.")
            break

    # Arming the drone
    print("-- Arming")
    await drone.action.arm()

    # Take off
    print("-- Taking off")
    await drone.action.takeoff()
    await asyncio.sleep(10)

    print("-- Set manual control")
    roll = 0.0
    pitch = 0.0
    throttle = 0.5
    yaw = 0.0
    # set the manual control input after arming
    manual = asyncio.create_task(manual_controls(drone))
    print("-- wait")
    await asyncio.sleep(1)

    # start manual control
    print("-- Starting manual control")
    await drone.manual_control.start_position_control()
    print("-- wait")
    await asyncio.sleep(1)
    print("-- Activating manual control")

    thread = Thread(target=recognizer_threaded)
    thread.start()

    # listener = keyboard.Listener(
    #     on_press=send_command)
    # listener.start()

    while True:
        await asyncio.sleep(1)

    await drone.action.land()
    print("-- end")

async def manual_controls(drone):
    global roll, pitch, yaw, throttle
    while True:
        await drone.manual_control.set_manual_control_input(pitch, roll, throttle, yaw)


def recognizer_threaded():
    with GestureRecognizer.create_from_options(options) as recognizer:
        while cap.isOpened():
            success, image = cap.read()
            time.sleep(1.0/fps)
            if not success:
              print("Ignoring empty camera frame.")
              # If loading a video, use 'break' instead of 'continue'.
              continue

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
            recognition_result = recognizer.recognize(mp_image)

            try:
                top_gesture = recognition_result.gestures[0][0]
                print("Gesture Probably: " + str(top_gesture.category_name))
                parse_gesture(top_gesture)
                hand_landmarks = recognition_result.hand_landmarks
            except:
                print("Unrecognized Gestures")
                cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))
                if cv2.waitKey(5) & 0xFF == 27:
                  break
                continue

            # Draw the hand annotations on the image.
            image.flags.writeable = True
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks[0]
            ])
            mp_drawing.draw_landmarks(
                image,
                hand_landmarks_proto,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
            # Flip the image horizontally for a selfie-view display.
            cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
              break
    cap.release()

asyncio.run(main())