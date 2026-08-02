# ⚡ LabInventory Pro - App Web en Python (FastAPI + SQLite + TailwindCSS)

Aplicación Web moderna en Python para la administración de inventario del laboratorio, emisión de **Fichas Digitales de Solicitud de Materiales** con descuento automático de stock y seguimiento de préstamos.

---

## 🚀 Características Principales

1. **Backend en Python + FastAPI + SQLite**:
   - Persistencia de datos en la base de datos `inventory.db` mediante **SQLAlchemy ORM**.
   - Precarga automática (`seed.py`) de los **197 artículos reales** del laboratorio con sus correspondientes cantidades físicas, ubicaciones de bodega y centros de costo.

2. **Ficha Digital de Solicitud de Materiales**:
   - Registro de datos del solicitante (Alumno/Docente, RUT, Carrera, Asignatura, Profesor y Fecha de Devolución).
   - **Descuento Automático**: Al autorizar la solicitud, FastAPI reduce inmediatamente la cantidad de *"Stock Disponible"* y la añade a *"En Uso / Prestado"*.
   - **Devolución de Materiales**: Botón para marcar solicitudes devueltas y retornar las unidades al stock disponible.
   - **Comprobante Oficial Imprimible**: Formulario listo para imprimir o guardar como PDF con firma del encargado y solicitante.

3. **Reportes y Estadísticas del Semestre**:
   - Ranking interactivo del **Top 10 de materiales más solicitados** durante el semestre.
   - Análisis por Centro de Costo (*Informática*, *Industrial*, *Ambas Carreras*).

4. **Diseño Responsivo (Celular y Escritorio)**:
   - Menú de navegación inferior táctil para celular.
   - Exportación de catálogo completo a archivo **CSV/Excel**.

---

## 🛠️ Instalación y Ejecución Local

### 1. Requisitos Previos
Tener Python 3.9 o superior instalado en tu sistema.

### 2. Instalación de Dependencias
Abre la terminal en este directorio (`lab_inventory_python_app`) y ejecuta:

```bash
pip install -r requirements.txt
```

### 3. Iniciar la Aplicación Web
Ejecuta el servidor con Python:

```bash
python app.py
```
o con `uvicorn`:
```bash
uvicorn app:app --reload --port 8000
```

Abre tu navegador en:
👉 **http://127.0.0.1:8000**

---

## 📋 Documentación de la API REST (Swagger UI)

FastAPI genera documentación interactiva de todos los endpoints en:
👉 **http://127.0.0.1:8000/docs**

---

## 🧪 Pruebas Automáticas

Para ejecutar la verificación completa de base de datos, precarga y descuento de stock:

```bash
python verify.py
```

---

## 📲 Guía para Subir a GitHub

1. Crea un nuevo repositorio en tu cuenta de GitHub (ej: `inventario-laboratorio-python`).
2. En la terminal de esta carpeta ejecuta:

```bash
git init
git add .
git commit -m "Inicializar LabInventory Pro App Web en Python"
git branch -M main
git remote add origin https://github.com/Flores27713/inventario-laboratorio-python.git
git push -u origin main
```
