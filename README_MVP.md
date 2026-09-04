# AMN Trace MVP

Prototipo local-first para demostrar la trazabilidad de inspecciones de AMN Quality.

## Ejecutar

Requiere Python 3.11+ y no requiere paquetes externos:

```powershell
python .\amn_trace_mvp.py
```

Abrir <http://127.0.0.1:8080>.

## Publicar en la web

El repositorio incluye `Dockerfile` y `render.yaml` para desplegar una demo en Render:

1. Crear una cuenta en Render y elegir **New > Blueprint**.
2. Conectar el repositorio `saidherw/AMN-Trace`.
3. Confirmar el archivo `render.yaml` y lanzar el servicio.
4. Render entregará una URL pública tipo `https://amn-trace.onrender.com`.

Esta configuración sirve para una demo pública. En el plan gratuito, la base e imágenes locales pueden perderse cuando el servicio se reinicia; para producción se debe usar PostgreSQL y almacenamiento de objetos inmutable en la nube, con retención de cinco años.

## GitHub Pages

También existe una demo estática en `docs/index.html`. En GitHub: **Settings > Pages > Deploy from a branch > master > /docs > Save**. Después de unos minutos quedará disponible en `https://saidherw.github.io/AMN-Trace/`. Esta demo guarda registros sólo en el navegador de cada visitante; no es el backend productivo.

## Qué demuestra

- Registro de todas las inspecciones: OK, NOK y pendiente.
- Asociación de número de serie, parte, lote, estación, operador, resultado e imagen.
- Persistencia local en SQLite y carpeta `data/evidence`.
- Cálculo de hash SHA-256 de la imagen original.
- Consulta por serie, parte, lote u operador.
- Base para cola offline: cada evento se guarda localmente con estado `PENDIENTE`.

## Siguiente incremento

El siguiente paso es conectar el adaptador real de la máquina (API, carpeta vigilada o CSV/XML/JSON), agregar el agente de sincronización con nube inmutable y convertir `PENDIENTE` en una cola con reintentos y confirmación de hash.

Este MVP es una demostración técnica local; todavía no debe usarse como sistema productivo ni como única copia de evidencia.
