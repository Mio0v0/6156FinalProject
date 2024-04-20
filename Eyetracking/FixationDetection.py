import time
import cv2
import lpips
import zmq
import numpy as np
from pylsl import StreamInlet, resolve_stream, StreamOutlet, StreamInfo
from physiolabxr.examples.Eyetracking.EyeUtils import prepare_image_for_sim_score, add_bounding_box
from physiolabxr.examples.Eyetracking.configs import *
import struct
import matplotlib.pyplot as plt
import unity_sdk
from unity_sdk.scene import Scene
from unity_sdk.gameobject import GameObject
from collections import deque

# Eyetracking parameters
eye_tracking_threshold = 0.7
eye_tracking_history_size = 10

# LSL detected events ########################################
fixation_outlet = StreamOutlet(StreamInfo("FixationDetection", 'FixationDetection', 3, 30, 'float32'))
saccade_outlet = StreamOutlet(StreamInfo("SaccadeDetection", 'SaccadeDetection', 3, 30, 'float32'))
blink_outlet = StreamOutlet(StreamInfo("BlinkDetection", 'BlinkDetection', 1, 30, 'float32'))
gaze_outlet = StreamOutlet(StreamInfo("GazePosition", 'GazePosition', 3, 30, 'float32'))

# zmq camera capture fields #######################################
subtopic = 'CamCapture'
sub_tcpAddress = "tcp://localhost:5556"
context = zmq.Context()
cam_capture_sub_socket = context.socket(zmq.SUB)
cam_capture_sub_socket.connect(sub_tcpAddress)
cam_capture_sub_socket.setsockopt_string(zmq.SUBSCRIBE, subtopic)

# Unity 3D scene reference
scene = Scene.get_current_scene()

# Create a new GameObject to represent the gaze position
gaze_obj = GameObject.create("Gaze")
gaze_obj.transform.position = (0, 0, 0)

# Eye tracking history
gaze_history = deque(maxlen=eye_tracking_history_size)
blink_history = deque(maxlen=eye_tracking_history_size)

print('Sockets connected, entering image loop')

while True:
    try:
        fix_detection_sample = np.zeros(3) - 1
        saccade_detection_sample = np.zeros(3) - 1
        blink_detection_sample = np.zeros(1) - 1
        gaze_detection_sample = np.zeros(3) - 1

        received_bytes = cam_capture_sub_socket.recv_multipart()
        imagePNGBytes = received_bytes[2]
        gaze_info = received_bytes[3]
        img = cv2.imdecode(np.frombuffer(imagePNGBytes, dtype='uint8'), cv2.IMREAD_UNCHANGED).reshape(image_shape)
        img_modified = img.copy()

        gaze_x, gaze_y = struct.unpack('hh', gaze_info)  # the gaze coordinate
        gaze_y = image_shape[1] - gaze_y  # because CV's y zero is at the bottom of the screen
        center = gaze_x, gaze_y

        # Update gaze history
        gaze_history.append((gaze_x, gaze_y))

        # Detect eye events
        if len(gaze_history) == eye_tracking_history_size:
            # Fixation detection
            gaze_displacement = np.sqrt(np.sum([(x - gaze_history[0][0])**2 + (y - gaze_history[0][1])**2 for x, y in gaze_history]))
            if gaze_displacement < eye_tracking_threshold:
                # Fixation detected
                gaze_position = scene.get_gameobject_by_name("Gaze").transform.position
                fix_detection_sample[0] = gaze_position.x
                fix_detection_sample[1] = gaze_position.y
                fix_detection_sample[2] = gaze_position.z
                fixation_outlet.push_sample(fix_detection_sample)

            # Saccade detection
            gaze_displacement = np.sqrt(np.sum([(x - gaze_history[-1][0])**2 + (y - gaze_history[-1][1])**2 for x, y in gaze_history]))
            if gaze_displacement > eye_tracking_threshold:
                # Saccade detected
                gaze_position = scene.get_gameobject_by_name("Gaze").transform.position
                saccade_detection_sample[0] = gaze_position.x
                saccade_detection_sample[1] = gaze_position.y
                saccade_detection_sample[2] = gaze_position.z
                saccade_outlet.push_sample(saccade_detection_sample)

            # Blink detection
            blink_history.append(np.mean(img_patch))
            if len(blink_history) == eye_tracking_history_size and np.std(blink_history) < eye_tracking_threshold:
                # Blink detected
                blink_detection_sample[0] = 1
                blink_outlet.push_sample(blink_detection_sample)

        # Update the gaze position in the 3D environment
        gaze_obj.transform.position = (gaze_x, gaze_y, 0)

        # Send the gaze position to the PhysioLabMarkerIN script
        gaze_detection_sample[0] = gaze_x
        gaze_detection_sample[1] = gaze_y
        gaze_detection_sample[2] = 0
        gaze_outlet.push_sample(gaze_detection_sample)

        img_modified = cv2.rectangle(img_modified, (int(gaze_x - 10), int(gaze_y - 10)), (int(gaze_x + 10), int(gaze_y + 10)), (0, 255, 0), thickness=2)
        cv2.imshow('Camera Capture Object Detection', img_modified)
        cv2.waitKey(delay=1)

    except KeyboardInterrupt:
        print('Stopped')