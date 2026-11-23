# Sistema de Gestión de Blog — Neo4j y Python

Aplicación de escritorio para la administración de un blog sobre una base de datos orientada a grafos (**Neo4j**), desarrollada en **Python** con **Tkinter** y el driver oficial `neo4j`.

## Contenido del Repositorio
* `blog.cypher` — Script Cypher con limpieza del grafo y restricciones de unicidad (`CONSTRAINT`).
* `dbC.py` — Capa de persistencia (DAO) e inicializador por línea de comandos (`--init`).
* `guiC.py` — Interfaz gráfica unificada (Operación pública + Panel administrativo con contraseña).
* `Proyecto_3_parcial_BDA.pdf` — Reporte técnico documentado y evidencias de ejecución.

---

## 1. Prerrequisitos
1. Servidor local de **Neo4j** activo en `bolt://localhost:7687` (en Linux: `sudo systemctl start neo4j`).
2. Configurar las credenciales locales (`URI`, `USER`, `PASSWORD`) al inicio de `dbC.py`.
3. **Python 3.8+** instalado.

---

## 2. Configuración del Entorno Virtual (`venv`)

### Linux / macOS
```bash
# 1. Crear el entorno virtual
python3 -m venv venv

# 2. Activar el entorno virtual
source venv/bin/activate

# 3. Instalar el driver de Neo4j
pip install neo4j

### Windows (PowerShell)
```PowerShell

# 1. Crear el entorno virtual
python -m venv venv

# 2. Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# 3. Instalar el driver de Neo4j
pip install neo4j

## 3. Ejecución del Proyecto

# Inicializar la base de datos (ejecutar una sola vez al inicio):
python dbC.py --init

# Abrir la aplicación gráfica:
python guiC.py
(Para acceder a la pestaña Administración y Auditoría, ingrese la contraseña: 123456).