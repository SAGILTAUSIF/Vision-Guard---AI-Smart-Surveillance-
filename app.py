import sys
import cv2
import requests
from flask import Flask, render_template, Response
from models.yolov3 import YOLOv3  # Import YOLOv3 model
from models.detect_mask import MaskDetector  # Import Mask Detection model
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# Initialize YOLOv3 model and MaskDetector
yolo_model = YOLOv3(weights_path='models/yolov3.weights', 
                    config_path='models/yolov3.cfg', 
                    labels_path='models/coco.names')

mask_model = MaskDetector(model_path='models/mask_detector.model', 
                          alert_sound_path='static/alert_sound.wav')

weapon_camera = None
mask_camera = None
detection_type = None

# Video frame generator for Flask streaming
def gen_frames(camera):
    while True:
        if detection_type is None:
            break

        success, frame = camera.read()
        if not success:
            break
        else:
            alert = False

            if detection_type == 'weapons_and_masks':
                # Process frame for weapons detection (YOLOv3)
                boxes, confidences, class_ids = yolo_model.detect_objects(frame)
                alert = yolo_model.detect_alert(boxes, class_ids)
                frame = yolo_model.draw_boxes(frame, boxes, confidences, class_ids, alert=alert)

                # Process frame for mask detection
                frame = mask_model.detect_mask(frame)

            elif detection_type == 'weapons':
                boxes, confidences, class_ids = yolo_model.detect_objects(frame)
                alert = yolo_model.detect_alert(boxes, class_ids)
                frame = yolo_model.draw_boxes(frame, boxes, confidences, class_ids, alert=alert)

            elif detection_type == 'masks':
                frame = mask_model.detect_mask(frame)

            elif detection_type == 'full_body':
                boxes, confidences, class_ids = yolo_model.detect_objects(frame)
                person_boxes = [b for b, cid in zip(boxes, class_ids) if cid == 0]
                person_confs = [c for c, cid in zip(confidences, class_ids) if cid == 0]
                person_ids = [cid for cid in class_ids if cid == 0]
                frame = yolo_model.draw_boxes(frame, person_boxes, person_confs, person_ids)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            if alert:
                yolo_model.play_alert_sound()  # Play alert sound if weapon/mask detected
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n' + b'alert')
            else:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Watchdog event handler to monitor file changes
class FileModifiedEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path == 'path_to_watched_file':
            with open(event.src_path, 'r') as file:
                new_line = file.readlines()[-1].strip()
                # Handle changes in the file (you may want to trigger a reload or log event)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_weapons_and_masks')
def video_feed_weapons_and_masks():
    global weapon_camera, mask_camera, detection_type
    detection_type = 'weapons_and_masks'
    
    # Open both cameras for simultaneous detection
    weapon_camera = cv2.VideoCapture(0)  # You could use the same camera or multiple cameras
    mask_camera = cv2.VideoCapture(0)
    
    return Response(gen_frames(weapon_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_weapons')
def video_feed_weapons():
    global weapon_camera, detection_type
    detection_type = 'weapons'
    weapon_camera = cv2.VideoCapture(0)
    return Response(gen_frames(weapon_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_masks')
def video_feed_masks():
    global mask_camera, detection_type
    detection_type = 'masks'
    mask_camera = cv2.VideoCapture(0)
    return Response(gen_frames(mask_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_full_body')
def video_feed_full_body():
    global detection_type
    detection_type = 'full_body'
    full_body_camera = cv2.VideoCapture(0)
    return Response(gen_frames(full_body_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/full_body')
def full_body_detection():
    return render_template('full_body.html')

@app.route('/stop_detection')
def stop_detection():
    global weapon_camera, mask_camera, detection_type
    detection_type = None

    if weapon_camera is not None:
        weapon_camera.release()
    if mask_camera is not None:
        mask_camera.release()

    return 'Stopped detection'

if __name__ == '__main__':
    observer = Observer()
    event_handler = FileModifiedEventHandler()
    observer.schedule(event_handler, path='.', recursive=False)                         
    observer.start()

    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
