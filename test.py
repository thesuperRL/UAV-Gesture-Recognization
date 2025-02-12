import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
from mediapipe.framework.formats import landmark_pb2

model_path = 'Google-Gesture-Recognition/gesture_recognizer.task'

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.GestureRecognizerOptions(base_options=base_options)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

cap = cv2.VideoCapture(1)
with vision.GestureRecognizer.create_from_options(options) as recognizer:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        results = recognizer.recognize(mp_image)
        try:
            top_gesture = results.gestures[0][0]
            print(top_gesture.category_name)
        except IndexError:
            top_gesture = None
            print(top_gesture)

        try:
            hand_landmarks = results.hand_landmarks[0]
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            for landmark in hand_landmarks:
                hand_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z)
                  ])
        except IndexError:
            cv2.imshow('Mediapipe Hands', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break
            continue

        annotated_image = image.copy()
        try:
            mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks_proto,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
        except ValueError:
            pass

        cv2.imshow('Mediapipe Hands', cv2.flip(annotated_image, 1))
        if cv2.waitKey(5) & 0xFF == 27:
          break
cap.release()