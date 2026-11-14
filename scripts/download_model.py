"""Download Google's versioned Hand Landmarker model, atomically."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
URL='https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'
target=Path(__file__).resolve().parent.parent/'models'/'hand_landmarker.task'
if target.exists():
    if hashlib.sha256(target.read_bytes()).hexdigest() != 'fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1':
        raise RuntimeError('El modelo existente está dañado. Renómbralo y vuelve a ejecutar este script.')
    print('El modelo ya existe:',target)
else:
    target.parent.mkdir(exist_ok=True)
    print('Descargando modelo oficial de Google…')
    with urlopen(URL,timeout=120) as response:
        data=response.read()
    if hashlib.sha256(data).hexdigest() != 'fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1':
        raise RuntimeError('La descarga no coincide con el modelo verificado. No se guardó; intenta otra vez.')
    temporary=target.with_suffix('.tmp')
    temporary.write_bytes(data)
    temporary.replace(target)
    print('Modelo listo. SHA-256:',hashlib.sha256(data).hexdigest())
