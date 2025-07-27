from flask import Flask, request, jsonify
from supabase import create_client
import swisseph as swe
import requests
from datetime import date
from datetime import datetime, timedelta
import pytz



app = Flask(__name__)

swe.set_ephe_path('.')  # Asegurate que los .se1 estén en el mismo folder

SUPABASE_URL = "https://amjskrqaoiuabscecmji.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtanNrcnFhb2l1YWJzY2VjbWppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5Nzg3NDksImV4cCI6MjA2NjU1NDc0OX0.t_9h25ehDGBWGz39YmMPdeeaFyWpQcoDR0POt5Y3CXQ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def grados_a_dms(grado_decimal):
    grados = int(grado_decimal)
    minutos = int((grado_decimal - grados) * 60)
    segundos = int((((grado_decimal - grados) * 60) - minutos) * 60)
    return f"{grados:02d}°{minutos:02d}'{segundos:02d}\""


def calcular_casa(jd, lat, lon, grado_planeta):

    cuspides, _ = swe.houses(jd, lat, lon, b'P')  # <--- invertido!
    print(f"Cúspides: {cuspides}")
    print(f"Grado planeta: {grado_planeta}")
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



def obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon):
    # Asignamos zona horaria correcta (Comodoro usa zona Argentina)
    tz = pytz.timezone("America/Argentina/Buenos_Aires")  # válido para todo el país
    dt_local = datetime(anio, mes, dia, hora, minuto)
    offset = tz.utcoffset(dt_local).total_seconds() / 3600
    return offset
'''
def obtener_offset_horario(lat, lon):
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
        api_key = "21f0075720f44914b2cfdd8e64c27b68"  # <-- reemplazá por tu key real
        url = f"https://api.opencagedata.com/geocode/v1/json?q={direccion}&key={api_key}&language=es&pretty=1"

        response = requests.get(url)
        data = response.json()

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
        "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra",
        "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signos[int(grados // 30)]


def obtener_sol(anio, mes, dia, hora, minuto, lat, lon):
    print(
        f"🛰️ Procesando Sol → {anio}-{mes}-{dia} {hora}:{minuto}, lat: {lat}, lon: {lon}"
    )
    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Posición del Sol
    grados_sol = swe.calc_ut(jd, swe.SUN)[0][0]
    signo = obtener_signo(grados_sol)
    grado_signo = grados_sol % 30
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


def obtener_ascendente(anio, mes, dia, hora, minuto, lat, lon):
    # Calcular hora UTC
    offset = obtener_offset_horario(anio, mes, dia, hora, minuto, lat, lon)
    hora_utc_decimal = hora + minuto / 60 - offset
    # Calcular día juliano
    jd = swe.julday(anio, mes, dia, hora_utc_decimal)

    # Calcular casas y ascendente
    casas, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = ascmc[0]
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
    """
    Determina el elemento predominante (o elementos en caso de empate).

    Argumentos:
        planetas_en_signos (dict): Diccionario con nombres de planetas como claves
                                   y sus signos zodiacales como valores.

    Retorna:
        str: Elemento(s) predominante(s), separados por "-" si hay empate.
    """

    elementos_por_signo = {
        "Aries": "Fuego",
        "Leo": "Fuego",
        "Sagitario": "Fuego",
        "Cáncer": "Agua",
        "Escorpio": "Agua",
        "Piscis": "Agua",
        "Géminis": "Aire",
        "Libra": "Aire",
        "Acuario": "Aire",
        "Tauro": "Tierra",
        "Virgo": "Tierra",
        "Capricornio": "Tierra"
    }

    contador_elementos = {"Fuego": 0, "Agua": 0, "Aire": 0, "Tierra": 0}

    for signo in planetas_en_signos.values():
        elemento = elementos_por_signo.get(signo)
        if elemento:
            contador_elementos[elemento] += 1

    # Encontrar el máximo valor
    max_valor = max(contador_elementos.values())

    # Obtener todos los elementos que tienen ese valor máximo
    elementos_dominantes = [
        elemento for elemento, cantidad in contador_elementos.items()
        if cantidad == max_valor
    ]

    # Unirlos con guiones si hay más de uno
    return "-".join(elementos_dominantes)


def obtener_polaridad(planetas_en_signos):
    """
    Retorna la polaridad predominante: 'Positivo', 'Negativo' o 'Equilibrio'.
    """

    polaridad_por_signo = {
        "Aries": "Positivo",
        "Leo": "Positivo",
        "Sagitario": "Positivo",
        "Géminis": "Positivo",
        "Libra": "Positivo",
        "Acuario": "Positivo",
        "Tauro": "Negativo",
        "Cáncer": "Negativo",
        "Virgo": "Negativo",
        "Escorpio": "Negativo",
        "Capricornio": "Negativo",
        "Piscis": "Negativo"
    }

    contador_polaridad = {"Positivo": 0, "Negativo": 0}

    for signo in planetas_en_signos.values():
        polaridad = polaridad_por_signo.get(signo)
        if polaridad:
            contador_polaridad[polaridad] += 1

    if contador_polaridad["Positivo"] == contador_polaridad["Negativo"]:
        return "Equilibrio"

    # Devolver directamente la clave con mayor cantidad
    return max(contador_polaridad, key=contador_polaridad.get)


def obtener_modalidad(planetas_en_signos):
    """
    Determina la modalidad predominante (o modalidades en caso de empate).

    Argumentos:
        planetas_en_signos (dict): Diccionario con nombres de planetas como claves
                                   y sus signos zodiacales como valores.

    Retorna:
        str: modalidad(s) predominante(s), separados por "-" si hay empate.
    """

    modalidad_por_signo = {
        "Aries": "Cardinal",
        "Leo": "Fija",
        "Sagitario": "Mutable",
        "Cáncer": "Cardinal",
        "Escorpio": "Fija",
        "Piscis": "Mutable",
        "Géminis": "Mutable",
        "Libra": "Cardinal",
        "Acuario": "Fija",
        "Tauro": "Fija",
        "Virgo": "Mutable",
        "Capricornio": "Cardinal"
    }

    contador_modalidad = {"Cardinal": 0, "Fija": 0, "Mutable": 0}

    for signo in planetas_en_signos.values():
        modalidad = modalidad_por_signo.get(signo)
        if modalidad:
            contador_modalidad[modalidad] += 1

    # Encontrar el máximo valor
    max_valor = max(contador_modalidad.values())

    # Obtener todos las modalidades que tienen ese valor máximo
    modalidad_dominantes = [
        m for m, cantidad in contador_modalidad.items()
        if cantidad == max_valor
    ]

    # Unirlos con guiones si hay más de uno
    return "-".join(modalidad_dominantes)
    

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


'''
from datetime import datetime, timedelta
from flask import jsonify

