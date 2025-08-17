from timezonefinder import TimezoneFinder
TF = TimezoneFinder(in_memory=True)  # evita leer desde disco en cada request
from flask import Flask, request, jsonify, abort
from supabase import create_client, Client
import swisseph as swe
import requests
from datetime import date
from datetime import datetime, timedelta
import pytz
import os, hmac
import math
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv



API_SECRET = os.environ.get("API_SHARED_SECRET")

def require_api_key():
    # Comparación en tiempo constante
    provided = request.headers.get("X-API-KEY", "")
    if not API_SECRET or not hmac.compare_digest(provided, API_SECRET):
        abort(401)  # Unauthorized





def configurar_swisseph():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweph", "ephe")
    swe.set_ephe_path(ruta)
    print("Swiss Ephemeris configurado en:", ruta)



app = Flask(__name__)


# Carga .env junto a este archivo, sin depender de desde dónde ejecutes
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

#SUPABASE_URL = "https://amjskrqaoiuabscecmji.supabase.co"
#SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtanNrcnFhb2l1YWJzY2VjbWppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5Nzg3NDksImV4cCI6MjA2NjU1NDc0OX0.t_9h25ehDGBWGz39YmMPdeeaFyWpQcoDR0POt5Y3CXQ"
#SUPABASE_KEY = "sb_secret_PQ9R_OaevJPdpIHr-voFOg_avwtWZdK"
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]   # service_role
if not url or not key:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en variables de entorno")

supabase = create_client(url, key)

#supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

PLANETAS_ELEMENTO_POLARIDAD = ["Sol", "Luna", "Mercurio", "Venus", "Marte", "Jupiter", "Saturno", 
                               "Asc", "MC", "Neptuno", "Urano", "Pluton"] 

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
    #print(f"fecha inconsciente: {fecha_inconsciente}")
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

''''
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
'''

def obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    tzname = TF.timezone_at(lat=float(lat), lng=float(lon)) \
             or TF.closest_timezone_at(lat=float(lat), lng=float(lon))
    dt_local = datetime(anio, mes, dia, hora, minuto, tzinfo=ZoneInfo(tzname))
    return dt_local.astimezone(ZoneInfo("UTC")), tzname
'''
def obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    tzname = TimezoneFinder().timezone_at(lat=lat, lng=lon) or \
             TimezoneFinder().closest_timezone_at(lat=lat, lng=lon)
    #print(f"Zona horaria encontrada: {tzname}")
    dt_local = datetime(anio, mes, dia, hora, minuto, tzinfo=ZoneInfo(tzname))
    #print(f"Fecha y hora local: {dt_local}")
    return dt_local.astimezone(ZoneInfo("UTC")), tzname
'''



'''
TF = TimezoneFinder(in_memory=True)

def jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, override_offset_hours=None):
    # 1) tz IANA por coordenadas
    tzname = TF.timezone_at(lat=float(lat), lng=float(lon)) \
             or TF.closest_timezone_at(lat=float(lat), lng=float(lon)) \
             or "UTC"
    dt_local = datetime(anio, mes, dia, hora, minuto, tzinfo=ZoneInfo(tzname))

    # 2) Modo override explícito (solo para debug/manual)
    if override_offset_hours is not None:
        dt_utc = datetime(anio, mes, dia, hora, minuto) - timedelta(hours=float(override_offset_hours))
        mode = f"override_{override_offset_hours:+.1f}h"
    else:
        # 3) Cálculo normal con zoneinfo
        dt_utc_zoneinfo = dt_local.astimezone(ZoneInfo("UTC"))
        off_hours = dt_local.utcoffset().total_seconds() / 3600.0
        mode = f"zoneinfo({off_hours:+.1f}h)"

        # 4) Parche Argentina: si devuelve -2h entre OCT–MAR, forzamos -3h
        if tzname.startswith("America/Argentina/"):
            if off_hours > -3.0 and mes in (10, 11, 12, 1, 2, 3):
                dt_utc = datetime(anio, mes, dia, hora, minuto) - timedelta(hours=3)
                mode = f"AR_patch_-3_from_{off_hours:+.1f}h"
            else:
                dt_utc = dt_utc_zoneinfo
        else:
            dt_utc = dt_utc_zoneinfo

    h = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)
    return jd, tzname, dt_utc, mode
'''


TF = TimezoneFinder(in_memory=True)

AR_TZS = ("America/Argentina/",)  # prefijo
CL_TZS = ("America/Santiago", "America/Punta_Arenas", "Pacific/Easter")
UY_TZS = ("America/Montevideo",)

def _canon_pais(p):
    p = (p or "").strip().lower()
    if p in ("argentina","ar"): return "AR"
    if p in ("chile","cl"):     return "CL"
    if p in ("uruguay","uy"):   return "UY"
    if p in ("brasil","brazil","br"): return "BR"
    return None

def _es_argentina(lat, lon):
    # bbox amplia y barata
    return (-55.2 <= lat <= -21.8) and (-74.1 <= lon <= -53.5)

def _es_magallanes(lat, lon):
    # muy aproximado para preferir America/Punta_Arenas
    return (-54.0 <= lat <= -48.0) and (-76.0 <= lon <= -66.0)

def _es_isla_de_pascua(lat, lon):
    return (-28.5 <= lat <= -26.0) and (-111.0 <= lon <= -108.0)

def _tz_desde_coords(lat, lon, country_hint=None):
    tz = TF.timezone_at(lat=float(lat), lng=float(lon)) \
         or TF.closest_timezone_at(lat=float(lat), lng=float(lon))
    ch = _canon_pais(country_hint)
    #print(f"TZ desde coords: {lat}, {lon} → {tz} (hint: {ch})")

    # Si el usuario dijo un país, priorizamos ese país SOLO si las coords encajan
    if ch == "AR" and _es_argentina(lat, lon) and not (tz and tz.startswith(AR_TZS)):
        tz = "America/Argentina/Buenos_Aires"
    elif ch == "CL":
        if _es_isla_de_pascua(lat, lon):
            tz = "Pacific/Easter"
        elif _es_magallanes(lat, lon):
            tz = "America/Punta_Arenas"
        else:
            tz = "America/Santiago"
    elif ch == "UY":
        tz = "America/Montevideo"
    # Para BR u otros, no forzamos nada: confiamos en TF.

    return tz or "UTC"

def jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, override_offset_hours=None):
    tzname = _tz_desde_coords(lat, lon, country_hint)
    #print(f"ASC Zona horaria detectada: {tzname}")
    dt_local = datetime(anio, mes, dia, hora, minuto, tzinfo=ZoneInfo(tzname))

    if override_offset_hours is not None:
        dt_utc = datetime(anio, mes, dia, hora, minuto) - timedelta(hours=float(override_offset_hours))
        mode = f"override_{override_offset_hours:+.1f}h"
    else:
        dt_utc_zoneinfo = dt_local.astimezone(ZoneInfo("UTC"))
        off_hours = dt_local.utcoffset().total_seconds() / 3600.0
        mode = f"zoneinfo({off_hours:+.1f}h)"

        # Parche SOLO para Argentina (nunca Chile/Uruguay/Brasil)
        if tzname.startswith("America/Argentina") and mes in (10,11,12,1,2,3) and off_hours > -3.0:
            dt_utc = datetime(anio, mes, dia, hora, minuto) - timedelta(hours=3)
            mode = f"AR_patch_-3_from_{off_hours:+.1f}h"
        else:
            dt_utc = dt_utc_zoneinfo

    h = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)
    return jd, tzname, dt_utc, mode


def _asc_from_dt_utc(dt_utc, lat, lon):
    """Calcula ASC (0–360) desde un datetime ya en UTC."""
    h = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)
    _, ascmc = swe.houses(jd, float(lat), float(lon), 'P')
    return float(ascmc[0])

def jd_ut(anio, mes, dia, hora, minuto, lat, lon):
    dt_utc, tzname = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    h = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    print(f"dt_utc: {dt_utc}, h: {h}, tzname: {tzname}")
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)
    return jd, tzname, dt_utc

def _casas_1_a_12(jd, lat, lon, hsys='P'):
    cusps_raw, _ = swe.houses(jd, float(lat), float(lon), hsys)
    if len(cusps_raw) == 13:
        casas = list(cusps_raw[1:13])   # 1..12
    elif len(cusps_raw) == 12:
        casas = list(cusps_raw)         # ya viene 1..12
    else:
        raise ValueError(f"Formato de cúspides inesperado: len={len(cusps_raw)} -> {cusps_raw}")
    if len(casas) != 12:
        raise ValueError(f"Cúspides incompletas: len={len(casas)} (deben ser 12)")
    return casas


def calcular_casa(jd, lat, lon, grado_planeta):
    casas = _casas_1_a_12(jd, lat, lon, b'P')
    g = grado_planeta % 360.0

    # Convención para empatar con carta-natal.es:
    # el tramo [cusp[i], cusp[i+1]) pertenece a la Casa (i+1)+1
    for i in range(12):                     # i = 0..11 => cusp 1..12
        a = casas[i]
        b = casas[(i + 1) % 12]             # wrap 12→1
        cruza = a > b                       # cruce 360→0
        if (not cruza and a <= g < b) or (cruza and (g >= a or g < b)):
            h = (i + 1) % 12     # tu convención de “siguiente casa”
            return 12 if h == 0 else h
            
        
    return 12


'''
def calcular_casa(jd, lat, lon, grado_planeta):
    cusps, _ = swe.houses(jd, lat, lon, b'P')   # Placidus
    #print(f"Cúspides de casas: {cusps}")
    casas = cusps[1:13]                        # 12 cúspides reales (1..12)
    #print(f"Casas: {casas}")
    g = grado_planeta % 360

    for i in range(12):
        a = casas[i]
        b = casas[(i + 1) % 12]
        cruza = (a > b)  # cruce 360→0
        if (not cruza and a <= g < b) or (cruza and (g >= a or g < b)):
            # sector [cúspide i, cúspide i+1) es la Casa i+1
            return ((i + 1) % 12) + 1

    return 12
'''


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
    
