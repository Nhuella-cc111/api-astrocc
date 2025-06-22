from flask import Flask, request, jsonify
import swisseph as swe
import requests

swe.set_ephe_path('.')  # Asegurate que los .se1 estén en el mismo folder

app = Flask(__name__)



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

@app.route('/mercurio', methods=['GET'])
def obtener_mercurio():
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

        grados_mercurio = swe.calc_ut(jd, swe.MERCURY)[0][0]
        signo = obtener_signo(grados_mercurio)
        grado_signo = grados_mercurio % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_mercurio)

        return jsonify({
            "signo": signo,
            "grados": round(grados_mercurio, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/venus', methods=['GET'])
def obtener_venus():
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

        grados_venus = swe.calc_ut(jd, swe.VENUS)[0][0]
        signo = obtener_signo(grados_venus)
        grado_signo = grados_venus % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_venus)

        return jsonify({
            "signo": signo,
            "grados": round(grados_venus, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})
       

@app.route('/marte', methods=['GET'])
def obtener_marte():
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

        grados_marte = swe.calc_ut(jd, swe.MARS)[0][0]
        signo = obtener_signo(grados_marte)
        grado_signo = grados_marte % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_marte)

        return jsonify({
            "signo": signo,
            "grados": round(grados_marte, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/jupiter', methods=['GET'])
def obtener_jupiter():
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

        grados_jupiter = swe.calc_ut(jd, swe.JUPITER)[0][0]
        signo = obtener_signo(grados_jupiter)
        grado_signo = grados_jupiter % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_jupiter)

        return jsonify({
            "signo": signo,
            "grados": round(grados_jupiter, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})
        
@app.route('/saturno', methods=['GET'])
def obtener_saturno():
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

        grados_saturno = swe.calc_ut(jd, swe.SATURN)[0][0]
        signo = obtener_signo(grados_saturno)
        grado_signo = grados_saturno % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_saturno)

        return jsonify({
            "signo": signo,
            "grados": round(grados_saturno, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/urano', methods=['GET'])
def obtener_urano():
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

        grados_urano = swe.calc_ut(jd, swe.URANUS)[0][0]
        signo = obtener_signo(grados_urano)
        grado_signo = grados_urano % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_urano)

        return jsonify({
            "signo": signo,
            "grados": round(grados_urano, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/neptuno', methods=['GET'])
def obtener_neptuno():
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

        grados_neptuno = swe.calc_ut(jd, swe.NEPTUNE)[0][0]
        signo = obtener_signo(grados_neptuno)
        grado_signo = grados_neptuno % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_neptuno)

        return jsonify({
            "signo": signo,
            "grados": round(grados_neptuno, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })


    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/pluton', methods=['GET'])
def obtener_pluton():
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

        grados_pluton = swe.calc_ut(jd, swe.PLUTO)[0][0]
        signo = obtener_signo(grados_pluton)
        grado_signo = grados_pluton % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_pluton)

        return jsonify({
            "signo": signo,
            "grados": round(grados_pluton, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })


    except Exception as e:
        return jsonify({"error": str(e)})
        

@app.route('/nodoN', methods=['GET'])
def obtener_nodoN():
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

        grados_nodoN = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
        signo = obtener_signo(grados_nodoN)
        grado_signo = grados_nodoN % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_nodoN)

        return jsonify({
            "signo": signo,
            "grados": round(grados_nodoN, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })


    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/quiron', methods=['GET'])
def obtener_quiron():
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

        grados_quiron = swe.calc_ut(jd, swe.CHIRON)[0][0]
        signo = obtener_signo(grados_quiron)
        grado_signo = grados_quiron % 30
        formato_dms = grados_a_dms(grado_signo)

        casa = calcular_casa(jd, lat, lon, grados_quiron)

        return jsonify({
            "signo": signo,
            "grados": round(grados_quiron, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })


    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/lilith', methods=['GET'])
def obtener_lilith():
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

        grados_lilith = swe.calc_ut(jd, 12)[0][0]  # Lilith media
        signo = obtener_signo(grados_lilith)
        grado_signo = grados_lilith % 30
        formato_dms = grados_a_dms(grado_signo)
        casa = calcular_casa(jd, lat, lon, grados_lilith)

        return jsonify({
            "signo": signo,
            "grados": round(grados_lilith, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}",
            "casa": casa
        })

    except Exception as e:
        return jsonify({"error": str(e)})

        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

