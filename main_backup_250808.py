from flask import Flask, request, jsonify
from supabase import create_client, Client
import swisseph as swe
import requests
from datetime import date
from datetime import datetime, timedelta
import pytz
import os
import math


def configurar_swisseph():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweph", "ephe")
    swe.set_ephe_path(ruta)
    print("Swiss Ephemeris configurado en:", ruta)



app = Flask(__name__)


SUPABASE_URL = "https://amjskrqaoiuabscecmji.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtanNrcnFhb2l1YWJzY2VjbWppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5Nzg3NDksImV4cCI6MjA2NjU1NDc0OX0.t_9h25ehDGBWGz39YmMPdeeaFyWpQcoDR0POt5Y3CXQ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Modalidad por signo
modalidad_por_signo = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricornio": "Cardinal",
    "Tauro": "Fija", "Leo": "Fija", "Escorpio": "Fija", "Acuario": "Fija",
    "Geminis": "Mutable", "Virgo": "Mutable", "Sagitario": "Mutable", "Piscis": "Mutable"
}

# Elemento por signo
elemento_por_signo = {
    "Aries": "Fuego", "Leo": "Fuego", "Sagitario": "Fuego",
    "Tauro": "Tierra", "Virgo": "Tierra", "Capricornio": "Tierra",
    "Geminis": "Aire", "Libra": "Aire", "Acuario": "Aire",
    "Cancer": "Agua", "Escorpio": "Agua", "Piscis": "Agua"
}

# Polaridad por signo
polaridad_por_signo = {
    "Aries": "P", "Geminis": "P", "Leo": "P", "Libra": "P",
    "Sagitario": "P", "Acuario": "P",
    "Tauro": "N", "Cancer": "N", "Virgo": "N",
    "Escorpio": "N", "Capricornio": "N", "Piscis": "N"
}

# Pesos por planeta/punto
pesos = {
    "Sol": 3, "Luna": 3, "Asc": 3,
    "Mercurio": 2, "Venus": 2, "Marte": 2,
    "Jupiter": 1, "Saturno": 1
}

PLANETAS_ELEMENTO_POLARIDAD = ["Sol", "Luna", "Mercurio", "Venus", "Marte", "Jupiter", "Saturno"] 

'''
Diseño Humano
'''
tabla_puertas = [
    {"puerta":17, "inicio": 3.750,   "fin": 9.375  },
    {"puerta":21, "inicio": 9.375,   "fin": 15.000 },
    {"puerta":51, "inicio": 15.000,  "fin": 20.625 },
    {"puerta":42, "inicio": 20.625,  "fin": 26.250 },
    {"puerta": 3, "inicio": 26.250,  "fin": 31.875 },
    {"puerta":27, "inicio": 31.875,  "fin": 37.500 },
    {"puerta":24, "inicio": 37.500,  "fin": 43.125 },
    {"puerta": 2, "inicio": 43.125,  "fin": 48.750 },
    {"puerta":23, "inicio": 48.750,  "fin": 54.375 },
    {"puerta": 8, "inicio": 54.375,  "fin": 60.000 },
    {"puerta":20, "inicio": 60.000,  "fin": 65.625 },
    {"puerta":16, "inicio": 65.625,  "fin": 71.250 },
    {"puerta":35, "inicio": 71.250,  "fin": 76.875 },
    {"puerta":45, "inicio": 76.875,  "fin": 82.500 },
    {"puerta":12, "inicio": 82.500,  "fin": 88.125 },
    {"puerta":15, "inicio": 88.125,  "fin": 93.750 },
    {"puerta":52, "inicio": 93.750,  "fin": 99.375 },
    {"puerta":39, "inicio": 99.375,  "fin": 105.000},
    {"puerta":53, "inicio": 105.000, "fin": 110.625},
    {"puerta":62, "inicio": 110.625, "fin": 116.250},
    {"puerta":56, "inicio": 116.250, "fin": 121.875},
    {"puerta":31, "inicio": 121.875, "fin": 127.500},
    {"puerta":33, "inicio": 127.500, "fin": 133.125},
    {"puerta": 7, "inicio": 133.125, "fin": 138.750},
    {"puerta": 4, "inicio": 138.750, "fin": 144.375},
    {"puerta":29, "inicio": 144.375, "fin": 150.000},
    {"puerta":59, "inicio": 150.000, "fin": 155.625},
    {"puerta":40, "inicio": 155.625, "fin": 161.250},
    {"puerta":64, "inicio": 161.250, "fin": 166.875},
    {"puerta":47, "inicio": 166.875, "fin": 172.500},
    {"puerta": 6, "inicio": 172.500, "fin": 178.125},
    {"puerta":46, "inicio": 178.125, "fin": 183.750},
    {"puerta":18, "inicio": 183.750, "fin": 189.375},
    {"puerta":48, "inicio": 189.375, "fin": 195.000},
    {"puerta":57, "inicio": 195.000, "fin": 200.625},
    {"puerta":32, "inicio": 200.625, "fin": 206.250},
    {"puerta":50, "inicio": 206.250, "fin": 211.875},
    {"puerta":28, "inicio": 211.875, "fin": 217.500},
    {"puerta":44, "inicio": 217.500, "fin": 223.125},
    {"puerta": 1, "inicio": 223.125, "fin": 228.750},
    {"puerta":43, "inicio": 228.750, "fin": 234.375},
    {"puerta":14, "inicio": 234.375, "fin": 240.000},
    {"puerta":34, "inicio": 240.000, "fin": 245.625},
    {"puerta": 9, "inicio": 245.625, "fin": 251.250},
    {"puerta": 5, "inicio": 251.250, "fin": 256.875},
    {"puerta":26, "inicio": 256.875, "fin": 262.500},
    {"puerta":11, "inicio": 262.500, "fin": 268.125},
    {"puerta":10, "inicio": 268.125, "fin": 273.750},
    {"puerta":58, "inicio": 273.750, "fin": 279.375},
    {"puerta":38, "inicio": 279.375, "fin": 285.000},
    {"puerta":54, "inicio": 285.000, "fin": 290.625},
    {"puerta":61, "inicio": 290.625, "fin": 296.250},
    {"puerta":60, "inicio": 296.250, "fin": 301.875},
    {"puerta":41, "inicio": 301.875, "fin": 307.500},
    {"puerta":19, "inicio": 307.500, "fin": 313.125},
    {"puerta":13, "inicio": 313.125, "fin": 318.750},
    {"puerta":49, "inicio": 318.750, "fin": 324.375},
    {"puerta":30, "inicio": 324.375, "fin": 330.000},
    {"puerta":55, "inicio": 330.000, "fin": 335.625},
    {"puerta":37, "inicio": 335.625, "fin": 341.250},
    {"puerta":63, "inicio": 341.250, "fin": 346.875},
    {"puerta":22, "inicio": 346.875, "fin": 352.500},
    {"puerta":36, "inicio": 352.500, "fin": 358.125},
    {"puerta":25, "inicio": 358.125, "fin": 3.750  }
]
'''
tabla_puertas = []
for i in range(64):
    inicio = i * 5.625
    fin = inicio + 5.625
    tabla_puertas.append({
        "puerta": i + 1,
        "inicio": inicio,
        "fin": fin
    })
print(tabla_puertas)
'''

