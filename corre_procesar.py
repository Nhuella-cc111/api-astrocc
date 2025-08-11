import requests
import os
import swisseph as swe

def configurar_swisseph():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweph", "ephe")
    swe.set_ephe_path(ruta)
    print("Swiss Ephemeris configurado en:", ruta)

configurar_swisseph()
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#RUTA_EPH = os.path.join(BASE_DIR, "sweph", "ephe")
#swe.set_ephe_path(RUTA_EPH)



url = "http://localhost:5000/procesa_datos"

#?modo=string"

data = {
    #"nh": "23",
    "anio":2013,
    "mes": 9,
    "dia": 17,
    "hora": 15,
    "minuto": 4,
    #"fecha_nac" : "1973-04-28",
    #"hora_nac": "15:30",
    "lat": -45.8632024,
    "lon": -67.4752615
}

response = requests.post(url, json=data)

print("Código:", response.status_code)
print("Respuesta:", response.json())