'''
def (anterior)obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    # Asignamos zona horaria correcta (Comodoro usa zona Argentina)
    tz = pytz.timezone("America/Argentina/Buenos_Aires")  # válido para todo el país
    dt_local = datetime(anio, mes, dia, hora, minuto)
    offset = tz.utcoffset(dt_local).total_seconds() / 3600
    return offset

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
'''

def obtener_signo(grados):
    signos = [
        "Aries", "Tauro", "Geminis", "Cancer", "Leo", "Virgo", "Libra",
        "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signos[int(grados // 30)]


def obtener_sol(anio, mes, dia, hora, minuto, lat, lon, inconsciente, country_hint):
    #print(
    #    f"🛰️ Procesando Sol → {anio}-{mes}-{dia} {hora}:{minuto}, lat: {lat}, lon: {lon}"
    #)
    #print(f"inconsciente: {inconsciente}")
    # Obtené JD en UT (con DST histórico correcto)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    # Sol en UT
    grados_sol = swe.calc_ut(jd, swe.SUN)[0][0]
    signo = obtener_signo(grados_sol)
    grado_signo = grados_sol % 30
    formato_dms = grados_a_dms(grado_signo)

    # Casa (usar las cúspides 1..12)
    casa = calcular_casa(jd, lat, lon, grados_sol)
    #print(f"Grados Sol: {grados_sol}")
    #print(f"SOL grados en signo: {grado_signo}")
    #print(f"SOL grados: {formato_dms}")
    #print(f"SOL Cúspide de la casa: {casa}")

    '''
    if inconsciente: 
        offset= 0
    else:
        offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)[0]
    hora_utc_decimal = hora + minuto / 60 - offset
    print(f"horautc_decimal: {hora_utc_decimal}")
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd = jd_ut(anio, mes, dia, hora, minuto, lat, lon)[0]

    # Posición del Sol
    grados_sol = swe.calc_ut(jd, swe.SUN)[0][0]
    print(f"Grados Sol: {grados_sol}")
    signo = obtener_signo(grados_sol)
    grado_signo = grados_sol % 30
    print(f"Grado en signo: {grado_signo}")
    formato_dms = grados_a_dms(grado_signo)

    # Determinar casa
    casa = calcular_casa(jd, lat, lon, grados_sol)
    '''
    return {
        "signo": signo,
        "grados": round(grados_sol, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }

def obtener_tierra(anio, mes, dia, hora, minuto, lat, lon, country_hint):
    
    sol= obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False, country_hint)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
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

def obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon, country_hint):
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    cusps_raw, ascmc = swe.houses(jd, float(lat), float(lon), b'P')
    asc = float(ascmc[0])
    signo = obtener_signo(asc)
    formato_dms = grados_a_dms(asc % 30)
    #print(f"anio: {anio}, mes: {mes}, dia: {dia}, hora: {hora}, minuto: {minuto}, lat: {lat}, lon: {lon}")
    #print(f"Ascendente: {asc}° ({formato_dms}) en {signo}")
    return {
        "grados": round(asc, 6),
        "signo": signo,
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        #"tz": tzname,
        #"utc": dt_utc.isoformat(),
        #"mode": mode
    }
'''
def obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon):
    # JD en UT (con DST histórico correcto)
    jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    # Casas y puntos angulares
    cusps_raw, ascmc = swe.houses(jd, float(lat), float(lon), b'P')

    # Normalizamos cúspides a SIEMPRE 12 valores (casas 1..12)
    if len(cusps_raw) == 13:
        casas = list(cusps_raw[1:13])
    elif len(cusps_raw) == 12:
        casas = list(cusps_raw)
    else:
        raise ValueError(f"Formato de cúspides inesperado: len={len(cusps_raw)} -> {cusps_raw}")

    asc = float(ascmc[0])

    # (Debug opcional) Asc debe ser ≈ cúspide 1
    #print("ASC:", asc, "Cusp1:", casas[0], "Δ", abs(asc - casas[0]))

    signo = obtener_signo(asc)
    grado_signo = asc % 30
    formato_dms = grados_a_dms(grado_signo)
    print(f"anio: {anio}, mes: {mes}, dia: {dia}, hora: {hora}, minuto: {minuto}, lat: {lat}, lon: {lon}")
    print(f"Ascendente: {asc}° ({formato_dms}) en {signo}")
    return {
        "grados": round(asc, 6),
        "signo": signo,
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "tz": tzname,
        "utc": dt_utc.isoformat(),
        # "cusp1": round(casas[0], 6)  # habilitalo si querés verificación rápida
    }
'''
def obtener_mc(anio, mes, dia, hora, minuto, lat, lon, country_hint):
    # JD en UT (ya con DST histórico correcto)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    cusps_raw, ascmc = swe.houses(jd, float(lat), float(lon), b'P')  # Placidus
    mc = float(ascmc[1])  # Mediocielo (longitud 0–360)
    #print("MC:", mc, "Cusp10:", cusps_raw[9], "Δ", abs(mc - cusps_raw[9]))
    signo = obtener_signo(mc)
    grado_signo = mc % 30
    formato_dms = grados_a_dms(grado_signo)

    # (opcional) verificación: en sistemas por cuadrantes, cusp(10) ≈ MC
    # if len(cusps_raw) >= 10:
    #     cusp10 = (cusps_raw[10] if len(cusps_raw)==13 else cusps_raw[9])
    #     print("Δ(MC, C10) =", abs(mc - cusp10))

    return {
        "grados": round(mc, 6),
        "signo": signo,
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        #"tz": tzname,
        #"utc": dt_utc.isoformat()
    }


'''
def obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon):
    # Calcular hora UTC
    jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)
    

    # Calcular casas y ascendente
    casas, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = ascmc[0]
    print(f"valor asc {asc}")
    signo = obtener_signo(asc)
    grado_signo = asc % 30
    formato_dms = grados_a_dms(grado_signo)

    return {
        "ascendente_grado": round(asc, 2),
        "signo": signo,
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}"
    }
'''

