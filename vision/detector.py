"""One lazily loaded IMAGE-mode detector, serialized across requests.
Independent frames prevent tracking state leaking between browser sessions.
OpenCV decodes, resizes, converts color and annotates every processed frame.
"""
import atexit
import base64
import threading
import cv2
import numpy as np
from django.conf import settings
from .gestures import finger_states, classify
_LOCK = threading.Lock()
_DETECTOR = None
def close_detector():
    global _DETECTOR
    with _LOCK:
        if _DETECTOR is not None:
            _DETECTOR.close()
            _DETECTOR = None

atexit.register(close_detector)
EDGES = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]

def analyze(raw, render_image=True):
    global _DETECTOR
    if not raw or not raw.startswith(b'\xff\xd8\xff'):
        raise ValueError('Envía una imagen JPEG válida.')
    frame = cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
    if frame is None: raise ValueError('La imagen no es válida.')
    h,w=frame.shape[:2]
    if h>1080 or w>1920: raise ValueError('La imagen debe ser de máximo 1920 × 1080.')
    if w != 640:
        frame=cv2.resize(frame,(640,max(1,round(h*640/w))))
    import mediapipe as mp
    with _LOCK:
        if _DETECTOR is None:
            if not settings.MODEL_PATH.exists():
                raise FileNotFoundError('Falta el modelo. Ejecuta: python scripts/download_model.py')
            options=mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(settings.MODEL_PATH)),
                running_mode=mp.tasks.vision.RunningMode.IMAGE,
                num_hands=2,min_hand_detection_confidence=0.6,min_hand_presence_confidence=0.6)
            _DETECTOR=mp.tasks.vision.HandLandmarker.create_from_options(options)
        result=_DETECTOR.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)))
    hands=[]
    height,width=frame.shape[:2]
    for landmarks in result.hand_landmarks:
        # Scale all axes to pixels to avoid aspect-ratio distortions in angles.
        points=[(lm.x*width,lm.y*height,lm.z*width) for lm in landmarks]
        states=finger_states(points)
        hands.append({'fingers':sum(states),'gesture':classify(states,points),
                      'landmarks':[[lm.x,lm.y] for lm in landmarks]})
        if not render_image:
            continue
        for a,b in EDGES:
            cv2.line(frame,tuple(map(int,points[a][:2])),tuple(map(int,points[b][:2])),(220,210,40),2)
        for x,y,z in points:
            cv2.circle(frame,(int(x),int(y)),5,(90,245,180),-1)
        x,y,_=points[0]
        cv2.putText(frame,f'{sum(states)} dedos',(max(5,int(x)-40),max(25,int(y)-15)),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
    response = {'hands':hands,'total':sum(h['fingers'] for h in hands)}
    if not render_image:
        return response
    ok,encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])
    if not ok: raise RuntimeError('No se pudo codificar la imagen.')
    response['image'] = base64.b64encode(encoded).decode()
    return response