from datetime import datetime, timedelta
from flask import Flask, request

app = Flask(__name__)
'''
def cumple_kin(kin):
    if not isinstance(kin, int) or kin < 1 or kin > 260:
        return None

    ciclo = 260
    hoy = datetime.now()
    inicio_ciclo = datetime(2025, 3, 25)  # 25/03/2025

    dias_desde_inicio = (hoy - inicio_ciclo).days
    ciclos_pasados = dias_desde_inicio // ciclo
    fecha_ultimo_inicio = inicio_ciclo + timedelta(days=ciclos_pasados * ciclo)
    fecha_cumple_kin = fecha_ultimo_inicio + timedelta(days=(kin - 1))

    return fecha_cumple_kin.strftime("%d/%m/%Y")
    




def procesar(anio, mes, dia, hora, minuto, lat, lon):

    # Ahora sí: llamás a las funciones de los planetas
    sol = obtener_sol(anio, mes, dia, hora, minuto, lat, lon)
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
        "Júpiter": jupiter["signo"],
        "Saturno": saturno["signo"],
        "Urano": urano["signo"],
        "Neptuno": neptuno["signo"],
        "Plutón": pluton["signo"],
        "Quiron": quiron["signo"],
        "Lilith": lilith["signo"]
    }

    planetas_nodos = {
        "nodoN": nodoN["signo"],
        "nodoS": nodoS["signo"]
    }    
    '''
    # Obtener y mostrar el elemento predominante
    elemento_dominante = obtener_elemento(planetas_en_signos)
    print("🌟 Elemento predominante en tu carta:", elemento_dominante)
    polaridad_dominante = obtener_polaridad(planetas_en_signos)
    print("🌟 Polaridad predominante en tu carta:", polaridad_dominante)
    modalidad_dominante = obtener_modalidad(planetas_en_signos)
    print("🌟 Modalidad predominante en tu carta:", modalidad_dominante)
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
        "grados_sol": sol["grados"],
        "grados_luna": luna["grados"],
        "luna_nac": obtener_fase_lunar(sol["grados"], luna["grados"]),
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
        "nodoN": nodoN["signo"],
        "gr_nodoN": nodoN["grado_en_signo"],
        "c_nodoN": nodoN["casa"],
        "nodoS": nodoS["signo"],
        "gr_nodoS": nodoS["grado_en_signo"],
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
        "rayo": dia_y_rayo(dia, mes, anio)["color"]
        
    }
    return registro


@app.route('/calcular')
def calcular():
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

'''
@app.route('/cumplekin', methods=['GET'])
def api_cumple_kin():
    try:
        kin_param = request.args.get('kin')
        print(f"Kin recibido: {kin_param}")
        kin = int(kin_param)

        resultado = cumple_kin(kin)
        print(f"Resultado: {resultado}")  # <-- Debug

        return jsonify(resultado)
    except Exception as e:
        print(f"Error en /cumplekin: {e}")
        return jsonify({"error": str(e)}), 500
'''
        

@app.route('/')
def home():
    return "✅ API Carnet Cósmico funcionando. Usá /calcular?nh=..."
