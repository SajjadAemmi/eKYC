import time
import random
from celery import Celery

celery_app = Celery(
    "tasks", broker="redis://localhost:6379", backend="redis://localhost:6379"
)


@celery_app.task
def face_verification(face_data: bytes):
    # Simulate processing time and perform face verification
    time.sleep(3)
    return {
        "status": "completed",
        "result": "face_match" if random.random() > 0.5 else "no_match",
    }


@celery_app.task
def speech_to_text(audio_data: bytes):
    # Simulate processing time and perform speech-to-text conversion
    time.sleep(5)
    return {"status": "completed", "result": "transcribed_text_here"}


@celery_app.task
def gesture_recognition(gesture_data: bytes):
    # Simulate processing time and perform gesture recognition
    time.sleep(4)
    return {"status": "completed", "result": "gesture_detected"}


# celery_app.conf.task_routes = {
#     "tasks.face_verification": {"queue": "face_verification"},
#     "tasks.speech_to_text": {"queue": "speech_to_text"},
#     "tasks.gesture_recognition": {"queue": "gesture_recognition"},
# }
