# Validación — 4 de noviembre de 2026

## Ejecutado en esta PC

- Python 3.11.9, PostgreSQL 16.15. Dependencias fijadas en `requirements.txt`.
- Migraciones aplicadas; `check --database default` sin errores; `makemigrations --check --dry-run` sin cambios; `pip check` sin conflictos.
- **14 pruebas aprobadas sobre PostgreSQL**, repetidas después de optimizar el video. Cubren geometría, API, CSRF, estabilidad, deduplicación, reingreso, dos manos simuladas, estadísticas, CSV, aislamiento de sesiones y entradas inválidas.
- Prueba JavaScript `scripts/test_frontend.cjs` ejecutada con Node: sintaxis, cancelación durante el permiso de cámara, vista de video directo, cancelación de petición, descarte de respuesta tardía y limpieza de temporizadores. Usa dobles de DOM/cámara; no prueba hardware ni apariencia.
- Modelo oficial descargado y SHA-256 verificado. Inferencia real sobre JPEG negro: cero manos y cero dedos.
- Servidor reiniciado con la nueva versión. Página, CSS y JS responden HTTP 200. API real con CSRF procesa 11 JPEG sin manos; historial permanece vacío y CSV responde HTTP 200.
- El usuario confirmó el diseño visual después de corregir la colisión de la variable DEBUG de Windows.

## Medición de rendimiento

Antes: la vista mostraba JPEG procesados con un límite de 6,25 FPS. Detector sobre 30 imágenes negras de 640×480: media 16,7 ms, p95 18,0 ms; primera carga 823,5 ms. Estas cifras no incluyen HTTP ni cámara.

Después: video directo solicitado a 30 FPS, independiente del análisis secuencial limitado a 10/s. Prueba HTTP real sobre diez imágenes negras después de la carga: **57,4 ms de media**, **63,8 ms máximo**; primera petición **999,5 ms**. Respuesta sin manos: **41 bytes**, sin JPEG de vuelta (antes, solo la imagen base64 ocupaba 7236 caracteres). No se comparan los tiempos del detector con los de HTTP como si fueran la misma medición.

Las medidas sin manos no demuestran rendimiento con dos manos. La frecuencia real del video depende de la cámara y la iluminación. Los puntos y el conteo aún tienen la latencia del análisis; el video ya no espera esos resultados. Los puntos viejos se ocultan tras 300 ms sin resultados.

## Pendiente de aceptación manual

- Confirmar fluidez, alineación de puntos y conteos con una/dos manos en la nueva versión.
- Probar abierta, puño, victoria, índice y pulgar con distintas luces y orientaciones.
- Probar inicio, parada, desconexión y cambio de pestaña con la webcam física.
- Descargar y abrir CSV con eventos reales; API y aislamiento están probados con datos simulados.
- Confirmar visualmente el intérprete seleccionado en VS Code; su ruta está configurada.

No se afirma precisión certificada ni ausencia total de retraso. No se guardan fotos o videos en estas comprobaciones.
