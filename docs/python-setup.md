# Configuración de Python en Windows

Este módulo se usa solo cuando el usuario inicia el análisis de video. No se ejecuta al iniciar `npm run dev`.

## Verificar Python

```powershell
py -0p
where python
```

Se recomienda Python 3.11 porque MediaPipe suele tener compatibilidad más estable con esa versión.

## Crear entorno

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si `py -3.11` no existe, instala Python 3.11 desde `python.org` y repite los comandos.

## Verificar el módulo

```powershell
python python_analysis/analyze_video.py --help
npm run check:python
```

Para una prueba con video:

```powershell
python python_analysis/analyze_video.py --video "ruta_del_video.mp4" --output "tmp/analysis_result.json"
```

El resultado es orientativo, no constituye diagnóstico médico y requiere valoración profesional.
