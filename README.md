# api-astrocc

Backend para cálculo y automatización del **Carnet Cósmico**.

## 📦 Tecnologías principales

- Python 3.13+
- Flask (API REST)
- Swiss Ephemeris (pyswisseph)
- Supabase (como base de datos)
- Gunicorn (para producción)
- Make, Retool y Render (para despliegue e integración)
- pytz (manejo de husos horarios)
- requests (llamados a APIs)

## 🚀 Instalación y ejecución local

1. **Cloná el repo:**
   ```bash
   git clone https://github.com/Nhuella-cc111/api-astrocc.git
   cd api-astrocc

2. Creá un entorno virtual y activalo:


python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

3.Instalá dependencias:


pip install -r requirements.txt

4. Configurá variables de entorno (Supabase, etc):

Crear archivo .env con tus credenciales si es necesario.

5. Ejecución local:


python main.py

6. Para pruebas unitarias o scripts:


python corre_guardar.py

===========================
Endpoints principales
POST /guardar — Calcula y guarda datos astrológicos, kin maya, DH y marca como procesado.

Otros endpoints para cálculos astrológicos (ver main.py).

🛠️ Despliegue
El proyecto se puede desplegar en Render usando Gunicorn.

El requirements.txt instala todas las dependencias automáticamente.

💡 Notas
El proyecto está orientado a integraciones automáticas con Make, Retool y formularios web.

Para dudas sobre la lógica astrológica, ver funciones en main.py.




