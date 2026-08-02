# ⚡ LabInventory Pro - App Web en Python (FastAPI + SQLite + TailwindCSS)

Aplicación Web moderna en Python para la administración de inventario del laboratorio, emisión de **Fichas Digitales de Solicitud de Materiales** con descuento automático de stock y seguimiento de préstamos.

---

## 🌐 Cómo Desplegar Gratis en Render.com (En 2 Minutos)

Para publicar tu app web en internet y tener un enlace público tipo `https://gestion-laboratorio.onrender.com` que puedas abrir desde tu celular:

### Paso 1: Iniciar sesión en Render
1. Ve a [https://dashboard.render.com](https://dashboard.render.com) e inicia sesión con tu cuenta de **GitHub**.

### Paso 2: Crear un nuevo Web Service
1. Haz clic en el botón azul **"New +"** &rarr; **"Web Service"**.
2. Selecciona tu repositorio de GitHub: **`Flores27713/Gestion-laboratorio`**.

### Paso 3: Configurar los parámetros en Render
Rellena estos sencillos datos:

- **Name**: `gestion-laboratorio` (o el nombre que prefieras).
- **Region**: Oregon (US West) o Frankfurt (Europe).
- **Branch**: `main`
- **Root Directory**: `lab_inventory_python_app` *(¡Muy Importante!)*
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: **Free**

### Paso 4: ¡Desplegar!
Haz clic en **"Create Web Service"**.
Render comenzará a construir e instalar las dependencias. En 1-2 minutos tendrás tu URL pública lista:
👉 **`https://gestion-laboratorio.onrender.com`**

---

## 🛠️ Ejecución Local

```bash
pip install -r requirements.txt
python app.py
```

Abrir en navegador:
👉 **http://127.0.0.1:8000**
👉 **http://127.0.0.1:8000/docs** (Swagger UI)

---

## 🧪 Pruebas Automáticas

```bash
python verify.py
```