def fecha_sol_inconsciente(anio, mes, dia, hora, minuto):
    """
    Devuelve la fecha y hora exacta 88.3 días antes del nacimiento.
    """
    fecha_nacimiento = datetime(anio, mes, dia, hora, minuto)

    # Restar 88 días
    delta = timedelta(days=88, hours=7, minutes=12, seconds=50) # 0.3 días ≈ 7h12m
    fecha_inconsciente= fecha_nacimiento - delta

    # Forzar hora y minutos a 00:00
    fecha_inconsciente = fecha_inconsciente.replace(hour=12, minute=0, second=0, microsecond=0)

    #fecha_nacimiento = datetime(anio, mes, dia, hora, minuto)
    #delta = timedelta(days=88, hours=0, minutes=0)  # 0.3 días ≈ 7h12m
    #fecha_inconsciente = fecha_nacimiento - fecha_resultado
    print(f"fecha inconsciente: {fecha_inconsciente}")
    return {
        "anio_i":fecha_inconsciente.year,
        "mes_i":fecha_inconsciente.month,
        "dia_i":fecha_inconsciente.day,
        "hora_i":fecha_inconsciente.hour,
        "minuto_i":fecha_inconsciente.minute
    }


def grados_a_dms(grado_decimal):
    grados = int(grado_decimal)
    minutos = int((grado_decimal - grados) * 60)
    segundos = int((((grado_decimal - grados) * 60) - minutos) * 60)
    return f"{grados:02d}°{minutos:02d}'{segundos:02d}\""


def calcular_casa(jd, lat, lon, grado_planeta):

    cuspides, _ = swe.houses(jd, lat, lon, b'P')  # <--- invertido!
    #print(f"Cúspides: {cuspides}")
    #print(f"Grado planeta: {grado_planeta}")
    casa = 12
    for i in range(12):
        inicio = cuspides[i]
        fin = cuspides[(i + 1) % 12]
        if inicio < fin:
            if inicio <= grado_planeta < fin:
                casa = i + 1
                break
        else:  # cruce 360 -> 0
            if grado_planeta >= inicio or grado_planeta < fin:
                casa = i + 1
                break
    return casa

import requests

def obtener_offset_inconsciente(anio, mes, dia, hora, minuto, lat, lon):
    """
    Devuelve el offset UTC estándar (sin horario de verano) para cualquier lat/lon y fecha.
    Usa la API de TimeZoneDB.
    """
    try:
        api_key = "0KL8FYY73NT2"  # Reemplaza por tu propia API key si tienes otra
        url = (
            f"http://api.timezonedb.com/v2.1/get-time-zone"
            f"?key={api_key}&format=json&by=position&lat={lat}&lng={lon}"
            f"&time={anio}-{mes:02d}-{dia:02d}T{hora:02d}:{minuto:02d}:00"
        )
        response = requests.get(url)
        data = response.json()
        # El offset estándar está en 'gmtOffset' menos 'dst' si está en horario de verano
        # Pero para el estándar puro, usamos 'gmtOffset' menos 'dst' (si dst==1)
        offset = data.get("gmtOffset", 0)
        if data.get("dst", "0") == "1":
            offset = offset - data.get("dstSavings", 0)
        return offset / 3600
    except Exception as e:
        print(f"❌ ERROR en TimeZoneDB para lat={lat} lon={lon} → {e}")
        return 0  # fallback

def obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    # Asignamos zona horaria correcta (Comodoro usa zona Argentina)
    tz = pytz.timezone("America/Argentina/Buenos_Aires")  # válido para todo el país
    dt_local = datetime(anio, mes, dia, hora, minuto)
    offset = tz.utcoffset(dt_local).total_seconds() / 3600
    return offset
'''
def obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    try:
        print(f"Llamando a TimeZoneDB con lat={lat}, lon={lon}")
        url = f"http://api.timezonedb.com/v2.1/get-time-zone?key=0KL8FYY73NT2&format=json&by=position&lat={lat}&lng={lon}"
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")
        data = response.json()
        return data["gmtOffset"] / 3600
    except Exception as e:
        print(f"❌ ERROR en TimeZoneDB con lat={lat} lon={lon} → {e}")
        return -3  # fallback
'''

def obtener_geolocalizacion():
    try:
        ciudad = request.args.get("ciudad")
        provincia = request.args.get("provincia")
        pais = request.args.get("pais")

        if not all([ciudad, provincia, pais]):
            return jsonify({"error": "Faltan parámetros"})

        direccion = f"{ciudad}, {provincia}, {pais}"
        api_key = "21f0075720f44914b2cfdd8e64c27b68"  
        url = f"https://api.opencagedata.com/geocode/v1/json?q={direccion}&key={api_key}&language=es&pretty=1"

        response = requests.get(url)
        data = response.json()
        print(f"Geolocalización para {direccion}: {data}")

        if data["results"]:
            geometry = data["results"][0]["geometry"]
            return jsonify({
                "latitud": geometry["lat"],
                "longitud": geometry["lng"]
            })
        else:
            return jsonify({"error": "No se encontraron resultados"})

    except Exception as e:
        return jsonify({"error": str(e)})


def obtener_signo(grados):
    signos = [
        "Aries", "Tauro", "Geminis", "Cancer", "Leo", "Virgo", "Libra",
        "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signos[int(grados // 30)]


def obtener_sol(anio, mes, dia, hora, minuto, lat, lon, inconsciente):
    print(
        f"🛰️ Procesando Sol → {anio}-{mes}-{dia} {hora}:{minuto}, lat: {lat}, lon: {lon}"
    )
    print(f"inconsciente: {inconsciente}")
    if inconsciente: 
        offset= 0
    else:
        offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    print(f"horautc_decimal: {hora_utc_decimal}")
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Posición del Sol
    grados_sol = swe.calc_ut(jd, swe.SUN)[0][0]
    print(f"Grados Sol: {grados_sol}")
    signo = obtener_signo(grados_sol)
    grado_signo = grados_sol % 30
    print(f"Grado en signo: {grado_signo}")
    formato_dms = grados_a_dms(grado_signo)

    # Determinar casa
    casa = calcular_casa(jd, lat, lon, grados_sol)

    return {
        "signo": signo,
        "grados": round(grados_sol, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }

def obtener_tierra(anio, mes, dia, hora, minuto, lat, lon):
    
    sol= obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False)

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    # Posición del Sol
    grados_tierra = (sol["grados"]+180)%360
    
    signo = obtener_signo(grados_tierra)
    grado_signo = grados_tierra % 30
    
    formato_dms = grados_a_dms(grado_signo)

    # Determinar casa
    casa = calcular_casa(jd, lat, lon, grados_tierra)

    return {
        "signo": signo,
        "grados": round(grados_tierra, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }

def obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon):
    # Calcular hora UTC
    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    # Calcular día juliano
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Calcular casas y ascendente
    casas, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = ascmc[0]
    #print(f"valor asc {asc}")
    signo = obtener_signo(asc)
    grado_signo = asc % 30
    formato_dms = grados_a_dms(grado_signo)

    return {
        "ascendente_grado": round(asc, 2),
        "signo": signo,
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}"
    }


