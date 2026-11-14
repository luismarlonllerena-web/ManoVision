# ManoVision

Aplicación local para detectar hasta dos manos, contar de 0 a 10 dedos y reconocer gestos básicos. Usa **Django, OpenCV, MediaPipe Tasks y PostgreSQL**. Incluye historial por sesión, estadísticas y exportación CSV; no guarda fotos ni videos.

## Abrir en esta PC

1. Ejecuta **iniciar.bat** con doble clic y mantén abierta su consola.
2. Abre **http://127.0.0.1:8000/**. Pulsa **Iniciar cámara** y acepta el permiso.
3. Muestra las palmas con buena luz. Prueba mano abierta, puño, victoria, índice y pulgar arriba.
4. Pulsa **Detener** para liberar la cámara. El historial permanece. Cambiar de pestaña también detiene la captura.
5. **Exportar CSV** descarga todos los eventos de esta sesión. La tabla muestra los 30 más recientes; las estadísticas cuentan todos.

No es necesario reinstalar dependencias, descargar el modelo ni volver a crear la base cada vez. El iniciador comprueba el modelo, inicia PostgreSQL cuando hace falta y aplica solo migraciones pendientes. Si ya está abierta la aplicación, utiliza ese servidor; no abras varias consolas en el mismo puerto.

### Instalación local realizada

- Python **3.11.9 de 64 bits**, aislado en `.venv`. Se conservó Python 3.14.7; Python 3.12 no estaba instalado.
- PostgreSQL **16.15** portable en `.local/pgsql`, datos en `.local/pgdata`, base/usuario `manovision`, puerto **127.0.0.1:5433**. No necesita Docker ni servicio Windows.
- Credenciales aleatorias en `.env`; credencial administrativa en `.local/postgres-admin.env`. No compartas estos archivos.
- Modelo oficial en `models/hand_landmarker.task`, verificado por SHA-256.
- `.vscode/settings.json` apunta a `.venv/Scripts/python.exe`. Si el editor conserva otra selección: **Ctrl+Shift+P → Python: Select Interpreter → Enter interpreter path**, y selecciona ese ejecutable.

Ctrl+C en la consola detiene Django. PostgreSQL permanece encendido. Para detenerlo limpiamente después de cerrar Django:

```powershell
.local\pgsql\bin\pg_ctl.exe -D .local\pgdata -m fast -w stop
```

No borres `.local/pgdata`: contiene el historial. `.venv`, `.env`, `.local` y el modelo son necesarios en esta PC, pero están excluidos de Git.

## Instalar desde Git o ZIP en otra PC Windows

Si recibiste un ZIP, extrae **todo su contenido** antes de empezar. El paquete contiene el código y las instrucciones, no las dependencias instaladas ni las credenciales de otra PC. La sección «Instalación local realizada» describe el equipo original, no el contenido del ZIP.