def obtener_luna(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #print(
    #    f"🛰️ Recibido en /luna → {anio}-{mes}-{dia} {hora}:{minuto}, lat: {lat}, lon: {lon}"
    #)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)
    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Posición de la Luna
    grados_luna = swe.calc_ut(jd, swe.MOON)[0][0]
    signo = obtener_signo(grados_luna)
    grado_signo = grados_luna % 30
    formato_dms = grados_a_dms(grado_signo)

    #print(f"Grados Luna: {grados_luna}")
    #print(f"LUNA grados en signo: {grado_signo}")
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


def obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    # Obtené JD en UT (con DST histórico correcto)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    # Mercurio en UT
    grados_mercurio = swe.calc_ut(jd, swe.MERCURY)[0][0]
    signo = obtener_signo(grados_mercurio)
    grado_signo = grados_mercurio % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Mercurio: {grados_mercurio}")
    # Casa (usar las cúspides 1..12)
    casa = calcular_casa(jd, lat, lon, grados_mercurio)
    '''
    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    grados_mercurio = swe.calc_ut(jd, swe.MERCURY)[0][0]
    signo = obtener_signo(grados_mercurio)
    grado_signo = grados_mercurio % 30
    formato_dms = grados_a_dms(grado_signo)

    casa = calcular_casa(jd, lat, lon, grados_mercurio)
    '''
    return {
        "signo": signo,
        "grados": round(grados_mercurio, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_venus(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_venus = swe.calc_ut(jd, swe.VENUS)[0][0]
    signo = obtener_signo(grados_venus)
    grado_signo = grados_venus % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Venus: {grados_venus}")
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


def obtener_marte(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_marte = swe.calc_ut(jd, swe.MARS)[0][0]
    signo = obtener_signo(grados_marte)
    grado_signo = grados_marte % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Marte: {grados_marte}")
    casa = calcular_casa(jd, lat, lon, grados_marte)

    return {
        "signo": signo,
        "grados": round(grados_marte, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_jupiter = swe.calc_ut(jd, swe.JUPITER)[0][0]
    signo = obtener_signo(grados_jupiter)
    grado_signo = grados_jupiter % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Júpiter: {grados_jupiter}")
    casa = calcular_casa(jd, lat, lon, grados_jupiter)

    return {
        "signo": signo,
        "grados": round(grados_jupiter, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_saturno(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_saturno = swe.calc_ut(jd, swe.SATURN)[0][0]
    signo = obtener_signo(grados_saturno)
    grado_signo = grados_saturno % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Saturno: {grados_saturno}")
    casa = calcular_casa(jd, lat, lon, grados_saturno)

    return {
        "signo": signo,
        "grados": round(grados_saturno, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_urano(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_urano = swe.calc_ut(jd, swe.URANUS)[0][0]
    signo = obtener_signo(grados_urano)
    grado_signo = grados_urano % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Urano: {grados_urano}")
    casa = calcular_casa(jd, lat, lon, grados_urano)

    return {
        "signo": signo,
        "grados": round(grados_urano, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_neptuno = swe.calc_ut(jd, swe.NEPTUNE)[0][0]
    signo = obtener_signo(grados_neptuno)
    grado_signo = grados_neptuno % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Neptuno: {grados_neptuno}")
    casa = calcular_casa(jd, lat, lon, grados_neptuno)

    return {
        "signo": signo,
        "grados": round(grados_neptuno, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_pluton(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_pluton = swe.calc_ut(jd, swe.PLUTO)[0][0]
    signo = obtener_signo(grados_pluton)
    grado_signo = grados_pluton % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Plutón: {grados_pluton}")
    #print(f"jd: {jd}, lat: {lat}, lon: {lon}")
    casa = calcular_casa(jd, lat, lon, grados_pluton)

    return {
        "signo": signo,
        "grados": round(grados_pluton, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_nodoN = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
    signo = obtener_signo(grados_nodoN)
    grado_signo = grados_nodoN % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Nodo Norte: {grados_nodoN}")
    casa = calcular_casa(jd, lat, lon, grados_nodoN)

    return {
        "signo": signo,
        "grados": round(grados_nodoN, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    # Nodo Norte (MEAN Node)
    nodo_norte = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]

    # Nodo Sur = opuesto al Nodo Norte
    nodo_sur = (nodo_norte + 180) % 360

    signo = obtener_signo(nodo_sur)
    grado_signo = nodo_sur % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Nodo Sur: {nodo_sur}")
    
    casa = calcular_casa(jd, lat, lon, nodo_sur)

    return {
        "signo": signo,
        "grados": round(nodo_sur, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_quiron(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    #offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    #hora_utc_decimal = hora + minuto / 60 - offset
    #jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
    #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_quiron = swe.calc_ut(jd, swe.CHIRON)[0][0]
    signo = obtener_signo(grados_quiron)
    grado_signo = grados_quiron % 30
    formato_dms = grados_a_dms(grado_signo)
    #print(f"Grados Quirón: {grados_quiron}")
    #print(f"jd: {jd}, lat: {lat}, lon: {lon}")
    casa = calcular_casa(jd, lat, lon, grados_quiron)

    return {
        "signo": signo,
        "grados": round(grados_quiron, 2),
        "grado_en_signo": formato_dms,
        "signo_completo": f"{formato_dms} {signo}",
        "casa": casa
    }


def obtener_lilith(anio, mes, dia, hora, minuto, lat, lon, country_hint):

   # offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
   # hora_utc_decimal = hora + minuto / 60 - offset
   # jd = swe.julday(anio, mes, dia, hora_utc_decimal)
    jd, tzname, dt_utc, mode = jd_ut_smart(anio, mes, dia, hora, minuto, lat, lon, country_hint, None)
   #jd, tzname, dt_utc = jd_ut(anio, mes, dia, hora, minuto, lat, lon)

    grados_lilith = swe.calc_ut(jd, 12)[0][0]  # Lilith media
    signo = obtener_signo(grados_lilith)
    grado_signo = grados_lilith % 30
    formato_dms = grados_a_dms(grado_signo)
    casa = calcular_casa(jd, lat, lon, grados_lilith)

    #print(f"Grados Lilith: {grados_lilith}")

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
'''
def obtener_elemento(signos_por_punto):
    
    contador = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
    #for cuerpo, signo in planetas_en_signos.items():
    for punto, peso in PESOS_12.items():
        signo = signos_por_punto.get(punto)
        if not signo:
            continue
        if signo in POS:
            pos += peso
    for cuerpo, signo in PESOS_12.items():
        if cuerpo in PLANETAS_ELEMENTO_POLARIDAD:
            elemento = elemento_por_signo.get(signo)
            if elemento:
                contador[elemento] += peso
    max_val = max(contador.values())
    dominantes = [e for e, v in contador.items() if v == max_val]
    print("elemento", dict(contador))
    print(f"elem dominante {dominantes}")
    return "-".join(dominantes)
'''
def obtener_elemento(signos_por_punto):
    
    contador = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
    #for cuerpo, signo in planetas_en_signos.items():
    for punto, peso in PESOS_12.items():
        signo = signos_por_punto.get(punto)
        if not signo:
            continue
        if signo in elemento_por_signo:
            
            elemento = elemento_por_signo.get(signo)
            if elemento:
                contador[elemento] += peso
    max_val = max(contador.values())
    dominantes = [e for e, v in contador.items() if v == max_val]
    #print("elemento", dict(contador))
    #print(f"elem dominante {dominantes}")
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

POS = {"Aries","Geminis","Leo","Libra","Sagitario","Acuario"}

PESOS_12 = {
    "Sol":3, "Luna":3, "Asc":3,
    "Mercurio":2, "Venus":2, "Marte":2, "MC":2,
    "Jupiter":1, "Saturno":1, "Urano":1, "Neptuno":1, "Pluton":1
    
}
#"MC":2,    "Júpiter":1, "Saturno":1, "Urano":1, "Neptuno":1, "Plutón":1

def polaridad_ponderada_12(signos_por_punto):
    pos = neg = 0
    
    for punto, peso in PESOS_12.items():
        signo = signos_por_punto.get(punto)
        if not signo:
            continue
        if signo in POS:
            pos += peso
        else:
            neg += peso
           
    if pos > neg:
        return "P"
    elif neg > pos:
        return "N"
    else:
        return "E" 
    

    
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
    #signo_sol = signo_sol
    #signo_asc = signo_asc
    
    # Lista de signos en orden
    signos = ["Aries", "Tauro", "Geminis", "Cancer", "Leo", "Virgo",
              "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
    
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


def procesar(anio, mes, dia, hora, minuto, lat, lon, country_hint):

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
    sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False, country_hint)
    luna = obtener_luna(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    mercurio = obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    venus = obtener_venus(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    marte = obtener_marte(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    jupiter = obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    saturno = obtener_saturno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    urano = obtener_urano(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    neptuno = obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    pluton = obtener_pluton(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    quiron = obtener_quiron(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    lilith = obtener_lilith(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    ascendente =  obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    nodoN = obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    nodoS = obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    fase = obtener_fase_lunar(sol["grados"], luna["grados"])
    #tierra = obtener_tierra(anio, mes, dia, hora, minuto, lat, lon)
    mc = obtener_mc(anio, mes, dia, hora, minuto, lat, lon, country_hint)

    #print(f" sol {sol['grados']} luna {luna['grados']} tierra {tierra['grados']}")
    #print(f" nodoN {nodoN['grados']} nodoS {nodoS['grados']}")
    #print(f" mercurio {mercurio['grados']} venus {venus['grados']} marte {marte['grados']}")
    #print(f" jupiter {jupiter['grados']} saturno {saturno['grados']} urano {urano['grados']}")
    #print(f" neptuno {neptuno['grados']} pluton {pluton['grados']}")
    #print(f" quiron {quiron['grados']} lilith {lilith['grados']}")
    #print(f" ascendente {ascendente['grados']} MC {mc['signo']}")
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
    planetas_en_signos12 = {
        "Sol": sol["signo"],
        "Luna": luna["signo"],
        "Mercurio": mercurio["signo"],
        "Venus": venus["signo"],
        "Marte": marte["signo"],
        "Jupiter": jupiter["signo"],
        "Saturno": saturno["signo"],
        "Urano": urano["signo"],
        "Neptuno": neptuno["signo"],
        "Pluton": pluton["signo"],
        "Asc": ascendente["signo"],
        "MC": mc["signo"],
     
    
    }
    #print("planetas en signos", planetas_en_signos)
    #print("planetas en signos 12", planetas_en_signos12)
    ''''
    anio_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["anio_i"]
    mes_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["mes_i"]
    dia_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["dia_i"]
    hora_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["hora_i"]
    min_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["minuto_i"]
    
    grados_in =88.3
    #grados_inlun = 88*12.92

    
    sol_inconsciente =      (sol["grados"]-grados_in)%360
    #print(f"grado sol inconsciente {sol_inconsciente}")
    tierra_inconsciente =   (tierra["grados"]-grados_in)%360
    '''
    #fecha_natal = datetime(anio, mes, dia, hora, minuto)
    #deltain = timedelta(days=88, hours=7, minutes=12, seconds=50) # 0.3 días ≈ 7h12m
    #fecha_inco= fecha_natal - deltain
    #fecha_inco = fecha_inco.replace(hour=0, minute=0, second=0, microsecond=0)
    '''
    luna_in = obtener_luna(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon)
    #print(f"grado luna inconsciente {luna_in['grados']}")
    luna_inconsciente =     luna_in["grados"]
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
    
    for planetas in (
        [sol, tierra, luna, nodoN, nodoS, mercurio, venus, marte, jupiter, saturno, urano, neptuno, pluton,
                     ]):
        tolerancia = 0
        puerta_dict = obtener_puerta(planetas["grados"], tolerancia)
        puerta = puerta_dict["puerta"] if puerta_dict else None
        #print(f"puerta activa : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)
            
            #if nombre == "sol":
            #    puertasol_con = puerta_dict["puerta"] 
            #if nombre == "tierra":
            #    puertatierra_con = puerta_dict["puerta"] 
            
        
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
        #print(f"puerta activa :{nombre} : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)
            
            #if nombre == "sol_inconsciente":
            #    puertasol_in = puerta_dict["puerta"] 
            #if nombre == "tierra_inconsciente":    
            #    puertatierra_in = puerta_dict["puerta"]
                 

    # Detectar canales activos
    canales_activos = detectar_canales(puertas_activadas)
    #print(f"canales activos: {canales_activos}")
    # Calcular tipo
    tipo = calcular_tipo(canales_activos)
    #print(f"tipo dh {tipo}")
    
    perfil = calcular_perfil( sol["grados"], sol_inconsciente)
    #print(f"perfil dh {perfil}")
    #print(f"grado_sol_iconsciente dh {sol_inconsciente}")
    #print(f"grado_sol_consciente dh {sol["grados"]}")
    #tipo = calcular_tipo(canales_activos)
    #puerta_con =puertasol_con&","& puertatierra_con
    #puerta_in = puertasol_in&","& puertatierra_in
    #cruz = calcular_cruz(puerta_con, puerta_in)

    #print(f"Perfil: {perfil}")
    #print(f"Tipo: {tipo}")
    #print(f"Cruz de encarnación: {cruz}")
    '''
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
        "nodoS": nodoS["signo"],
        "gr_nodos":nodoS["grado_en_signo"],
        "c_nodoS": nodoS["casa"],
        "gr_lilith": lilith["grado_en_signo"],
        "c_lilith":  lilith["casa"],
        "gr_quiron": quiron["grado_en_signo"],
        "c_quiron":  quiron["casa"],
        "elemento": obtener_elemento(planetas_en_signos12),
        "polaridad": polaridad_ponderada_12(planetas_en_signos12),
        "modalidad": obtener_modalidad(planetas_en_signos),
        "n_destino": calcular_numero_destino(dia, mes, anio),
        "fr_144": calcular_fractal(sol["signo"], ascendente["signo"]),
        "dia_llegada": dia_y_rayo(dia, mes, anio)["dia"],
        "rayo": dia_y_rayo(dia, mes, anio)["color"]        
        
        
    }
    #if request.args.get("modo") == "string":
    #return "-".join(str(v) for v in registro.values())
   # else:
    return registro
    #return registro


def procesar_dh(anio, mes, dia, hora, minuto, lat, lon, country_hint):

    '''
    Calcula datos de DH
    Las puertas se obtienen a partir de los grados zodiacales de los planetas usando una tabla de mapeo.
   '''
    
    

    # Ahora sí: llamás a las funciones de los planetas
    sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False, country_hint)
    luna = obtener_luna(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    mercurio = obtener_mercurio(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    venus = obtener_venus(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    marte = obtener_marte(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    jupiter = obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    saturno = obtener_saturno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    urano = obtener_urano(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    neptuno = obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    pluton = obtener_pluton(anio, mes, dia, hora, minuto, lat, lon, country_hint)

    ascendente =  obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    nodoN = obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    nodoS = obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    
    tierra = obtener_tierra(anio, mes, dia, hora, minuto, lat, lon, country_hint)
   

    
    anio_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["anio_i"]
    mes_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["mes_i"]
    dia_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["dia_i"]
    hora_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["hora_i"]
    min_in = fecha_sol_inconsciente(anio, mes, dia, hora, minuto)["minuto_i"]
    
    grados_in =88.3
    #grados_inlun = 88*12.92

    
    sol_inconsciente =      (sol["grados"]-grados_in)%360
    #print(f"grado sol inconsciente {sol_inconsciente}")
    tierra_inconsciente =   (tierra["grados"]-grados_in)%360
    '''
    fecha_natal = datetime(anio, mes, dia, hora, minuto)
    deltain = timedelta(days=88, hours=7, minutes=12, seconds=50) # 0.3 días ≈ 7h12m
    fecha_inco= fecha_natal - deltain
    fecha_inco = fecha_inco.replace(hour=0, minute=0, second=0, microsecond=0)
    '''
    luna_in = obtener_luna(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)
    #print(f"grado luna inconsciente {luna_in['grados']}")
    luna_inconsciente =     luna_in["grados"]
    #luna_inconsciente =     (luna["grados"]-grados_inlun)%360
        
    nodon_inconsciente =    obtener_nodoN(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    nodos_inconsciente =    obtener_nodo_sur(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    mercurio_inconsciente = obtener_mercurio(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    venus_inconsciente =    obtener_venus(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    marte_inconsciente =    obtener_marte(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    jupiter_inconsciente =  obtener_jupiter(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    saturno_inconsciente =  obtener_saturno(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    urano_inconsciente =    obtener_urano(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    neptuno_inconsciente =  obtener_neptuno(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    pluton_inconsciente =   obtener_pluton(anio_in, mes_in, dia_in, hora_in, min_in, lat, lon, country_hint)["grados"]
    
    
    #grado_sol_inconsciente = sol["grados"]- grados_in
    # Obtener puertas activadas por los planetas
    puertas_activadas = []
    
    for planetas in (
        [sol, tierra, luna, nodoN, nodoS, mercurio, venus, marte, jupiter, saturno, urano, neptuno, pluton,
                     ]):
        tolerancia = 0
        puerta_dict = obtener_puerta(planetas["grados"], tolerancia)
        puerta = puerta_dict["puerta"] if puerta_dict else None
        #print(f"puerta activa : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)
            '''
            if nombre == "sol":
                puertasol_con = puerta_dict["puerta"] 
            if nombre == "tierra":
                puertatierra_con = puerta_dict["puerta"] 
            ''' 
        
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
        #print(f"puerta activa :{nombre} : {puerta}")
        if puerta:
            puertas_activadas.append(puerta)
            ''''
            if nombre == "sol_inconsciente":
                puertasol_in = puerta_dict["puerta"] 
            if nombre == "tierra_inconsciente":    
                puertatierra_in = puerta_dict["puerta"]
            '''     

    # Detectar canales activos
    canales_activos = detectar_canales(puertas_activadas)
    #print(f"canales activos: {canales_activos}")
    # Calcular tipo
    tipo = calcular_tipo(canales_activos)
    #print(f"tipo dh {tipo}")
    
    perfil = calcular_perfil( sol["grados"], sol_inconsciente)
    #print(f"perfil dh {perfil}")
    #print(f"grado_sol_iconsciente dh {sol_inconsciente}")
    #print(f"grado_sol_consciente dh {sol["grados"]}")
    #tipo = calcular_tipo(canales_activos)
    #puerta_con =puertasol_con&","& puertatierra_con
    #puerta_in = puertasol_in&","& puertatierra_in
    #cruz = calcular_cruz(puerta_con, puerta_in)

    #print(f"Perfil: {perfil}")
    #print(f"Tipo: {tipo}")
    #print(f"Cruz de encarnación: {cruz}")
    registro = {
        "fecha_nac": date(anio, mes, dia),
        "hora": hora,
        "minuto": minuto,
        "lat": lat,
        "lon": lon,
        "tipo_dh": tipo,
        "perfil": perfil
    
    }
  
    return registro
   



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
    #print(f"linea {puerta}- {grado} - gr_relativo {grado_relativo} - {linea}")
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

'''
def _parse_par(par):
    """
    Acepta: "24,44"  ó  [24,44]  ó  (24,44)
    Devuelve: tupla ordenada de enteros, p.ej. (24, 44)
    """
    if isinstance(par, str):
        nums = [int(x.strip()) for x in par.split(",") if x.strip()]
    else:
        nums = [int(x) for x in par]
    if len(nums) != 2:
        raise ValueError("Cada par debe tener exactamente 2 puertas")
    return tuple(sorted(nums))

def _clave(pares_consc, pares_inconsc):
    """
    Devuelve una clave canónica ((c1,c2),(i1,i2)) para usar en el diccionario.
    """
    c = _parse_par(pares_consc)
    i = _parse_par(pares_inconsc)
    return (c, i)

# Mapa: ((pSolCon,pTieCon),(pSolDis,pTieDis)) -> nombre de cruz
# (Si te llega invertido Sol/Tierra dentro de cada par, igual matchea porque ordenamos)

CRUCES = {
    _clave("9,16", "40,37"): "Angulo Derecho de la Planificacion 4",
    _clave("9,16", "64,63"): "Cruz Yuxtapuesta del Foco",
    _clave("9,16", "64,63"): "Angulo Izquierdo de la Identificacion 2",
    _clave("5,35", "64,63"): "Angulo Derecho de la Consciencia 4",
    _clave("5,35", "47,22"): "Cruz Yuxtapuesta de los Habitos",
    _clave("5,35", "47,22"): "Angulo Izquierdo de la Separacion 2",
    _clave("26,45", "47,22"): "Angulo Derecho de la Autoridad 4",
    _clave("26,45", "6,36"): "Cruz Yuxtapuesta del Embaucador",
    _clave("26,45", "6,36"): "Angulo Izquierdo de la Confrontacion 2",
    _clave("11,12", "6,36"): "Angulo Derecho del Eden 4",
    _clave("11,12", "46,25"): "Cruz Yuxtapuesta de las Ideas",
    _clave("11,12", "46,25"): "Angulo Izquierdo de la Educacion 2",
    _clave("10,15", "46,25"): "Angulo Derecho del Receptaculo del Amor 4",
    _clave("10,15", "18,17"): "Cruz Yuxtapuesta del Comportamiento",
    _clave("10,15", "18,17"): "Angulo Izquierdo de la Prevencion 2",
    _clave("58,52", "18,17"): "Angulo Derecho del Servicio 4",
    _clave("58,52", "48,21"): "Cruz Yuxtapuesta de la Vitalidad",
    _clave("58,52", "48,21"): "Angulo Izquierdo de las Exigencias 2",
    _clave("38,39", "48,21"): "Angulo Derecho de la Tension 4",
    _clave("38,39", "57,51"): "Cruz Yuxtapuesta de la Oposicion",
    _clave("38,39", "57,51"): "Angulo Izquierdo del Individualismo 2",
    _clave("54,53", "57,51"): "Angulo Derecho de la Penetracion 4",
    _clave("54,53", "32,42"): "Cruz Yuxtapuesta de la Ambicion",
    _clave("54,53", "32,42"): "Angulo Izquierdo de los Ciclos 2",
    _clave("32,42", "62,61"): "Angulo Derecho del Maya 4",
    _clave("61,62", "50,3"): "Cruz Yuxtapuesta del Pensamiento",
    _clave("61,62", "50,3"): "Angulo Izquierdo del Oscurecimiento 2",
    _clave("60,56", "50,3"): "Angulo Derecho de las Leyes 4",
    _clave("60,56", "28,27"): "Cruz Yuxtapuesta de la Limitacion",
    _clave("60,56", "28,27"): "Angulo Izquierdo de la Distraccion 2",
    _clave("41,31", "28,27"): "Angulo Derecho de lo Inesperado 4",
    _clave("41,31", "44,24"): "Cruz Yuxtapuesta de la Fantasia",
    _clave("41,31", "44,24"): "Angulo Izquierdo del Alpha 2",
    _clave("19,33", "44,24"): "Angulo Derecho de los Cuatro Caminos 4",
    _clave("19,33", "1,2"): "Cruz Yuxtapuesta de la Necesidad",
    _clave("19,33", "1,2"): "Angulo Izquierdo del Refinamiento 2",
    _clave("13,7", "1,2"): "Angulo Derecho de la Esfinge",
    _clave("13,7", "43,23"): "Cruz Yuxtapuesta de Escuchar",
    _clave("13,7", "43,23"): "Angulo Izquierdo de las Mascaras",
    _clave("49,4", "43,23"): "Angulo Derecho de las Explicaciones",
    _clave("49,4", "14,8"): "Cruz Yuxtapuesta de los Principios",
    _clave("49,4", "14,8"): "Angulo Izquierdo de la Revolucion",
    _clave("30,29", "14,8"): "Angulo Derecho del Contagio",
    _clave("30,29", "34,20"): "Cruz Yuxtapuesta del Destino",
    _clave("30,29", "34,20"): "Angulo Izquierdo de la Industria",
    _clave("55,59", "34,20"): "Angulo Derecho del Fenix Durmiente (hasta 2027)",
    _clave("55,59", "9,16"): "Cruz Yuxtapuesta de los Humores Cambiantes",
    _clave("55,59", "9,16"): "Angulo Izquierdo del Espiritu",
    _clave("37,40", "9,16"): "Angulo Derecho de la Planificacion",
    _clave("37,40", "5,35"): "Cruz Yuxtapuesta de los Acuerdos",
    _clave("37,40", "5,35"): "Angulo Izquierdo de la Migracion",
    _clave("63,64", "5,35"): "Angulo Derecho de la Consciencia",
    _clave("63,64", "26,45"): "Cruz Yuxtapuesta de las Dudas",
    _clave("63,64", "26,45"): "Angulo Izquierdo del Dominio",
    _clave("22,47", "26,45"): "Angulo Derecho de la Autoridad",
    _clave("22,47", "11,12"): "Cruz Yuxtapuesta de la Gracia",
    _clave("22,47", "11,12"): "Angulo Izquierdo de Informar",
    _clave("36,6", "11,12"): "Angulo Derecho del Eden",
    _clave("36,6", "10,15"): "Cruz Yuxtapuesta de la Crisis",
    _clave("36,6", "10,15"): "Angulo Izquierdo del Plano Mundano",
    _clave("25,46", "10,15"): "Angulo Derecho del Receptaculo del Amor",
    _clave("25,46", "58,52"): "Cruz Yuxtapuesta de la Inocencia",
    _clave("25,46", "58,52"): "Angulo Izquierdo de la Sanacion",
    _clave("17,18", "58,52"): "Angulo Derecho del Servicio",
    _clave("17,18", "38,39"): "Cruz Yuxtapuesta de las Opiniones",
    _clave("17,18", "38,39"): "Angulo Izquierdo de la Convulsion",
    _clave("21,48", "38,39"): "Angulo Derecho de la Tension",
    _clave("21,48", "54,53"): "Cruz Yuxtapuesta del Control",
    _clave("21,48", "54,53"): "Angulo Izquierdo del Empeno",
    _clave("51,57", "54,53"): "Angulo Derecho de la Penetracion",
    _clave("51,57", "61,62"): "Cruz Yuxtapuesta del Shock",
    _clave("51,57", "61,62"): "Angulo Izquierdo del Clarion",
    _clave("42,32", "61,62"): "Angulo Derecho del Maya",
    _clave("42,32", "60,56"): "Cruz Yuxtapuesta de la Culminacion",
    _clave("42,32", "60,56"): "Angulo Izquierdo de la Limitacion",
    _clave("3,50", "60,56"): "Angulo Derecho de las Leyes",
    _clave("3,50", "41,31"): "Cruz Yuxtapuesta de la Mutacion",
    _clave("3,50", "41,31"): "Angulo Izquierdo de los Deseos",
    _clave("27,28", "41,31"): "Angulo Derecho de lo Inesperado",
    _clave("27,28", "19,33"): "Cruz Yuxtapuesta de Cuidar",
    _clave("27,28", "19,33"): "Angulo Izquierdo del Alineamiento",
    _clave("24,44", "19,33"): "Angulo Derecho de los Cuatro Caminos",
    _clave("24,44", "13,7"): "Cruz Yuxtapuesta de la Racionalizacion",
    _clave("24,44", "13,7"): "Angulo Izquierdo de la Encarnacion",
    _clave("2,1", "13,7"): "Angulo Derecho de la Esfinge 2",
    _clave("2,1", "49,4"): "Cruz Yuxtapuesta del Chofer",
    _clave("2,1", "49,4"): "Angulo Izquierdo del Desafio",
    _clave("23,43", "49,4"): "Angulo Derecho de las Explicaciones 2",
    _clave("23,43", "30,29"): "Cruz Yuxtapuesta de la Asimilacion",
    _clave("23,43", "30,29"): "Angulo Izquierdo de la Dedicacion",
    _clave("8,14", "30,29"): "Angulo Derecho del Contagio 2",
    _clave("8,14", "55,59"): "Cruz Yuxtapuesta de la Contribucion",
    _clave("8,14", "55,59"): "Angulo Izquierdo de la Incertidumbre",
    _clave("20,34", "55,59"): "Angulo Derecho del Fenix Durmiente 2",
    _clave("20,34", "37,40"): "Cruz Yuxtapuesta del Ahora",
    _clave("20,34", "37,40"): "Angulo Izquierdo de la Dualidad",
    _clave("16,9", "37,40"): "Angulo Derecho de la Planificacion 2",
    _clave("16,9", "63,64"): "Cruz Yuxtapuesta de la Experimentacion",
    _clave("16,9", "63,64"): "Angulo Izquierdo de la Identificacion",
    _clave("35,5", "63,64"): "Angulo Derecho de la Consciencia 2",
    _clave("35,5", "22,47"): "Cruz Yuxtapuesta de la Experiencia",
    _clave("35,5", "22,47"): "Angulo Izquierdo de la Separacion",
    _clave("45,26", "22,47"): "Angulo Derecho de la Autoridad 2",
    _clave("45,26", "36,6"): "Cruz Yuxtapuesta de la Posesion",
    _clave("45,26", "36,6"): "Angulo Izquierdo de la Confrontacion",
    _clave("12,11", "36,6"): "Angulo Derecho del Eden 2",
    _clave("12,11", "25,46"): "Cruz Yuxtapuesta de la Articulacion",
    _clave("12,11", "25,46"): "Angulo Izquierdo de la Educacion",
    _clave("15,10", "25,46"): "Angulo Derecho del Receptaculo del Amor 2",
    _clave("15,10", "17,18"): "Cruz Yuxtapuesta de los Extremos",
    _clave("15,10", "17,18"): "Angulo Izquierdo de la Prevencion",
    _clave("52,58", "17,18"): "Angulo Derecho del Servicio 2",
    _clave("52,58", "21,48"): "Cruz Yuxtapuesta de la Quietud",
    _clave("52,58", "21,48"): "Angulo Izquierdo de las Exigencias",
    _clave("39,38", "21,48"): "Angulo Derecho de la Tension 2",
    _clave("39,38", "51,57"): "Cruz Yuxtapuesta de la Provocacion",
    _clave("39,38", "51,57"): "Angulo Izquierdo del Individualismo",
    _clave("53,54", "51,57"): "Angulo Derecho de la Penetracion 2",
    _clave("53,54", "42,32"): "Cruz Yuxtapuesta de los Comienzos",
    _clave("53,54", "42,32"): "Angulo Izquierdo de los Ciclos",
    _clave("62,61", "42,32"): "Angulo Derecho del Maya 2",
    _clave("62,61", "3,50"): "Cruz Yuxtapuesta del Detalle",
    _clave("62,61", "3,50"): "Angulo Izquierdo del Oscurecimiento",
    _clave("56,60", "3,50"): "Angulo Derecho de las Leyes 2",
    _clave("56,60", "27,28"): "Cruz Yuxtapuesta de la Estimulacion",
    _clave("56,60", "27,28"): "Angulo Izquierdo de la Distraccion",
    _clave("31,41", "27,28"): "Angulo Derecho de lo Inesperado 2",
    _clave("31,41", "24,44"): "Cruz Yuxtapuesta de la Influencia",
    _clave("31,41", "24,44"): "Angulo Izquierdo del Alpha",
    _clave("33,19", "24,44"): "Angulo Derecho de los Cuatro Caminos 2",
    _clave("33,19", "2,1"): "Cruz Yuxtapuesta de la Retirada",
    _clave("33,19", "2,1"): "Angulo Izquierdo del Refinamiento",
    _clave("7,13", "2,1"): "Angulo Derecho de la Esfinge 3",
    _clave("7,13", "23,43"): "Cruz Yuxtapuesta de la Interaccion",
    _clave("7,13", "23,43"): "Angulo Izquierdo de las Mascaras 2",
    _clave("4,49", "23,43"): "Angulo Derecho de las Explicaciones 3",
    _clave("4,49", "8,14"): "Cruz Yuxtapuesta de la Formulacion",
    _clave("4,49", "8,14"): "Angulo Izquierdo de la Revolucion 2",
    _clave("29,30", "8,14"): "Angulo Derecho del Contagio 3",
    _clave("29,30", "20,34"): "Cruz Yuxtapuesta de los Compromisos",
    _clave("29,30", "20,34"): "Angulo Izquierdo de la Industria 2",
    _clave("59,55", "20,34"): "Angulo Derecho del Fenix Durmiente 3",
    _clave("59,55", "16,9"): "Cruz Yuxtapuesta de la Estrategia",
    _clave("59,55", "16,9"): "Angulo Izquierdo del Espiritu 2",
    _clave("40,37", "16,9"): "Angulo Derecho de la Planificacion 3",
    _clave("40,37", "35,5"): "Cruz Yuxtapuesta de la Negacion",
    _clave("40,37", "35,5"): "Angulo Izquierdo de la Migracion 2",
    _clave("64,63", "35,5"): "Angulo Derecho de la Consciencia 3",
    _clave("64,63", "45,26"): "Cruz Yuxtapuesta de la Confusion",
    _clave("64,63", "45,26"): "Angulo Izquierdo del Dominio 2",
    _clave("47,22", "25,26"): "Angulo Derecho de la Autoridad 3",
    _clave("47,22", "12,11"): "Cruz Yuxtapuesta de la Opresion",
    _clave("47,22", "12,11"): "Angulo Izquierdo de Informar 2",
    _clave("6,36", "12,11"): "Angulo Derecho del Eden 3",
    _clave("6,36", "15,10"): "Cruz Yuxtapuesta del Conflicto",
    _clave("6,36", "15,10"): "Angulo Izquierdo del Plano Mundano 2",
    _clave("46,25", "15,10"): "Angulo Derecho del Receptaculo del Amor 3",
    _clave("46,25", "52,58"): "Cruz Yuxtapuesta de la Serendipia",
    _clave("46,25", "52,58"): "Angulo Izquierdo de la Sanacion 2",
    _clave("18,17", "52,58"): "Angulo Derecho del Servicio 3",
    _clave("18,17", "39,38"): "Cruz Yuxtapuesta de Correccion",
    _clave("18,17", "39,38"): "Angulo Izquierdo de la Convulsion 2",
    _clave("48,21", "39,38"): "Angulo Derecho de la Tension 3",
    _clave("48,21", "53,54"): "Cruz Yuxtapuesta de la Profundidad",
    _clave("48,21", "53,54"): "Angulo Izquierdo del Empeno 2",
    _clave("57,51", "53,54"): "Angulo Derecho de la Penetracion 3",
    _clave("57,51", "62,61"): "Cruz Yuxtapuesta de la Intuicion",
    _clave("57,51", "62,61"): "Angulo Izquierdo del Clarion 2",
    _clave("32,42", "62,61"): "Angulo Derecho del Maya 3",
    _clave("32,42", "56,60"): "Cruz Yuxtapuesta de la Conservacion",
    _clave("32,42", "56,60"): "Angulo Izquierdo de la Limitacion 2",
    _clave("50,3", "56,60"): "Angulo Derecho de las Leyes 3",
    _clave("50,3", "31,41"): "Cruz Yuxtapuesta de los Valores",
    _clave("50,3", "31,41"): "Angulo Izquierdo de los Deseos 2",
    _clave("28,27", "31,41"): "Angulo Derecho de lo Inesperado 3",
    _clave("28,27", "33,19"): "Cruz Yuxtapuesta de los Riesgos",
    _clave("28,27", "33,19"): "Angulo Izquierdo del Alineamiento 2",
    _clave("44,24", "33,19"): "Angulo Derecho de los Cuatro Caminos 3",
    _clave("44,24", "7,13"): "Cruz Yuxtapuesta de Estar Alerta",
    _clave("44,24", "7,13"): "Angulo Izquierdo de la Encarnacion 2",
    _clave("1,2", "7,13"): "Angulo Derecho de la Esfinge 4",
    _clave("1,2", "4,49"): "Cruz Yuxtapuesta de la Autoexpresion",
    _clave("1,2", "4,49"): "Angulo Izquierdo del Desafio 2",
    _clave("43,23", "4,49"): "Angulo Derecho de las Explicaciones 4",
    _clave("43,23", "29,30"): "Cruz Yuxtapuesta de la Vision Interior",
    _clave("43,23", "29,30"): "Angulo Izquierdo de la Dedicacion 2",
    _clave("14,8", "29,30"): "Angulo Derecho del Contagio 4",
    _clave("14,8", "59,55"): "Cruz Yuxtapuesta de la Potenciacion",
    _clave("14,8", "59,55"): "Angulo Izquierdo de la Incertidumbre 2",
    _clave("34,20", "59,55"): "Angulo Derecho del Fenix Durmiente 4",
    _clave("34,20", "40,37"): "Cruz Yuxtapuesta del Poder",
    _clave("34,20", "40,37"): "Angulo Izquierdo de la Dualidad 2"                     
}



# Función para calcular la cruz de encarnación (simplificada)
def calcular_cruz(puerta_con, puerta_in):
    
    cruces = {
       {"cruz": "Angulo Derecho de la Esfinge 4", "puertas": "1,2,7,13"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor 4", "puertas": "1,2,7,13"},
       {"cruz": "Angulo Derecho de las Leyes 4", "puertas": "2,1,7,13"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor 2", "puertas": "2,1,7,13"},
       {"cruz": "Angulo Derecho de la Consciencia 4", "puertas": "5,35,47,22"},
       {"cruz": "Angulo Derecho del Plano Mundano 2", "puertas": "6,36,47,22"},
       {"cruz": "Angulo Derecho de la Esfinge 3", "puertas": "7,13,1,2"},
       {"cruz": "Angulo Derecho del Contagio 2", "puertas": "8,14,1,2"},
       {"cruz": "Angulo Derecho de la Planificación 4", "puertas": "9,16,40,37"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor 4", "puertas": "10,15,40,37"},
       {"cruz": "Angulo Derecho de los Cuatro Caminos 4", "puertas": "11,12,15,46"},
       {"cruz": "Angulo Derecho del Eden 2", "puertas": "12,11,15,46"},
       {"cruz": "Angulo Derecho del Servicio 4", "puertas": "13,7,1,2"},
       {"cruz": "Angulo Derecho de las Explicaciones 3", "puertas": "14,8,1,2"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor 2", "puertas": "15,10,40,37"},
       {"cruz": "Angulo Derecho de la Planificación 2", "puertas": "16,9,40,37"},
       {"cruz": "Angulo Derecho del Servicio", "puertas": "17,18,38,39"},
       {"cruz": "Angulo Derecho de Ocuparse de lo Echado a Perder", "puertas": "18,17,38,39"},
       {"cruz": "Angulo Derecho del Acercamiento", "puertas": "19,33,24,44"},
       {"cruz": "Angulo Derecho del Fenix Durmiente 2", "puertas": "20,34,24,44"},
       {"cruz": "Angulo Derecho de la Tension", "puertas": "21,48,24,44"},
       {"cruz": "Angulo Derecho de la Gracia", "puertas": "22,47,24,44"},
       {"cruz": "Angulo Derecho de las Decisiones 2", "puertas": "23,43,24,44"},
       {"cruz": "Angulo Derecho de los Cuatro Caminos", "puertas": "24,44,19,33"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor", "puertas": "25,46,19,33"},
       {"cruz": "Angulo Derecho de la Autoridad 4", "puertas": "26,45,19,33"},
       {"cruz": "Angulo Derecho de lo Inesperado", "puertas": "27,28,19,33"},
       {"cruz": "Angulo Derecho de la Preponderancia de lo Grande", "puertas": "28,27,19,33"},
       {"cruz": "Angulo Derecho del Contagio 3", "puertas": "29,30,19,33"},
       {"cruz": "Angulo Derecho de los Sentimientos", "puertas": "30,29,19,33"},
       {"cruz": "Angulo Derecho de lo Inesperado 2", "puertas": "31,41,19,33"},
       {"cruz": "Angulo Derecho de Maya 3", "puertas": "32,42,19,33"},
       {"cruz": "Angulo Derecho de los Cuatro Caminos 2", "puertas": "33,19,24,44"},
       {"cruz": "Angulo Derecho del Poder de lo Grande", "puertas": "34,20,24,44"},
       {"cruz": "Angulo Derecho de la Consciencia 2", "puertas": "35,5,24,44"},
       {"cruz": "Angulo Derecho del Oscurecimiento de la Luz", "puertas": "36,6,24,44"},
       {"cruz": "Angulo Derecho de la Planificacion", "puertas": "37,40,24,44"},
       {"cruz": "Angulo Derecho de la Penetracion 4", "puertas": "38,39,24,44"},
       {"cruz": "Angulo Derecho del Impedimento", "puertas": "39,38,24,44"},
       {"cruz": "Angulo Derecho de la Planificacion 3", "puertas": "40,37,25,46"},
       {"cruz": "Angulo Derecho de la Disminucion", "puertas": "41,31,25,46"},
       {"cruz": "Angulo Derecho del Aumento", "puertas": "42,32,25,46"},
       {"cruz": "Angulo Derecho de las Explicaciones 4", "puertas": "43,23,25,46"},
       {"cruz": "Angulo Derecho de los Cuatro Caminos 3", "puertas": "44,24,26,45"},
       {"cruz": "Angulo Derecho de la Autoridad 2", "puertas": "45,26,26,45"},
       {"cruz": "Angulo Derecho del Receptaculo del Amor 3", "puertas": "46,25,26,45"},
       {"cruz": "Angulo Derecho de la Autoridad 3", "puertas": "47,22,26,45"},
       {"cruz": "Angulo Derecho de la Tension 3", "puertas": "48,21,26,45"},
       {"cruz": "Angulo Derecho de las Leyes 3", "puertas": "49,4,26,45"},
       {"cruz": "Angulo Derecho de las Leyes 3", "puertas": "50,3,27,28"},
       {"cruz": "Angulo Derecho de la Penetracion", "puertas": "51,57,27,28"},
       {"cruz": "Angulo Derecho del Servicio 2", "puertas": "52,58,27,28"},
       {"cruz": "Angulo Derecho de la Penetracion 2", "puertas": "53,54,27,28"},
       {"cruz": "Angulo Derecho de la Muchacha que se Casa", "puertas": "54,53,27,28"},
       {"cruz": "Angulo Derecho del Espiritu", "puertas": "55,59,27,28"},
       {"cruz": "Angulo Derecho del Peregrine", "puertas": "56,60,27,28"},
       {"cruz": "Angulo Derecho de la Penetracion 3", "puertas": "57,51,27,28"},
       {"cruz": "Angulo Derecho del Servicio 4", "puertas": "58,52,29,30"},
       {"cruz": "Angulo Derecho de la Dispersion", "puertas": "59,55,29,30"},
       {"cruz": "Angulo Derecho de la Limitacion", "puertas": "60,56,29,30"},
       {"cruz": "Angulo Derecho de Maya 4", "puertas": "61,62,29,30"},
       {"cruz": "Angulo Derecho de Maya 2", "puertas": "62,61,31,41"},
       {"cruz": "Angulo Derecho de Despues de Concluir", "puertas": "63,64,31,41"},
       {"cruz": "Angulo Derecho de Antes de Concluir", "puertas": "64,63,31,41"},
       {"cruz": "Cruz Yuxtapuesta de la Autoexpresion", "puertas": "1,2,7,13"},
       {"cruz": "Cruz Yuxtapuesta del Chofer", "puertas": "2,1,7,13"},
       {"cruz": "Cruz Yuxtapuesta de Dificultad Inicial", "puertas": "3,50,7,13"},
       {"cruz": "Cruz Yuxtapuesta de la Formulacion", "puertas": "4,49,7,13"},
       {"cruz": "Cruz Yuxtapuesta de los Habitos", "puertas": "5,35,8,14"},
       {"cruz": "Cruz Yuxtapuesta del Conflicto", "puertas": "6,36,8,14"},
       {"cruz": "Cruz Yuxtapuesta del Rol", "puertas": "7,13,9,16"},
       {"cruz": "Cruz Yuxtapuesta de la Contribucion", "puertas": "8,14,9,16"},
       {"cruz": "Cruz Yuxtapuesta del Foco", "puertas": "9,16,10,15"},
       {"cruz": "Cruz Yuxtapuesta del Comportamiento", "puertas": "10,15,10,15"},
       {"cruz": "Cruz Yuxtapuesta de las Ideas", "puertas": "11,12,10,15"},
       {"cruz": "Cruz Yuxtapuesta de la Educacion", "puertas": "12,11,10,15"},
       {"cruz": "Cruz Yuxtapuesta de las Opiniones", "puertas": "13,7,17,18"},
       {"cruz": "Cruz Yuxtapuesta del Poder", "puertas": "14,8,17,18"},
       {"cruz": "Cruz Yuxtapuesta de los Extremos", "puertas": "15,10,17,18"},
       {"cruz": "Cruz Yuxtapuesta de la Experimentacion", "puertas": "16,9,17,18"},
       {"cruz": "Cruz Yuxtapuesta de las Opiniones", "puertas": "17,18,18,17"},
       {"cruz": "Cruz Yuxtapuesta de Corregir", "puertas": "18,17,18,17"},
       {"cruz": "Cruz Yuxtapuesta del Querer", "puertas": "19,33,20,34"},
       {"cruz": "Cruz Yuxtapuesta del Ahora", "puertas": "20,34,21,48"},
       {"cruz": "Cruz Yuxtapuesta de la Mordedura Tajante", "puertas": "21,48,21,48"},
       {"cruz": "Cruz Yuxtapuesta de la Gracia", "puertas": "22,47,22,47"},
       {"cruz": "Cruz Yuxtapuesta de la Asimilacion", "puertas": "23,43,23,43"},
       {"cruz": "Cruz Yuxtapuesta de la Racionalizacion", "puertas": "24,44,24,44"},
       {"cruz": "Cruz Yuxtapuesta de la Inocencia", "puertas": "25,46,25,46"},
       {"cruz": "Cruz Yuxtapuesta del Embajador", "puertas": "26,45,26,45"},
       {"cruz": "Cruz Yuxtapuesta del Cuidar", "puertas": "27,28,27,28"},
       {"cruz": "Cruz Yuxtapuesta de los Riesgos", "puertas": "28,27,28,27"},
       {"cruz": "Cruz Yuxtapuesta del Compromiso", "puertas": "29,30,29,30"},
       {"cruz": "Cruz Yuxtapuesta de la Conservacion", "puertas": "30,29,30,29"},
       {"cruz": "Cruz Yuxtapuesta de la Influencia", "puertas": "31,41,31,41"},
       {"cruz": "Cruz Yuxtapuesta de la Duracion", "puertas": "32,42,32,42"},
       {"cruz": "Cruz Yuxtapuesta de la Retirada", "puertas": "33,19,33,19"},
       {"cruz": "Cruz Yuxtapuesta de la Melancolia", "puertas": "34,20,34,20"},
       {"cruz": "Cruz Yuxtapuesta del Progreso", "puertas": "35,5,35,5"},
       {"cruz": "Cruz Yuxtapuesta de la Crisis", "puertas": "36,6,36,6"},
       {"cruz": "Cruz Yuxtapuesta de los Acordes", "puertas": "37,40,37,40"},
       {"cruz": "Cruz Yuxtapuesta de la Oposicion", "puertas": "38,39,38,39"},
       {"cruz": "Cruz Yuxtapuesta de los Comienzos", "puertas": "39,38,39,38"},
       {"cruz": "Cruz Yuxtapuesta de la Negacion", "puertas": "40,37,40,37"},
       {"cruz": "Cruz Yuxtapuesta de la Disminucion", "puertas": "41,31,41,31"},
       {"cruz": "Cruz Yuxtapuesta de la Culminacion", "puertas": "42,32,42,32"},
       {"cruz": "Cruz Yuxtapuesta de la Resolucion", "puertas": "43,23,43,23"},
       {"cruz": "Cruz Yuxtapuesta de Ir al Encuentro", "puertas": "44,24,44,24"},
       {"cruz": "Cruz Yuxtapuesta de la Posesion", "puertas": "45,26,45,26"},
       {"cruz": "Cruz Yuxtapuesta de la Seriondiplia", "puertas": "46,25,46,25"},
       {"cruz": "Cruz Yuxtapuesta de la Opresion", "puertas": "47,22,47,22"},
       {"cruz": "Cruz Yuxtapuesta de la Profundidad", "puertas": "48,21,48,21"},
       {"cruz": "Cruz Yuxtapuesta de los Valores", "puertas": "49,4,49,4"},
       {"cruz": "Cruz Yuxtapuesta de los Valores", "puertas": "50,3,50,3"},
       {"cruz": "Cruz Yuxtapuesta del Shock", "puertas": "51,57,51,57"},
       {"cruz": "Cruz Yuxtapuesta del Shock", "puertas": "52,58,52,58"},
       {"cruz": "Cruz Yuxtapuesta de los Comienzos", "puertas": "53,54,53,54"},
       {"cruz": "Cruz Yuxtapuesta de la Ambicion", "puertas": "54,53,54,53"},
       {"cruz": "Cruz Yuxtapuesta del Espiritu", "puertas": "55,59,55,59"},
       {"cruz": "Cruz Yuxtapuesta de la Estimulacion", "puertas": "56,60,56,60"},
       {"cruz": "Cruz Yuxtapuesta de la Intuicion", "puertas": "57,51,57,51"},
       {"cruz": "Cruz Yuxtapuesta del Vitalidad", "puertas": "58,52,58,52"},
       {"cruz": "Cruz Yuxtapuesta de la Estrategia", "puertas": "59,55,59,55"},
       {"cruz": "Cruz Yuxtapuesta de la Limitacion", "puertas": "60,56,60,56"},
       {"cruz": "Cruz Yuxtapuesta del Pensamiento", "puertas": "61,62,61,62"},
       {"cruz": "Cruz Yuxtapuesta del Detalle", "puertas": "62,61,62,61"},
       {"cruz": "Cruz Yuxtapuesta de las Dudas", "puertas": "63,64,63,64"},
       {"cruz": "Cruz Yuxtapuesta de la Confusion", "puertas": "64,63,64,63"},
       {"cruz": "Angulo Izquierdo de la Identificacion 2", "puertas": "1,2,7,13"},
       {"cruz": "Angulo Izquierdo del Desafio 2", "puertas": "2,1,7,13"},
       {"cruz": "Angulo Izquierdo de los Deseos", "puertas": "3,50,7,13"},
       {"cruz": "Angulo Izquierdo de la Revolucion 2", "puertas": "4,49,7,13"},
       {"cruz": "Angulo Izquierdo de la Separacion 2", "puertas": "5,35,8,14"},
       {"cruz": "Angulo Izquierdo del Plano Mundano 2", "puertas": "6,36,8,14"},
       {"cruz": "Angulo Izquierdo de las Mascaras 2", "puertas": "7,13,9,16"},
       {"cruz": "Angulo Izquierdo de la Incertidumbre", "puertas": "8,14,9,16"},
       {"cruz": "Angulo Izquierdo de la Identificacion 2", "puertas": "9,16,10,15"},
       {"cruz": "Angulo Izquierdo de la Prevencion 2", "puertas": "10,15,10,15"},
       {"cruz": "Angulo Izquierdo del Alpha 2", "puertas": "11,12,10,15"},
       {"cruz": "Angulo Izquierdo de la Educacion 2", "puertas": "12,11,10,15"},
       {"cruz": "Angulo Izquierdo de la Convulsion", "puertas": "13,7,17,18"},
       {"cruz": "Angulo Izquierdo de los Desafios 2", "puertas": "14,8,17,18"},
       {"cruz": "Angulo Izquierdo de las Exigencias 2", "puertas": "15,10,17,18"},
       {"cruz": "Angulo Izquierdo del Individualismo", "puertas": "16,9,17,18"},
       {"cruz": "Angulo Izquierdo de la Sanacion", "puertas": "17,18,18,17"},
       {"cruz": "Angulo Izquierdo de la Convulsion 2", "puertas": "18,17,18,17"},
       {"cruz": "Angulo Izquierdo del Refinamiento 2", "puertas": "19,33,20,34"},
       {"cruz": "Angulo Izquierdo de la Incertidumbre 2", "puertas": "20,34,21,48"},
       {"cruz": "Angulo Izquierdo del Empeno", "puertas": "21,48,21,48"},
       {"cruz": "Angulo Izquierdo de Informar", "puertas": "22,47,22,47"},
       {"cruz": "Angulo Izquierdo de la Dedicacion", "puertas": "23,43,23,43"},
       {"cruz": "Angulo Izquierdo de la Encarnacion 2", "puertas": "24,44,24,44"},
       {"cruz": "Angulo Izquierdo de la Migracion 2", "puertas": "25,46,25,46"},
       {"cruz": "Angulo Izquierdo de la Confrontacion 2", "puertas": "26,45,26,45"},
       {"cruz": "Angulo Izquierdo del Alineamiento", "puertas": "27,28,27,28"},
       {"cruz": "Angulo Izquierdo del Alineamiento 2", "puertas": "28,27,28,27"},
       {"cruz": "Angulo Izquierdo de la Industria 2", "puertas": "29,30,29,30"},
       {"cruz": "Angulo Izquierdo de las Exigencias", "puertas": "30,29,30,29"},
       {"cruz": "Angulo Izquierdo del Alpha", "puertas": "31,41,31,41"},
       {"cruz": "Angulo Izquierdo de la Limitacion 2", "puertas": "32,42,32,42"},
       {"cruz": "Angulo Izquierdo del Refinamiento", "puertas": "33,19,33,19"},
       {"cruz": "Angulo Izquierdo de la Dualidad 2", "puertas": "34,20,34,20"},
       {"cruz": "Angulo Izquierdo de la Separacion", "puertas": "35,5,35,5"},
       {"cruz": "Angulo Izquierdo del Plano Mundano", "puertas": "36,6,36,6"},
       {"cruz": "Angulo Izquierdo de la Migracion", "puertas": "37,40,37,40"},
       {"cruz": "Angulo Izquierdo de la Individualismo 2", "puertas": "38,39,38,39"},
       {"cruz": "Angulo Izquierdo del Individualismo", "puertas": "39,38,39,38"},
       {"cruz": "Angulo Izquierdo de la Migracion 2", "puertas": "40,37,40,37"},
       {"cruz": "Angulo Izquierdo de la Separacion 2", "puertas": "41,31,41,31"},
       {"cruz": "Angulo Izquierdo de la Limitacion", "puertas": "42,32,42,32"},
       {"cruz": "Angulo Izquierdo de la Dedicacion 2", "puertas": "43,23,43,23"},
       {"cruz": "Angulo Izquierdo de la Encarnacion", "puertas": "44,24,44,24"},
       {"cruz": "Angulo Izquierdo de la Confrontacion", "puertas": "45,26,45,26"},
       {"cruz": "Angulo Izquierdo del Dominio 2", "puertas": "46,25,46,25"},
       {"cruz": "Angulo Izquierdo de Informar 2", "puertas": "47,22,47,22"},
       {"cruz": "Angulo Izquierdo del Empeno 2", "puertas": "48,21,48,21"},
       {"cruz": "Angulo Izquierdo del Desafio", "puertas": "49,4,49,4"},
       {"cruz": "Angulo Izquierdo de los Deseos 2", "puertas": "50,3,50,3"},
       {"cruz": "Angulo Izquierdo del Clarion", "puertas": "51,57,51,57"},
       {"cruz": "Angulo Izquierdo de las Exigencias", "puertas": "52,58,52,58"},
       {"cruz": "Angulo Izquierdo de los Ciclos", "puertas": "53,54,53,54"},
       {"cruz": "Angulo Izquierdo de los Ciclos 2", "puertas": "54,53,54,53"},
       {"cruz": "Angulo Izquierdo del Espiritu 2", "puertas": "55,59,55,59"},
       {"cruz": "Angulo Izquierdo de la Distraccion 2", "puertas": "56,60,56,60"},
       {"cruz": "Angulo Izquierdo del Clarion 2", "puertas": "57,51,57,51"},
       {"cruz": "Angulo Izquierdo de las Exigencias 2", "puertas": "58,52,58,52"},
       {"cruz": "Angulo Izquierdo de la Dispersion", "puertas": "59,55,59,55"},
       {"cruz": "Angulo Izquierdo del Obscurecimiento", "puertas": "60,56,60,56"},
       {"cruz": "Angulo Izquierdo del Oscurecimiento 2", "puertas": "61,62,61,62"},
       {"cruz": "Angulo Izquierdo de la Preponderancia de lo Pequeño", "puertas": "62,61,62,61"},
       {"cruz": "Angulo Izquierdo del Dominio", "puertas": "63,64,63,64"},
       {"cruz": "Angulo Izquierdo del Dominio 2", "puertas": "64,63,64,63"}
}

    clave = _clave(puerta_con, puerta_in)
    return CRUCES.get(clave, "Cruz desconocida")
'''
   

@app.before_request
def guard():
    # Rutas que SÍ requieren API key
    protected = ("/guardar", "/calcular", "/calcular_dh", "/calcular_kinmaya")
    if request.path.startswith(protected):
        require_api_key()


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
        #pais = fila['pais']

        country_hint = fila.get('pais') 
        # Llamá tu función principal pasando country_hint
        resultado = procesar(anio, mes, dia, hora, minuto, lat, lon, country_hint=country_hint)
        

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/calcular_dh')
def calcular_dh():
    
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
        country_hint = fila['pais']  # Obtener el país si está disponible

        # Llamar a función principal
        resultado = procesar_dh(anio, mes, dia, hora, minuto, lat, lon, country_hint)

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


from flask import request, jsonify

    
@app.route('/guardar', methods=['POST'])
def guardar_datos():
    
    
    configurar_swisseph()
    #print("Ruta actual del proceso:", os.getcwd())
    #print("Archivos disponibles en sweph/ephe:", os.listdir("sweph/ephe"))
   
    try:
        data = request.get_json(silent=True) or {}
        nh = data.get("nh")
        perfil = str(data.get("perfil") or "").strip()
        tipo_dh = str(data.get("tipo_dh") or "").strip()
        id_cruz = str(data.get("id_cruz") or "").strip()

        fecha_nac = (data.get("fecha_nac") or "").strip()         # YYYY-MM-DD
        anio, mes, dia = map(int, fecha_nac.split("-"))

        hora_nac = (data.get("hora_nac") or "").strip()           # HH:MM o HH:MM:SS
        hh, mm = hora_nac.split(":")[0:2]                          # robusto a segundos
        hora, minuto = int(hh), int(mm)

        lat = float(data.get("lat")) if data.get("lat") not in (None, "") else None
        lon = float(data.get("lon")) if data.get("lon") not in (None, "") else None
        country_hint = str(data.get("pais") or "").strip()  

        #data = request.get_json()
        #nh = data.get("nh")
        #tipo_dh = data.get("tipo_dh")
        #perfil = data.get("perfil")
        #fecha_nac = data.get("fecha_nac")  
        #hora_nac = data.get("hora_nac")    
        #lat = data.get("lat")
        #lon = data.get("lon")
        #anio, mes, dia = map(int, fecha_nac.split('-'))
        #hora, minuto = map(int, hora_nac.split(':'))



        if not nh or not tipo_dh or not perfil or not id_cruz or not fecha_nac or not hora_nac :
            return jsonify({"error": "Faltan datos obligatorios"}), 400
        
            # Ahora sí: llamás a las funciones de los planetas
        sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon, False, country_hint)
        luna = obtener_luna(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        mercurio = obtener_mercurio(anio, mes, dia, hora, minuto, lat, country_hint)
        venus = obtener_venus(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        marte = obtener_marte(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        jupiter = obtener_jupiter(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        saturno = obtener_saturno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        urano = obtener_urano(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        neptuno = obtener_neptuno(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        pluton = obtener_pluton(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        quiron = obtener_quiron(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        lilith = obtener_lilith(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        ascendente =  obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        nodoN = obtener_nodoN(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        nodoS = obtener_nodo_sur(anio, mes, dia, hora, minuto, lat, lon, country_hint)
        mc = obtener_mc(anio, mes, dia, hora, minuto, lat, lon, country_hint)
    
        
         
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

        planetas_en_signos12 = {
        "Sol": sol["signo"],
        "Luna": luna["signo"],
        "Mercurio": mercurio["signo"],
        "Venus": venus["signo"],
        "Marte": marte["signo"],
        "Jupiter": jupiter["signo"],
        "Saturno": saturno["signo"],
        "Urano": urano["signo"],
        "Neptuno": neptuno["signo"],
        "Pluton": pluton["signo"],
        "Asc": ascendente["signo"],
        "MC": mc["signo"],
        
    }

  
        
        fractal = calcular_fractal(sol["signo"], ascendente["signo"])
        numero_destino = calcular_numero_destino(dia, mes, anio)
        nro_kin = calcular_kin_onda(anio, mes, dia)["nro_kin"]
        elemento = obtener_elemento(planetas_en_signos12)
        polaridad = polaridad_ponderada_12(planetas_en_signos12)
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
            "perfil": perfil,
            "id_cruz": id_cruz,
       
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
        country_hint = data['pais'] 
        
        modo = request.args.get("modo", "json")
        resultado = procesar(anio, mes, dia, hora, minuto, lat, lon, country_hint=country_hint)
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

