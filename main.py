from flask import Flask, request, jsonify
import swisseph as swe
import requests


app = Flask(__name__)
swe.set_ephe_path('.')  # Asegurate que los .se1 estén en el mismo folder

def grados_a_dms(grado_decimal):
    grados = int(grado_decimal)
    minutos = int((grado_decimal - grados) * 60)
    segundos = int((((grado_decimal - grados) * 60) - minutos) * 60)
    return f"{grados:02d}°{minutos:02d}'{segundos:02d}\""


def calcular_casa(jd, lat, lon, grado_planeta):
    cuspides, _ = swe.houses(jd, lat, lon, b'P')  # <--- invertido!
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


#def obtener_offset_horario(lat, lon):
#    api_key = '0KL8FYY73NT2'  # 🔁 Reemplazá con tu API Key de TimeZoneDB
#    url = f'https://api.timezonedb.com/v2.1/get-time-zone?key={api_key}&format=json&by=position&lat={lat}&lng={lon}'
    
#    try:
#        response = requests.get(url)
#        datos = response.json()
#        if datos['status'] == 'OK':
#            offset_segundos = int(datos['gmtOffset'])
#            offset_horas = offset_segundos / 3600
#            return offset_horas
#        else:
#            print(f"Error al obtener zona horaria: {datos['message']}")
#            return 0  # por defecto si falla
#    except Exception as e:
#        print(f"Error de conexión con TimeZoneDB: {e}")
#        return 0

@app.route('/geo', methods=['GET'])
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

@app.route('/sol', methods=['GET'])
def obtener_sol():
    try:
        anio = int(request.args.get("anio"))
        mes = int(request.args.get("mes"))
        dia = int(request.args.get("dia"))
        hora = int(request.args.get("hora"))
        minuto = int(request.args.get("minuto"))
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        offset = obtener_offset_horario(lat, lon)
        hora_utc_decimal = hora + minuto / 60 - offset
        jd = swe.julday(anio, mes, dia, hora_utc_decimal)

        sol = swe.calc_ut(jd, swe.SUN)
        grados_abs = sol[0][0]

        signo = obtener_signo(grados_abs)
        grado_signo = grados_abs % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_abs)

        return jsonify({
            "signo": signo,
            "grados": round(grados_abs, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })
    except Exception as e:
        return jsonify({"error": str(e)})




def obtener_signo(grados):
    signos = [
        "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra",
        "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signos[int(grados // 30)]


@app.route('/ascendente', methods=['GET'])
def obtener_ascendente():
    try:
        anio = int(request.args.get("anio"))
        mes = int(request.args.get("mes"))
        dia = int(request.args.get("dia"))
        hora = int(request.args.get("hora"))
        minuto = int(request.args.get("minuto"))
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        # Calcular hora UTC
        offset = obtener_offset_horario(lat, lon)
        hora_utc_decimal = hora + minuto / 60 - offset

        # Calcular día juliano
        jd = swe.julday(anio, mes, dia, hora_utc_decimal)

        # Calcular casas y ascendente
        casas, ascmc = swe.houses(jd, lat, lon, b'P')
        asc = ascmc[0]
        signo = obtener_signo(asc)
        grado_signo = asc % 30
        formato_dms = grados_a_dms(grado_signo)

        return jsonify({
            "ascendente_grado": round(asc, 2),
            "signo": signo,
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/luna', methods=['GET'])
def obtener_luna():
    try:
        anio = int(request.args.get("anio"))
        mes = int(request.args.get("mes"))
        dia = int(request.args.get("dia"))
        hora = int(request.args.get("hora"))
        minuto = int(request.args.get("minuto"))
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        offset = obtener_offset_horario(lat, lon)
        hora_utc_decimal = hora + minuto / 60 - offset
        jd = swe.julday(anio, mes, dia, hora_utc_decimal)

        # Posición de la Luna
        grados_luna = swe.calc_ut(jd, swe.MOON)[0][0]
        signo = obtener_signo(grados_luna)
        grado_signo = grados_luna % 30
        formato_dms = grados_a_dms(grado_signo)

        # Determinar casa
        casa = calcular_casa(jd, lat, lon, grados_luna)
        #print(f"lat: {lat}, lon: {lon}, offset: {offset}, hora_utc: {hora_utc_decimal}, jd: {jd}")

        return jsonify({
            "signo": signo,
            "grados": round(grados_luna, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