Requisitos: Python **3.11 o 3.12 de 64 bits**, cámara, navegador actual e Internet durante la instalación. Desde la carpeta con `manage.py`:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts/download_model.py
```

`requirements.txt` contiene las versiones exactas comprobadas en Windows con Python 3.11, incluidas las dependencias indirectas. Usa este archivo para reproducir la instalación. No instales varias distribuciones de OpenCV en el mismo entorno.

Elige una opción para PostgreSQL:

**Portable aislado:** descarga los [binarios oficiales de EDB](https://www.enterprisedb.com/download-postgresql-binaries) de PostgreSQL 16 para Windows x64 y extrae `pgsql` en `.local`. Con el puerto 5433 libre ejecuta:

```powershell
.venv\Scripts\python.exe scripts/setup_local_db.py
```

Este script crea credenciales y una base nueva; rechaza sobrescribir `.env` o un clúster existente. El usuario tiene CREATEDB para ejecutar las pruebas, sin ser superusuario. Si la preparación se interrumpe, revisa el estado creado antes de reintentarlo; no borres datos para forzar el proceso.

**PostgreSQL existente:** copia `.env.example` a `.env`, genera un SECRET_KEY aleatorio y configura una base dedicada con su usuario, contraseña, host y puerto. Un administrador debe crear la base y asignar ese usuario como propietario. No borres bases existentes. Para ejecutar las pruebas, el usuario necesita CREATEDB.

**Docker:** si ya tienes Docker Desktop, configura `.env` a partir del ejemplo y ejecuta `docker compose up -d db`. No uses el mismo puerto del PostgreSQL portable. Cambiar la contraseña de `.env` no cambia la contraseña de un volumen ya inicializado.

Finalmente ejecuta `iniciar.bat`. Opcionalmente crea un administrador con `.venv\Scripts\python.exe manage.py createsuperuser` y entra en `/admin/`.

## Video, detección e historial

El video se muestra directamente desde la cámara, reflejado, con una solicitud de hasta 30 FPS al dispositivo. La frecuencia real depende de la webcam y la iluminación. La vista no espera a que Django devuelva una imagen.

En paralelo se analiza como máximo un JPEG cada 100 ms (hasta 10 análisis/s), siempre secuencialmente y sin acumular fotogramas. OpenCV prepara la imagen y MediaPipe detecta hasta 21 puntos por mano. Django devuelve coordenadas, conteos y gestos; el navegador dibuja las conexiones sobre el video. El indicador muestra **análisis/s y milisegundos de captura/respuesta**, no los FPS de la webcam. Los puntos y el conteo pueden seguir teniendo un pequeño retraso respecto del video. Los puntos se ocultan si no llegan resultados nuevos durante 300 ms.

El detector usa modo IMAGE y un bloqueo para no compartir seguimiento temporal entre sesiones. Se mantiene una salida JPEG anotada opcional en `analyze(..., render_image=True)` para diagnóstico; la interfaz usa la respuesta compacta sin JPEG de vuelta.

Se guarda un evento después de tres análisis consecutivos coincidentes, con al menos dos segundos entre registros. Un gesto sostenido no se duplica; retirar las manos permite repetirlo. El historial pertenece a la sesión del navegador: borrar sus cookies impide recuperar desde ella los eventos anteriores, aunque siguen en PostgreSQL.

## Pruebas y limitaciones

```powershell
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe manage.py check --database default
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test -v 2 --noinput
```

Las pruebas usan PostgreSQL y crean/eliminan exclusivamente la base temporal `test_manovision`; no uses ese nombre para datos personales. No se usa SQLite. Resultados y pendientes: [docs/VALIDACION.md](docs/VALIDACION.md).

Los gestos se estiman con ángulos y distancias. Manos de perfil, oclusiones, mala luz y pulgares pegados a la palma pueden producir errores. No traduce lengua de señas ni tiene precisión certificada. Las pruebas simuladas no miden reconocimiento real. El primer análisis carga el modelo y tarda más.

## Solución de problemas

| Problema | Acción |
|---|---|
| Página sin diseño | Usa Ctrl+F5. El `.env` local debe tener `DEBUG=1`; solo `MANOVISION_DEBUG` puede sobrescribirlo desde el sistema. La variable genérica `DEBUG` de Windows se ignora. |
| Cámara denegada u ocupada | Revisa el permiso del navegador/Windows y cierra Zoom, Meet u otras aplicaciones que la usen. |
| Video fluido pero puntos retrasados | Observa los ms del indicador, mejora la luz y cierra procesos pesados. El análisis y la webcam tienen frecuencias distintas. |
| PostgreSQL no conecta | Revisa `.env`, el puerto y `.local/postgres.log`, sin publicar credenciales. |
| Modelo dañado | Renombra el archivo del modelo y ejecuta de nuevo el descargador. |
| Puerto 8000 ocupado | Usa el servidor ya abierto o ciérralo antes de iniciar otro. |

El servidor escucha solo en localhost y es para desarrollo local. No lo expongas a Internet con esta configuración.

## Archivos y GitHub

`config/` contiene configuración; `vision/` contiene detector, gestos, API, modelos, migraciones y pruebas; `static/` y `templates/` contienen la interfaz; `scripts/` prepara la base y descarga el modelo.

`.gitignore` excluye credenciales, entorno, PostgreSQL portable, datos, cachés, logs y modelo. El código, requirements.txt, migraciones, `.env.example` y documentación sí se versionan. No subas un ZIP completo de tu carpeta de trabajo.

Para publicar en un repositorio vacío de tu cuenta, revisa primero los archivos preparados:

```powershell
git add .
git diff --cached --stat
git commit -m "Prepara ManoVision para Windows y PostgreSQL"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/ManoVision.git
git push -u origin main
```

No se publica automáticamente ni se incluye ninguna contraseña. Sustituye `TU_USUARIO` por tu cuenta.

## Referencias

- [Django 5.2](https://docs.djangoproject.com/en/5.2/)
- [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)
- [PostgreSQL para Windows](https://www.postgresql.org/download/windows/)
- [OpenCV](https://docs.opencv.org/4.x/)

El modelo es preentrenado; no fue entrenado por este proyecto. Las bibliotecas y el modelo mantienen sus propias licencias.