def obtener_luna(anio, mes, dia, hora, minuto, lat, lon):

    print(
        f"🛰️ Recibido en /luna → {anio}-{mes}-{dia} {hora}:{minuto}, lat: {lat}, lon: {lon}"
    )
    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Posición de la Luna
    grados_luna = swe.calc_ut(jd, swe.MOON)[0][0]
    signo = obtener_signo(grados_luna)
    grado_signo = grados_luna % 30
    formato_dms = grados_a_dms(grado_signo)

    #esto es una prueba de busqueda de error
    #print(f"Calculando casas con:")
    #print(f"JD: {jd}")
    #print(
    #    f"Lat: {lat}, Lon: {lon}, Offset: {offset}, Hora local: {hora}:{minuto}, Hora UTC: {hora_utc_decimal}"
    #)

    # Determinar casa
    casa = calcular_casa(jd, lat, lon, grados_luna)
    #print(f"lat: {lat}, lon: {lon}, offset: {offset}, hora_utc: {hora_utc_decimal}, jd: {jd}")

    return {
        "signo": signo,
        "grados": round(grados_luna, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    grados_mercurio = swe.calc_ut(jd, swe.MERCURY)[0][0]
    signo = obtener_signo(grados_mercurio)
    grado_signo = grados_mercurio % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_mercurio)
    return {
        "signo": signo,
        "grados": round(grados_mercurio, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_venus(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_venus = swe.calc_ut(jd, swe.VENUS)[0][0]
    signo = obtener_signo(grados_venus)
    grado_signo = grados_venus % 30
    formato_dms = grados_a_dms(grado_signo)

    #esto es una prueba de busqueda de error
    #print(f"Calculando casas con:")
    #print(f"JD: {jd}")
    #print(
    #    f"Lat: {lat}, Lon: {lon}, Offset: {offset}, Hora local: {hora}:{minuto}, Hora UTC: {hora_utc_decimal}"
    #)

    casa = calcular_casa(jd, lat, lon, grados_venus)

    return {
        "signo": signo,
        "grados": round(grados_venus, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_marte(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_marte = swe.calc_ut(jd, swe.MARS)[0][0]
    signo = obtener_signo(grados_marte)
    grado_signo = grados_marte % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_marte)

    return {
        "signo": signo,
        "grados": round(grados_marte, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_jupiter = swe.calc_ut(jd, swe.JUPITER)[0][0]
    signo = obtener_signo(grados_jupiter)
    grado_signo = grados_jupiter % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_jupiter)

    return {
        "signo": signo,
        "grados": round(grados_jupiter, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_saturno(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_saturno = swe.calc_ut(jd, swe.SATURN)[0][0]
    signo = obtener_signo(grados_saturno)
    grado_signo = grados_saturno % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_saturno)

    return {
        "signo": signo,
        "grados": round(grados_saturno, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_urano(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_urano = swe.calc_ut(jd, swe.URANUS)[0][0]
    signo = obtener_signo(grados_urano)
    grado_signo = grados_urano % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_urano)

    return {
        "signo": signo,
        "grados": round(grados_urano, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_neptuno = swe.calc_ut(jd, swe.NEPTUNE)[0][0]
    signo = obtener_signo(grados_neptuno)
    grado_signo = grados_neptuno % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_neptuno)

    return {
        "signo": signo,
        "grados": round(grados_neptuno, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_pluton(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_pluton = swe.calc_ut(jd, swe.PLUTO)[0][0]
    signo = obtener_signo(grados_pluton)
    grado_signo = grados_pluton % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_pluton)

    return {
        "signo": signo,
        "grados": round(grados_pluton, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_nodoN = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
    signo = obtener_signo(grados_nodoN)
    grado_signo = grados_nodoN % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_nodoN)

    return {
        "signo": signo,
        "grados": round(grados_nodoN, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Nodo Norte (MEAN Node)
    nodo_norte = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]

    # Nodo Sur = opuesto al Nodo Norte
    nodo_sur = (nodo_norte + 180) % 360

    signo = obtener_signo(nodo_sur)
    grado_signo = nodo_sur % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, nodo_sur)

    return {
        "signo": signo,
        "grados": round(nodo_sur, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_quiron(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_quiron = swe.calc_ut(jd, swe.CHIRON)[0][0]
    signo = obtener_signo(grados_quiron)
    grado_signo = grados_quiron % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_quiron)

    return {
        "signo": signo,
        "grados": round(grados_quiron, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_lilith(anio, mes, dia, hora, minuto, lat, lon):

    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    grados_lilith = swe.calc_ut(jd, 12)[0][0]  # Lilith media
    signo = obtener_signo(grados_lilith)
    grado_signo = grados_lilith % 30
    formato_dms = grados_a_dms(grado_signo)
    casa = calcular_casa(jd, lat, lon, grados_lilith)

    return {
        "signo": signo,
        "grados": round(grados_lilith, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }

def obtener_fase_lunar(grados_sol, grados_luna):
    diferencia = (grados_luna - grados_sol) % 360

    if diferencia <= 22.5 or diferencia > 337.5:
        return "LN"  # Luna Nueva
    elif diferencia <= 112.5:
        return "LC"  # Luna Creciente
    elif diferencia <= 202.5:
        return "LLL" # Luna Llena
    else:
        return "LM"  # Luna Menguante


def obtener_elemento(planetas_en_signos):
    
    contador = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
    for cuerpo, signo in planetas_en_signos.items():
        if cuerpo in PLANETAS_ELEMENTO_POLARIDAD:
            elemento = elemento_por_signo.get(signo)
            if elemento:
                contador[elemento] += 1
    max_val = max(contador.values())
    dominantes = [e for e, v in contador.items() if v == max_val]
    print("elemento", dict(contador))
    print(f"elem dominante {dominantes}")
    return "-".join(dominantes)

def obtener_polaridad(planetas_en_signos):
    contador = {"P": 0, "N": 0}
    for cuerpo, signo in planetas_en_signos.items():
        if cuerpo in PLANETAS_ELEMENTO_POLARIDAD:
            polaridad = polaridad_por_signo.get(signo)
            if polaridad:
                contador["P" if polaridad == "P" else "N"] += 1
    max_val = max(contador.values())
    dominantes = [p for p, v in contador.items() if v == max_val]
    print("polaridad", dict(contador))
    print("polaridad dominante", dominantes[0])
    return "-".join(dominantes)

    
def obtener_modalidad(planetas_en_signos):
    contador = {"Cardinal": 0, "Fija": 0, "Mutable": 0}

    for cuerpo, signo in planetas_en_signos.items():
        modalidad = modalidad_por_signo.get(signo)
        if modalidad and cuerpo in pesos:
            contador[modalidad] += pesos[cuerpo]
    max_val = max(contador.values())
    dominantes = [m for m, v in contador.items() if v == max_val]
    #print(f"modalidad ", list(dominantes))
    return "-".join(dominantes)
    
    

def calcular_numero_destino(dia, mes, anio):
    """
    Calcula el número de destino a partir de la fecha de nacimiento.
    - Suma los dígitos de la fecha.
    - Si el total inicial es 11, 22 o 33 → se mantiene.
    - Si no, se reduce hasta un solo dígito (1-9).
    
    Parámetro:
        fecha_nac (str): Fecha en formato 'dd/mm/yyyy' o 'dd-mm-yyyy'
    
    Retorna:
        int: Número de destino (1-9, 11, 22, 33)
    """
    # Convertir a string y sumar dígitos
    todos_digitos = str(dia) + str(mes) + str(anio)
    total = sum(int(d) for d in todos_digitos)
       
    # Verificar número maestro SOLO en la primera suma
    if total in [11, 22, 33]:
        return total
    
    # Reducir hasta un dígito (sin considerar números maestros)
    while total > 9:
        total = sum(int(c) for c in str(total))
    
    return total

def calcular_fractal(signo_sol, signo_asc):
    """
    Calcula el número de fractal a partir del signo solar y asc.
    
    Parámetros:
        signo_sol (str): Signo solar (ej: "ARIES", "TAURO", etc.)
        signo_asc (str): Signo asc (ej: "GEMINIS", "PISCIS", etc.)
    
    Retorna:
        int: Número de fractal (1-144)
    """
    # Normalizamos mayúsculas
    signo_sol = signo_sol.upper()
    signo_asc = signo_asc.upper()
    
    # Lista de signos en orden
    signos = ["ARIES", "TAURO", "GEMINIS", "CANCER", "LEO", "VIRGO",
              "LIBRA", "ESCORPIO", "SAGITARIO", "CAPRICORNIO", "ACUARIO", "PISCIS"]
    
    if signo_sol not in signos or signo_asc not in signos:
        raise ValueError("Signo inválido. Use uno de: " + ", ".join(signos))
    
    fila = signos.index(signo_sol)
    columna = signos.index(signo_asc)
    
    nro_fractal = fila * 12 + columna + 1
    return nro_fractal

#from datetime import datetime

def dia_y_rayo(dia, mes, anio):
    """
    Devuelve un diccionario con:
    - dia: Nombre del día en español
    - color: Color asociado al día según la tabla
    
    Tabla:
    DOMINGO=AZUL, LUNES=AMARILLO, MARTES=ROSA, MIÉRCOLES=BLANCO,
    JUEVES=VERDE, VIERNES=NARANJA, SÁBADO=VIOLETA.
    """
    fecha = datetime(anio, mes, dia)
    
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    colores = {
        "Lunes": "AMARILLO",
        "Martes": "ROSA",
        "Miércoles": "BLANCO",
        "Jueves": "VERDE",
        "Viernes": "NARANJA",
        "Sábado": "VIOLETA",
        "Domingo": "AZUL"
    }
    
    dia_nombre = dias_semana[fecha.weekday()]
    color = colores[dia_nombre]
    
    return {
        "dia": dia_nombre,
        "color": color
    }






def calcular_kin_onda(anio, mes, dia):
    valores_anio = {
    2065:164, 2064: 59, 2063:214, 2062:109, 2061:  4, 2060:159, 2059: 54, 2058:209, 2057:104, 2056:259, 2055:154,
    2054: 49, 2053:204, 2052: 99, 2051:254, 2050:149, 2049: 44, 2048:199, 2047: 94, 2046:249, 2045:144, 2044: 39,
    2043:194, 2042: 89, 2041:244, 2040:139, 2039: 34, 2038:189, 2037: 84, 2036:239, 2035:134, 2034: 29, 2033:184,
    2032: 79, 2031:234, 2030:129, 2029: 24, 2028:179, 2027: 74, 2026:229, 2025:124, 2024: 19, 2023:174, 2022: 69,
    2021:224, 2020:119, 2019: 14, 2018:169, 2017: 64, 2016:219, 2015:114, 2014:  9, 2013:164, 2012: 59, 2011:214,
    2010:109, 2009:  4, 2008:159, 2007: 54, 2006:209, 2005:104, 2004:259, 2003:154, 2002: 49, 2001:204, 2000: 99,
    1999:254, 1998:149, 1997: 44, 1996:199, 1995: 94, 1994:249, 1993:144, 1992: 39, 1991:194, 1990: 89, 1989:244,
    1988:139, 1987: 34, 1986:189, 1985: 84, 1984:239, 1983:134, 1982: 29, 1981:184, 1980: 79, 1979:234, 1978:129,
    1977: 24, 1976:179, 1975: 74, 1974:229, 1973:124, 1972: 19, 1971:174, 1970: 69, 1969:224, 1968:119, 1967: 14,
    1966:169, 1965: 64, 1964:219, 1963:114, 1962:  9, 1961:164, 1960: 59, 1959:214, 1958:109, 1957:  4, 1956:159,
    1955: 54, 1954:209, 1953:104, 1952:259, 1951:154, 1950: 49, 1949:204, 1948: 99, 1947:254, 1946:149, 1945: 44,
    1944:199, 1943: 94, 1942:249, 1941:144, 1940: 39, 1939:194, 1938: 89, 1937:244, 1936:139, 1935: 34, 1934:189,
    1933: 84, 1932:239, 1931:134, 1930: 29, 1929:184, 1928: 79, 1927:234, 1926:129, 1925: 24, 1924:179, 1923: 74,
    1922:229, 1921:124, 1920: 19, 1919:174, 1918: 69, 1917:224, 1916:119, 1915: 14, 1914:169, 1913: 64, 1912:219,
    1911:114, 1910:  9
}

    valores_mes = {
    1: 53, 2: 84, 3: 112,
    4: 143, 5: 173, 6: 204,
    7: 234, 8: 5, 9: 36,
    10: 66, 11: 97, 12: 127
}

    

    try:
        valor_anio = valores_anio[anio]
        valor_mes = valores_mes[mes]
        
        suma_total = valor_anio + valor_mes + dia
        nro_kin = suma_total if suma_total <= 260 else suma_total % 260
                
        nro_onda = ((nro_kin - 1) // 13) + 1
        tono = ((nro_kin - 1) % 13) + 1
        sello = ((nro_kin - 1) % 20) + 1
        
        #calculo cumple_kin
        
        fecha_cumple = cumple_kin(nro_kin)
       
       
        return {
            "nro_kin": nro_kin,
            "nro_onda": nro_onda,
            "nro_tono": tono,
            "nro_sello": sello,
            "cumple_kin": fecha_cumple

            
        }
    except Exception as e:
        return {"error": str(e)}




def cumple_kin(kin):
    """
    Calcula el próximo cumpleaños Kin desde HOY, basado en ciclos de 260 días.
    Parámetros:
        kin (int): número del kin (1-260)
    Retorna:
        dict: {
            "fecha": "dd/mm/yyyy",
            "dias_faltantes": int,
            "ciclo_inicio": "dd/mm/yyyy",
            "ciclo_fin": "dd/mm/yyyy"
        }
    """
    if not isinstance(kin, int) or kin < 1 or kin > 260:
        return {"error": "Kin inválido"}

    ciclo = 260
    hoy = datetime.now().date()
    inicio_base = datetime(2025, 3, 25).date()  # Primer ciclo de referencia

    # Días desde el inicio base
    dias_desde_inicio = (hoy - inicio_base).days

    # Cuántos ciclos completos han pasado
    ciclos_pasados = dias_desde_inicio // ciclo if dias_desde_inicio >= 0 else -1

    # Inicio del ciclo actual
    inicio_ciclo_actual = inicio_base + timedelta(days=ciclos_pasados * ciclo)
    if inicio_ciclo_actual > hoy:
        inicio_ciclo_actual -= timedelta(days=ciclo)

    # Fecha de kin en el ciclo actual
    fecha_kin = inicio_ciclo_actual + timedelta(days=(kin ))

    # Si ya pasó hoy, sumamos un ciclo
    if fecha_kin <= hoy:
        fecha_kin += timedelta(days=ciclo)
        inicio_ciclo_actual += timedelta(days=ciclo)

    #fin_ciclo_actual = inicio_ciclo_actual + timedelta(days=ciclo - 1)

    #dias_faltantes = (fecha_kin - hoy).days
    return fecha_kin.strftime("%d/%m/%Y")
    

 

'''
def procesar_kin_onda(anio, mes, dia):

    registro = {
        "nro_kin": calcular_kin_onda(anio, mes, dia)["nro_kin"],
        "nro_onda": calcular_kin_onda(anio, mes, dia)["nro_onda"],
        "nro_tono": calcular_kin_onda(anio, mes, dia)["nro_tono"],
        "nro_sello": calcular_kin_onda(anio, mes, dia)["nro_sello"],
       
        
    } 
    return registro;
'''


def procesar(anio, mes, dia, hora, minuto, lat, lon):

    """
    Esta función recibe un número de identificación (nh) y realiza los siguientes pasos:
    1. Busca los datos de nacimiento (fecha_nac, hora_nac, lat, lon) desde una tabla en Supabase.
    2. Calcula los datos astrológicos completos usando una función existente (planetas, grados, casas, etc.).
    3. A partir de los grados zodiacales del Sol y Tierra (consciente e inconsciente), calcula:
       - El perfil de Diseño Humano (líneas del Sol consciente e inconsciente).
       - El tipo de Diseño Humano (Generador, Proyector, Manifestador, Reflector) según los centros definidos.
       - La cruz de encarnación, usando las puertas del Sol y Tierra.
    4. Devuelve un diccionario con todos los datos calculados.

    Requiere funciones auxiliares:
    - obtener_linea(grado): devuelve la línea 1–6 según el grado zodiacal.
    - calcular_perfil(grado_sol_consciente, grado_sol_inconsciente)
    - calcular_tipo(canales_activos)
    - calcular_cruz(puerta_sol, puerta_tierra)

    Las puertas se obtienen a partir de los grados zodiacales de los planetas usando una tabla de mapeo.
    """

    

    # Ahora sí: llamás a las funciones de los planetas
    sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False)
    luna = obtener_luna(anio, mes, dia, hora, minuto, lat, lon)
    mercurio = obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon)
    venus = obtener_venus(anio, mes, dia, hora, minuto, lat, lon)
    marte = obtener_marte(anio, mes, dia, hora, minuto, lat, lon)
    jupiter = obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon)
    saturno = obtener_saturno(anio, mes, dia, hora, minuto, lat, lon)
    urano = obtener_urano(anio, mes, dia, hora, minuto, lat, lon)
    neptuno = obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon)
    pluton = obtener_pluton(anio, mes, dia, hora, minuto, lat, lon)
    quiron = obtener_quiron(anio, mes, dia, hora, minuto, lat, lon)
    lilith = obtener_lilith(anio, mes, dia, hora, minuto, lat, lon)
    ascendente =  obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon)
    nodoN = obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon)
    nodoS = obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon)
    fase = obtener_fase_lunar(sol["grados"], luna["grados"])
    tierra = obtener_tierra(anio, mes, dia, hora, minuto, lat, lon)
    # Crear el diccionario con los signos
    planetas_en_signos = {
        "Sol": sol["signo"],
        "Luna": luna["signo"],
        "Mercurio": mercurio["signo"],
        "Venus": venus["signo"],
        "Marte": marte["signo"],
        "Jupiter": jupiter["signo"],
        "Saturno": saturno["signo"],
        "Asc": ascendente["signo"]
    
    }
    
    anio_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["anio_i"]
    mes_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["mes_i"]
    dia_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["dia_i"]
    hora_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["hora_i"]
    min_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["minuto_i"]
    
    grados_in =88.3
    #grados_inlun = 88*12.92

    
    sol_inconsciente =      (sol["grados"]-grados_in)%360
    print(f"grado sol inconsciente {sol_inconsciente}")
    tierra_inconsciente =   (tierra["grados"]-grados_in)%360
    '''
    fecha_natal = datetime(anio, mes, dia, hora, minuto)
    deltain = timedelta(days=88, hours=7, minutes=12, seconds=50) # 0.3 días ≈ 7h12m
    fecha_inco= fecha_natal - deltain
    fecha_inco = fecha_inco.replace(hour=0, minute=0, second=0, microsecond=0)
    '''
    luna_inconsciente =     obtener_luna(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    #luna_inconsciente =     (luna["grados"]-grados_inlun)%360
        
    nodon_inconsciente =    obtener_nodoN(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    nodos_inconsciente =    obtener_nodo_sur(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    mercurio_inconsciente = obtener_mercurio(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    venus_inconsciente =    obtener_venus(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    marte_inconsciente =    obtener_marte(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    jupiter_inconsciente =  obtener_jupiter(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    saturno_inconsciente =  obtener_saturno(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    urano_inconsciente =    obtener_urano(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    neptuno_inconsciente =  obtener_neptuno(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    pluton_inconsciente =   obtener_pluton(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)["grados"]
    
    
    #grado_sol_inconsciente = sol["grados"]- grados_in
    # Obtener puertas activadas por los planetas
    puertas_activadas = []
    
    for planetas in [sol, tierra, luna, nodoN, nodoS, mercurio, venus, marte, jupiter, saturno, urano, neptuno, pluton,
                     ]:
        tolerancia = 0
        puerta_dict = obtener_puerta(planetas["grados"], tolerancia)
        puerta = puerta_dict["puerta"] if puerta_dict else None
        print(f"puerta activa : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)
        
    for nombre, grado_inconsciente in zip(["sol_inconsciente","tierra_inconsciente", "luna_inconsciente", "nodon_inconsciente", "nodoS_inconsciente", "mercurio_inconsciente", 
         "venus_inconsciente", "marte_inconsciente", "jupiter_inconsciente", "saturno_inconsciente", "urano_inconsciente", 
         "neptuno_inconsciente", "pluton_inconsciente"],
        [sol_inconsciente, tierra_inconsciente, luna_inconsciente, nodon_inconsciente, nodos_inconsciente,
                     mercurio_inconsciente, venus_inconsciente, marte_inconsciente, jupiter_inconsciente, saturno_inconsciente,
                     urano_inconsciente, neptuno_inconsciente, pluton_inconsciente]):
        # Para los planetas inconscientes,
        tolerancia = 0
        puerta_dict = obtener_puerta(grado_inconsciente, tolerancia)
        puerta = puerta_dict["puerta"] if puerta_dict else None
        print(f"puerta activa :{nombre} : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)

    # Detectar canales activos
    canales_activos = detectar_canales(puertas_activadas)
    print(f"canales activos: {canales_activos}")
    # Calcular tipo
    tipo = calcular_tipo(canales_activos)
    print(f"tipo dh {tipo}")
    
    perfil = calcular_perfil( sol["grados"], sol_inconsciente)
    print(f"perfil dh {perfil}")
    print(f"grado_sol_iconsciente dh {sol_inconsciente}")
    print(f"grado_sol_consciente dh {sol["grados"]}")
    #tipo = calcular_tipo(canales_activos)
    #cruz = calcular_cruz(puerta_sol, puerta_tierra)

    print(f"Perfil: {perfil}")
    print(f"Tipo: {tipo}")
    #print(f"Cruz de encarnación: {cruz}")
    registro = {
        "fecha_nac": date(anio, mes, dia),
        "hora": hora,
        "minuto": minuto,
        "lat": lat,
        "lon": lon,
        "sol": sol["signo"],
        "luna": luna["signo"],
        "mercurio": mercurio["signo"],
        "venus": venus["signo"],
        "marte": marte["signo"],
        "jupiter": jupiter["signo"],
        "saturno": saturno["signo"],
        "urano": urano["signo"],
        "neptuno": neptuno["signo"],
        "pluton": pluton["signo"],
        "quiron": quiron["signo"],
        "lilith": lilith["signo"],
        "luna_nac": fase,
        "gr_sol": sol["grado_en_signo"],
        "c_sol": sol["casa"],
        "ascen": obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon),
        "gr_asc": ascendente["grado_en_signo"],
        "gr_luna": luna["grado_en_signo"],
        "c_luna": luna["casa"],
        "gr_merc": mercurio["grado_en_signo"],
        "c_merc":  mercurio["casa"],
        "gr_venus": venus["grado_en_signo"],
        "c_venus": venus["casa"],
        "gr_marte": marte["grado_en_signo"],
        "c_marte": marte["casa"],
        "gr_jupiter": jupiter["grado_en_signo"],
        "c_jupiter": jupiter["casa"],
        "gr_satur": saturno["grado_en_signo"],
        "c_satur": saturno["casa"],
        "gr_urano": urano["grado_en_signo"],
        "c_urano": urano["casa"],
        "gr_neptu": neptuno["grado_en_signo"],
        "c_neptu": neptuno["casa"],
        "gr_pluto": pluton["grado_en_signo"],
        "c_pluto": pluton["casa"],
        "nodon": nodoN["signo"],
        "gr_nodon": nodoN["grado_en_signo"],
        "c_nodon": nodoN["casa"],
        "nodoS": nodoS["signo"],
        "gr_nodos":nodoS["grado_en_signo"],
        "c_nodoS": nodoS["casa"],
        "gr_lilith": lilith["grado_en_signo"],
        "c_lilith":  lilith["casa"],
        "gr_quiron": quiron["grado_en_signo"],
        "c_quiron":  quiron["casa"],
        "elemento": obtener_elemento(planetas_en_signos),
        "polaridad": obtener_polaridad(planetas_en_signos),
        "modalidad": obtener_modalidad(planetas_en_signos),
        "n_destino": calcular_numero_destino(dia, mes, anio),
        "fr_144": calcular_fractal(sol["signo"], ascendente["signo"]),
        "dia_llegada": dia_y_rayo(dia, mes, anio)["dia"],
        "rayo": dia_y_rayo(dia, mes, anio)["color"],
        "tipo_dh": tipo,
        "perfil": perfil
        
        
        
    }
    #if request.args.get("modo") == "string":
    return "-".join(str(v) for v in registro.values())
   # else:
    #    return registro
    #return registro



def marcar_procesado_en_rtas_form(supabase: Client, nh: str):
    
    """
    Marca como procesado=True en la tabla rtas_form para el registro con nh dado.
    """
    try:
        response = supabase.table("rtas_form").update({"procesado": True}).eq("nh", nh).execute()
        if response.data:
            print(f"Registro con nh={nh} actualizado como procesado.")
            return True
        else:
            print(f"No se encontró el registro con nh={nh}.")
            return False
    except Exception as e:
        print(f"Error al actualizar procesado: {e}")
        return False
   

def obtener_puerta(grado, tolerancia):
    """
    Devuelve el número de puerta correspondiente al grado zodiacal.
    Si el grado está a menos de `tolerancia` del fin de la puerta, devuelve la puerta siguiente.
    """
    for i, puerta_dict in enumerate(tabla_puertas):
        inicio = puerta_dict["inicio"]
        fin = puerta_dict["fin"]
        puerta = puerta_dict["puerta"]
        # Manejo de rangos normales
        if inicio < fin:
            if inicio <= grado < fin:
                '''
                # Si está cerca del fin, buscar la puerta siguiente
                if fin - grado < tolerancia:
                    # Buscar la puerta cuyo inicio sea fin (la siguiente en la tabla)
                    for siguiente in tabla_puertas:
                        if abs(siguiente["inicio"] - fin) < 0.001:
                            return siguiente
                if grado - inicio < tolerancia: 
                    for anterior in tabla_puertas:
                        if abs(anterior["fin"] - inicio) < 0.001:
                            return anterior  
                '''                 
                return puerta_dict
        else:
            # Rango que cruza 0 Aries
            if grado >= inicio or grado < fin:
                '''
                if (fin - grado) % 360 < tolerancia:
                    for siguiente in tabla_puertas:
                        if abs(siguiente["inicio"] - fin) < 0.001:
                            return siguiente
                if (grado - inicio) % 360 < tolerancia:
                    for anterior in tabla_puertas:
                        if abs(anterior["fin"] - inicio) < 0.001:
                            return anterior   
                '''                 
                return puerta_dict
    return puerta_dict



def obtener_linea(grado, tolerancia):
    """
    Devuelve la línea (1 a 6) dentro de la puerta, según el grado zodiacal.
    """
    puerta = obtener_puerta(grado, tolerancia)
    if puerta is None:
        return None
    inicio = puerta["inicio"]
    grado_relativo = grado - inicio
    linea = int(grado_relativo // 0.9375) + 1
    print(f"linea {puerta}- {grado} - gr_relativo {grado_relativo} - {linea}")
    if linea < 1:
        linea = 1
    return min(linea, 6)


def calcular_perfil( grado_sol_consciente, grado_sol_inconsciente):
    '''
    Devuelve el perfil como string, por ejemplo '3/5'.
    '''
    linea_consciente = obtener_linea(grado_sol_consciente, 0)
    linea_inconsciente = obtener_linea(grado_sol_inconsciente, 0)
    
    return f"{linea_consciente}/{linea_inconsciente}"




# Función para calcular el tipo según centros definidos
def calcular_tipo(canales_activos):
    centros_por_canal = {
        "1-8": ["G", "Garganta"],
        "2-14": ["Sacral", "G"],
        "3-60": ["Raíz", "Sacral"],
        "4-63": ["Cabeza", "Ajna"],
        "5-15": ["Sacral", "G"],
        "6-59": ["Sacral", "Emocional"],
        "7-31": ["G", "Garganta"],
        "9-52": ["Sacral", "Raíz"],
        "10-20": ["G", "Garganta"],
        "11-56": ["Ajna", "Garganta"],
        "12-22": ["Emocional", "Garganta"],
        "13-33": ["G", "Garganta"],
        "16-48": ["Bazo", "Garganta"],
        "17-62": ["Ajna", "Garganta"],
        "18-58": ["Bazo", "Raíz"],
        "19-49": ["Raíz", "Emocional"],
        "20-34": ["Garganta", "Sacral"],
        "21-45": ["Corazón", "Garganta"],
        "22-12": ["Emocional", "Garganta"],
        "23-43": ["Garganta", "Ajna"],
        "24-61": ["Ajna", "Cabeza"],
        "25-51": ["G", "Corazón"],
        "26-44": ["Corazón", "Bazo"],
        "27-50": ["Sacral", "Bazo"],
        "28-38": ["Bazo", "Raíz"],
        "29-46": ["Sacral", "G"],
        "30-41": ["Emocional", "Raíz"],
        "32-54": ["Bazo", "Raíz"],
        "34-57": ["Sacral", "Bazo"],
        "35-36": ["Garganta", "Emocional"],
        "37-40": ["Emocional", "Corazón"],
        "39-55": ["Raíz", "Emocional"],
        "42-53": ["Sacral", "Raíz"],
        "47-64": ["Ajna", "Cabeza"],
        "48-16": ["Bazo", "Garganta"],
        "49-19": ["Emocional", "Raíz"],
        "57-10": ["Bazo", "G"],
    }
    centros_definidos = set()
    for canal in canales_activos:
        centros = centros_por_canal.get(canal, [])
        centros_definidos.update(centros)

    tiene_sacral = "Sacral" in centros_definidos
    tiene_garganta = "Garganta" in centros_definidos
    tiene_motor = any(c in centros_definidos for c in ["Sacral", "Corazón", "Emocional", "Raíz"])

    # Generador Manifestante: Sacral y Garganta conectados directamente (por canal 20-34)
    if "20-34" in canales_activos:
        return "GM"
    elif tiene_sacral and tiene_garganta:
        return "GM"
    elif tiene_sacral:
        return "G"
    elif tiene_garganta and tiene_motor:
        return "M"
    elif centros_definidos:
        return "P"
    else:
        return "R"    

def detectar_canales(puertas_activadas):
    """
    Devuelve una lista de canales activos a partir de las puertas activadas.
    """
    canales_posibles = {
    "1-8", "2-14", "3-60", "4-63", "5-15", "6-59", "7-31", "9-52",
    "10-20", "11-56", "12-22", "13-33", "16-48", "17-62", "18-58",
    "19-49", "20-34", "21-45", "22-12", "23-43", "24-61", "25-51",
    "26-44", "27-50", "28-38", "29-46", "30-41", "32-54", "34-57",
    "35-36", "37-40", "39-55", "42-53", "47-64", "48-16", "49-19", "57-10"
}
   
    canales = []
    puertas_set = set(puertas_activadas)
    for canal in canales_posibles:
        p1, p2 = map(int, canal.split("-"))
        if p1 in puertas_set and p2 in puertas_set:
            canales.append(canal)
    return canales


# Función para calcular la cruz de encarnación (simplificada)
def calcular_cruz(puerta_sol, puerta_tierra):
    cruces = {
        (15, 10): "Cruz del Ritmo",
        (59, 55): "Cruz de la Penetración",
        (34, 20): "Cruz del Servicio",
        (43, 23): "Cruz de la Explicación",
        # Agregá más combinaciones si querés
    }
    return cruces.get((puerta_sol, puerta_tierra), "Cruz desconocida")



@app.route('/calcular')
def calcular():
    configurar_swisseph()
    nh = request.args.get('nh')
    if not nh:
        return jsonify({"error": "Falta parámetro nh"}), 400

    try:
        res = supabase.table("rtas_form").select("*").eq("nh", nh).execute()
        if not res.data:
            return jsonify({"error": f"No se encontró nh={nh}"}), 404

        fila = res.data[0]

        # Parseo de datos
        anio, mes, dia = map(int, fila['fecha_nac'].split('-'))
        hora_str, minuto_str, *_ = fila['hora_nac'].split(':')
        hora = int(hora_str)
        minuto = int(minuto_str)
        lat = float(fila['lat'])
        lon = float(fila['lon'])

        # Llamar a función principal
        resultado = procesar(anio, mes, dia, hora, minuto, lat, lon)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calcular_kinmaya')
def api_calcular_kinmaya():
    nh = request.args.get('nh')
    if not nh:
        return jsonify({"error": "Falta parámetro nh"}), 400

    try:
        res = supabase.table("rtas_form").select("*").eq("nh", nh).execute()
        if not res.data:
            return jsonify({"error": f"No se encontró nh={nh}"}), 404

        fila = res.data[0]

        # Parseo de datos
        anio, mes, dia = map(int, fila['fecha_nac'].split('-'))
        #hora_str, minuto_str, *_ = fila['hora_nac'].split(':')
        
        

        # Llamar a función principal
        resultado = calcular_kin_onda(anio, mes, dia)

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cumplekin', methods=['GET'])
def api_cumple_kin():
    try:
        kin_param = request.args.get('kin')
        kin = int(kin_param)
        fecha = cumple_kin(kin)
        if fecha:
            return jsonify({"fecha": fecha})
        else:
            return jsonify({"error": "Kin inválido"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/guardar', methods=['POST'])
def guardar_datos():
    configurar_swisseph()
    #print("Ruta actual del proceso:", os.getcwd())
    #print("Archivos disponibles en sweph/ephe:", os.listdir("sweph/ephe"))
   
    try:
        data = request.get_json()
        nh = data.get("nh")
        tipo_dh = data.get("tipo_dh")
        perfil = data.get("perfil")
        fecha_nac = data.get("fecha_nac")  
        hora_nac = data.get("hora_nac")    
        lat = data.get("lat")
        lon = data.get("lon")
        anio, mes, dia = map(int, fecha_nac.split('-'))
        hora, minuto = map(int, hora_nac.split(':'))



        if not nh or not tipo_dh or not perfil or not fecha_nac or not hora_nac :
            return jsonify({"error": "Faltan datos obligatorios"}), 400
        '''
        # 1. Buscar datos personales en rtas_form
        res = supabase.table("rtas_form").select("*").eq("nh", nh).execute()
        if not res.data:
            return jsonify({"error": f"No se encontró nh={nh}"}), 404

        fila = res.data[0]
        # Extraer fecha, hora, lat, lon
        anio, mes, dia = map(int, fila['fecha_nac'].split('-'))
        hora, minuto = map(int, fila['hora_nac'].split(':'))
        lat = float(fila['lat'])
        lon = float(fila['lon'])
        '''
            # Ahora sí: llamás a las funciones de los planetas
        sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False)
        luna = obtener_luna(anio, mes, dia, hora, minuto, lat, lon)
        mercurio = obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon)
        venus = obtener_venus(anio, mes, dia, hora, minuto, lat, lon)
        marte = obtener_marte(anio, mes, dia, hora, minuto, lat, lon)
        jupiter = obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon)
        saturno = obtener_saturno(anio, mes, dia, hora, minuto, lat, lon)
        urano = obtener_urano(anio, mes, dia, hora, minuto, lat, lon)
        neptuno = obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon)
        pluton = obtener_pluton(anio, mes, dia, hora, minuto, lat, lon)
        quiron = obtener_quiron(anio, mes, dia, hora, minuto, lat, lon)
        lilith = obtener_lilith(anio, mes, dia, hora, minuto, lat, lon)
        ascendente =  obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon)
        nodoN = obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon)
        nodoS = obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon)
    
        
         
        # Crear el diccionario con los signos
        planetas_en_signos = {
            "Sol": sol["signo"],
            "Luna": luna["signo"],
            "Mercurio": mercurio["signo"],
            "Venus": venus["signo"],
            "Marte": marte["signo"],
            "Jupiter": jupiter["signo"],
            "Saturno": saturno["signo"],
            "Asc": ascendente["signo"]
           # "Urano": urano["signo"],
           # "Neptuno": neptuno["signo"],
           # "Plutón": pluton["signo"],
           # "Quiron": quiron["signo"],
           # "Lilith": lilith["signo"]
        }

  
        
        fractal = calcular_fractal(sol["signo"], ascendente["signo"])
        numero_destino = calcular_numero_destino(dia, mes, anio)
        nro_kin = calcular_kin_onda(anio, mes, dia)["nro_kin"]
        elemento = obtener_elemento(planetas_en_signos)
        polaridad = obtener_polaridad(planetas_en_signos)
        modalidad = obtener_modalidad(planetas_en_signos)
        fase = obtener_fase_lunar(sol["grados"], luna["grados"])
        rayo  = dia_y_rayo(dia, mes, anio)["color"]
        dia_llegada = dia_y_rayo(dia, mes, anio)["dia"]
        fecha_cumple = cumple_kin(nro_kin)
        fecha_obj = datetime.strptime(fecha_cumple, '%d/%m/%Y')
        fecha_iso = fecha_obj.strftime('%Y-%m-%d')  # Para guardar en Supabase

        # 3. Registro final para datoscc
        registro = {
            "nh": nh,
            "sol": sol["signo"],
            "luna": luna["signo"],
            "mercurio": mercurio["signo"],
            "venus": venus["signo"],
            "marte": marte["signo"],
            "jupiter": jupiter["signo"],
            "saturno": saturno["signo"],
            "urano": urano["signo"],
            "neptuno": neptuno["signo"],
            "pluton": pluton["signo"],
            "quiron": quiron["signo"],
            "lilith": lilith["signo"],
            "gr_sol": sol["grados"],
            "gr_luna": luna["grados"],
            "luna_nac": fase,
            "gr_sol": sol["grado_en_signo"],
            "c_sol": sol["casa"],
            "ascen": ascendente["signo"],
            "gr_asc": ascendente["grado_en_signo"],
            "gr_luna": luna["grado_en_signo"],
            "c_luna": luna["casa"],
            "gr_merc": mercurio["grado_en_signo"],
            "c_merc":  mercurio["casa"],
            "gr_venus": venus["grado_en_signo"],
            "c_venus": venus["casa"],
            "gr_marte": marte["grado_en_signo"],
            "c_marte": marte["casa"],
            "gr_jupiter": jupiter["grado_en_signo"],
            "c_jupiter": jupiter["casa"],
            "gr_satur": saturno["grado_en_signo"],
            "c_satur": saturno["casa"],
            "gr_urano": urano["grado_en_signo"],
            "c_urano": urano["casa"],
            "gr_neptu": neptuno["grado_en_signo"],
            "c_neptu": neptuno["casa"],
            "gr_pluto": pluton["grado_en_signo"],
            "c_pluto": pluton["casa"],
            "nodon": nodoN["signo"],
            "gr_nodon": nodoN["grado_en_signo"],
            "c_nodon": nodoN["casa"],
            "nodos": nodoS["signo"],
            "gr_nodos": nodoS["grado_en_signo"],
            "c_nodos": nodoS["casa"],
            "gr_lilith": lilith["grado_en_signo"],
            "c_lilith":  lilith["casa"],
            "gr_quiron": quiron["grado_en_signo"],
            "c_quiron":  quiron["casa"],
            "elemento": elemento,
            "polaridad": polaridad,
            "modalidad": modalidad,
            "n_destino": numero_destino,
            "n_fractal": fractal,
            "dia_llegada": dia_llegada,
            "rayo": rayo,
            "nro_kin": calcular_kin_onda(anio, mes, dia)["nro_kin"],
            "nro_onda": calcular_kin_onda(anio, mes, dia)["nro_onda"],
            "nro_sello": calcular_kin_onda(anio, mes, dia)["nro_sello"],
            "nro_tono": calcular_kin_onda(anio, mes, dia)["nro_tono"],
            "cumple_kin": fecha_iso ,
            "tipo_dh": tipo_dh,
            "perfil": perfil
       
        }

         # 2. Insertar en datoscc
        response = supabase.table("datoscc").insert(registro).execute()

        # 3. Chequear resultado antes de marcar procesado
        if response.data:
            marcar_procesado_en_rtas_form(supabase, nh)
            return jsonify({"status": "ok", "inserted": response.data})
        else:
            return jsonify({"error": "No se pudo insertar en datoscc"}), 500

        # return jsonify(dict(registro)) ## para pruebas

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/procesa_datos', methods=['POST'])
def api_procesa_datos():
    configurar_swisseph()
    try:
        data = request.get_json()
        anio = int(data["anio"])
        mes = int(data["mes"])
        dia = int(data["dia"])
        hora = int(data["hora"])
        minuto = int(data["minuto"])
        lat = float(data["lat"])
        lon = float(data["lon"])
        modo = request.args.get("modo", "json")
        resultado = procesar(anio, mes, dia, hora, minuto, lat, lon)
        if modo == "string":
            return resultado
        else:
            return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route('/')
def home():
    return "✅ API Carnet Cósmico funcionando. Usá /calcular?nh=..."


if __name__ == '__main__':
    configurar_swisseph()
    app.run(host="0.0.0.0", port=5000, debug=True)

