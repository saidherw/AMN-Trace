# AMN Trace MVP

Prototipo local-first para demostrar la trazabilidad de inspecciones de AMN Quality.

## Ejecutar

Requiere Python 3.11+ y no requiere paquetes externos:

```powershell
python .\amn_trace_mvp.py
```

Abrir <http://127.0.0.1:8080>.

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
