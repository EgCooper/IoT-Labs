# L6 — Consumo de telemetría IoT y API propia

**Rama:** `L6-A1-A2-A3`  
**Repo:** https://github.com/EgCooper/IoT-Labs  
**API:** `api/app.py`  
**Dashboard:** http://127.0.0.1:5000

Endpoint público: https://callback-iot.up.railway.app/data

| Método | Ruta | Función |
|--------|------|---------|
| GET | `/data` | Consulta el endpoint público y devuelve los últimos 2 registros |
| POST | `/visualize` | Recibe JSON y lo envía a la visualización |

Las imágenes van en `docs/capturas/` y se enlazan abajo.

---

## 1. JSON recibido (GET `/data`)

> Pegá aquí la captura del JSON (navegador, dashboard o respuesta de la API).

![JSON recibido](/img/json.png)

---

## 2. Terminal — GET y POST

> Capturas de la consola donde se vean las llamadas a `GET /data` y `POST /visualize` (curl, PowerShell o log de Flask).

### GET `/data`

![Terminal GET](/img/terminal.png)

```text
# ejemplo
curl http://127.0.0.1:5000/data
```

### POST `/visualize`

![Terminal POST](/img/terminal.png)

```text
# ejemplo
curl -Method POST http://127.0.0.1:5000/sync
```

---

## 3. Dashboard (gauges)

> Captura del panel con temperatura, humedad, presión y batería después de sincronizar.

![Dashboard](/img/dashboard.png)

---

## 4. Reflexión

La API propia funciona como adaptador: no habla Sigfox directo, consume el callback HTTP ya publicado. Separar GET (lectura de los últimos 2 registros) de POST (carga de la visualización) permite probar cada método y también encadenarlos desde el dashboard.

El estado de los gauges vive en memoria del proceso Flask, suficiente para el laboratorio. En un sistema real se persistiría. Node-RED quedó como opción; se usó una web propia para versionar los widgets junto con el código.

**Qué se observó al probar**

- *(completar con lo que viste en las capturas: un solo registro vs dos, valores de temp/hum, etc.)*
- *(dificultades: entorno, CORS, endpoint público, etc.)*
