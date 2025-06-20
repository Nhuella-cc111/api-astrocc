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


@app.route('/sol', methods=['GET'])
def obtener_sol():
    try:
        anio = int(request.args.get("anio"))
        mes = int(request.args.get("mes"))
        dia = int(request.args.get("dia"))
        hora = int(request.args.get("hora"))
        minuto = int(request.args.get("minuto"))

        hora_decimal = hora + minuto / 60
        jd = swe.julday(anio, mes, dia, hora_decimal)
        sol = swe.calc_ut(jd, swe.SUN)
        grados_abs = sol[0][0]

        signo = obtener_signo(grados_abs)
        grado_signo = grados_abs % 30
        formato_dms = grados_a_dms(grado_signo)

        return jsonify({
            "signo": signo,
            "grados": round(grados_abs, 2),
            "grado_en_signo": formato_dms,
            "signo_completo": f"{formato_dms} {signo}"
        })
    except Exception as e:
        return jsonify({"error": str(e)})


#@app.route('/sol', methods=['GET'])
#def obtener_sol():
#    try:
#        anio = int(request.args.get("anio"))
#        mes = int(request.args.get("mes"))
#        dia = int(request.args.get("dia"))
#        hora = int(request.args.get("hora"))
#        minuto = int(request.args.get("minuto"))

#        hora_decimal = hora + minuto / 60
#        jd = swe.julday(anio, mes, dia, hora_decimal)
#        sol = swe.calc_ut(jd, swe.SUN)
#        grados = sol[0][0]
#        signo = obtener_signo(grados)

#        return jsonify({"signo": signo, "grados": round(grados, 2)})
#    except Exception as e:
#        return jsonify({"error": str(e)})

def obtener_signo(grados):
    signos = [
        "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", "Libra",
        "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
    ]
    return signos[int(grados // 30)]

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





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

