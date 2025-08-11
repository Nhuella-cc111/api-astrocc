'''''
import matplotlib.pyplot as plt
import numpy as np

# Coordenadas del círculo zodiacal
fig, ax = plt.subplots(figsize=(6,6), subplot_kw={'projection': 'polar'})
ax.set_theta_direction(-1)  # Horario
ax.set_theta_offset(np.pi/2)  # Desde arriba
ax.set_yticklabels([])
ax.set_xticklabels([])

# Dividir en 12 casas
for i in range(12):
    angle = i * 30 * np.pi / 180
    ax.plot([angle, angle], [0, 1], color='black')

# Dibujar planetas (ejemplo con 3)
planetas = {
    "Sol": 50,    # grados
    "Luna": 120,
    "Marte": 215,
    "Mercurio": 260,
    "Venus": 95,
    "Jupiter": 130,
    "Pluton": 105,
    "Saturno": 343,
    "Neptuno": 220,
    "Urano": 140,
    "Quiron": 55,
    "Lilith": 84,
    "Ascen": 20,
    "NodoN": 75,
    "NodoS": 15
}

for planeta, grado in planetas.items():
    theta = (360 - grado + 90) % 360  # convertir a dirección polar
    angle_rad = np.deg2rad(theta)
    ax.plot(angle_rad, 0.9, 'o', label=planeta)
    ax.text(angle_rad, 1.05, planeta, ha='center', va='center', fontsize=8)

plt.legend(loc='upper right')
plt.savefig("carta_astral.png")
plt.show()

import matplotlib.pyplot as plt
import numpy as np

# ------------------------
# CONFIGURACIÓN INICIAL
# ------------------------
# Posiciones ficticias de planetas (en grados zodiacales)
planetas = {
    '☉': 47,    # Sol en Tauro
    '☽': 335,   # Luna en Piscis
    '☿': 55,    # Mercurio
    '♀': 65,    # Venus
    '♂': 300,   # Marte
    '♃': 275,   # Júpiter
    '♄': 95,    # Saturno
    '♅': 200,   # Urano
    '♆': 225,   # Neptuno
    '♇': 215,   # Plutón
    '⚷': 150,   # Quirón
    '☊': 10,    # Nodo Norte
    '☋': 190,   # Nodo Sur
    '⚸': 320,   # Lilith
    'Asc': 137,  # Ascendente
}

# Casas ficticias en grados zodiacales
casas = [123.4, 152.6, 182.1, 215.0, 245.8, 275.0, 305.2, 333.5, 3.1, 34.7, 65.3, 95.6]

# Colores por planeta
colores = {
    '☉': 'gold', '☽': 'lightblue', '☿': 'darkgreen', '♀': 'deeppink', '♂': 'red',
    '♃': 'orange', '♄': 'dimgray', '♅': 'royalblue', '♆': 'purple', '♇': 'black',
    '⚷': 'darkviolet', '☊': 'teal', '☋': 'teal', '⚸': 'darkred'
}

# Signos zodiacales (glifos)
signos = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

# ------------------------
# FUNCIONES
# ------------------------
def dibujar_aspectos(ax, planetas, orbes):
    planetas_items = list(planetas.items())
    for i in range(len(planetas_items)):
        p1, g1 = planetas_items[i]
        for j in range(i + 1, len(planetas_items)):
            p2, g2 = planetas_items[j]
            diff = abs(g1 - g2)
            diff = min(diff, 360 - diff)
            for aspecto, (angle, orbe, color) in orbes.items():
                if abs(diff - angle) <= orbe:
                    t1 = np.deg2rad((360 - g1 + 90) % 360)
                    t2 = np.deg2rad((360 - g2 + 90) % 360)
                    ax.plot([t1, t2], [0.2, 0.85], color=color, lw=1)
                    break

# ------------------------
# GRAFICAR CARTA ASTRAL
# ------------------------
fig, ax = plt.subplots(figsize=(9,9), subplot_kw={'projection': 'polar'})
ax.set_theta_direction(-1)
ax.set_theta_offset(np.pi / 2)
ax.set_xticks([])
ax.set_yticks([])
ax.set_facecolor("#f7f7f7")

# Dibujar signos zodiacales
theta_signos = np.linspace(0, 2 * np.pi, 12, endpoint=False)
for i, signo in enumerate(signos):
    angle = theta_signos[i] + np.deg2rad(15)
    ax.text(angle, 1.07, signo, fontsize=24, ha='center', va='center', fontweight='bold', color='darkblue')

# Líneas de signos
for i in range(12):
    angle = np.deg2rad(i * 30)
    ax.plot([angle, angle], [0, 1], color='lightgray', lw=0.8)

# Dibujar casas
for i, casa_grado in enumerate(casas):
    theta = np.deg2rad((360 - casa_grado + 90) % 360)
    ax.plot([theta, theta], [0, 1], color='black', lw=1.2)
    ax.text(theta, 1.02, str(i+1), fontsize=9, ha='center', va='center', color='black')

# Dibujar planetas
for planeta, grado in planetas.items():
    theta = np.deg2rad((360 - grado + 90) % 360)
    ax.plot(theta, 0.85, 'o', color=colores.get(planeta, 'black'), markersize=8)
    ax.text(theta, 0.92, planeta, fontsize=16, ha='center', va='center', color=colores.get(planeta, 'black'))

# Dibujar aspectos
orbes = {
    "conjunción": (0, 8, 'gray')
   # "oposición": (180, 8, 'red'),
   # "trígono": (120, 6, 'green'),
   # "cuadratura": (90, 6, 'red'),
   # "sextil": (60, 5, 'green')
}
dibujar_aspectos(ax, planetas, orbes)

# Título y guardar
ax.set_title("Carta Astral - Posiciones y Aspectos", fontsize=16, pad=20, color='navy')
plt.savefig("carta_astral_completa.png", dpi=300, bbox_inches='tight')
plt.show()
'''

import matplotlib.pyplot as plt
import numpy as np

# ------------------------
# CONFIGURACIÓN INICIAL
# ------------------------
# Posiciones reales de Karina (en grados zodiacales)
planetas = {
    '☉': 38.317,    # Sol 8°19' Tauro
    '☽': 343.86,     # Luna 13°51' Piscis
    '☿': 17.18,      # Mercurio 17°11' Aries
    '♀': 43.25,      # Venus 13°15' Tauro
    '♂': 323.35,     # Marte 23°21' Acuario
    '♃': 280.54,     # Júpiter 10°32' Capricornio
    '♄': 198.23,     # Saturno 18°13' Libra
    '♅': 200.29,     # Urano 20°17' Libra
    '♆': 246.81,     # Neptuno 6°48' Sagitario
    '♇': 182.0,      # Plutón 2°10' Libra
    'ASC': 137.37,   # Ascendente 17°22' Leo
    'MC': 38.32      # Medio Cielo 8°19' Tauro
}

offset = planetas['ASC']  # desplazamiento en grados para alinear el ASC

# Calcular cúspides de casas basadas en ASC cada 30° en sentido antihorario
casas = [(planetas['ASC'] + i * 30) % 360 for i in range(12)]

# Colores por planeta
colores = {
    '☉': 'gold', '☽': 'lightblue', '☿': 'darkgreen', '♀': 'deeppink', '♂': 'red',
    '♃': 'orange', '♄': 'dimgray', '♅': 'royalblue', '♆': 'purple', '♇': 'black',
    'ASC': 'red', 'MC': 'darkblue'
}

signos = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
'''
# ------------------------
# FUNCIONES
# ------------------------
def dibujar_aspectos(ax, planetas, orbes):
    planetas_items = list(planetas.items())
    r_planeta = 0.65  # radio de los símbolos planetarios
    for i in range(len(planetas_items)):
        p1, g1 = planetas_items[i]
        for j in range(i + 1, len(planetas_items)):
            p2, g2 = planetas_items[j]
            diff = abs(g1 - g2)
            diff = min(diff, 360 - diff)
            for aspecto, (angle, orbe, color) in orbes.items():
                if abs(diff - angle) <= orbe:
                    theta1 = np.deg2rad((360 - g1 + 90) % 360)
                    theta2 = np.deg2rad((360 - g2 + 90) % 360)
                    x1, y1 = r_planeta * np.cos(theta1), r_planeta * np.sin(theta1)
                    x2, y2 = r_planeta * np.cos(theta2), r_planeta * np.sin(theta2)
                    ax.plot([x1, x2], [y1, y2], color=color, lw=1)
                    break
'''
# ------------------------
# FUNCIONES Y ROTACIONES
# ------------------------

# Ajuste global de ángulos según el ASC
def ajustar_angulo(grado, asc):
    return (360 - (grado - asc + 360) % 360 + 90) % 360

# Dibujar aspectos como líneas entre planetas si el ángulo cae dentro del orbe
def dibujar_aspectos(ax, planetas, orbes, asc):
    planetas_items = list(planetas.items())
    r_planeta = 0.65
    for i in range(len(planetas_items)):
        p1, g1 = planetas_items[i]
        for j in range(i + 1, len(planetas_items)):
            p2, g2 = planetas_items[j]
            diff = abs(g1 - g2)
            diff = min(diff, 360 - diff)
            for aspecto, (angle, orbe, color) in orbes.items():
                if abs(diff - angle) <= orbe:
                    
                    theta1 = np.deg2rad(ajustar_angulo(g1, asc))
                    theta2 = np.deg2rad(ajustar_angulo(g2, asc))
                    x1, y1 = r_planeta * np.cos(theta1), r_planeta * np.sin(theta1)
                    x2, y2 = r_planeta * np.cos(theta2), r_planeta * np.sin(theta2)
                    ax.plot([x1, x2], [y1, y2], color=color, lw=1)
                    break

# ------------------------
# GRAFICAR CARTA ASTRAL
# ------------------------
fig, ax = plt.subplots(figsize=(10,10))
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor("#f7f7f7")

# Dibujar el círculo exterior del zodíaco, rotado según el ASC
for i, signo in enumerate(signos):
    angle = np.deg2rad(ajustar_angulo(i * 30 + 15, planetas['ASC']))

 #   angle = np.deg2rad((i * 30 - offset + 90) % 360 + 15)  # +15 para centrar el glifo
    x = 1.05 * np.cos(angle)
    y = 1.05 * np.sin(angle)
    ax.text(x, y, signo, fontsize=24, ha='center', va='center', fontweight='bold', color='darkblue')


# Líneas de división de signos

for i in range(12):
 #   angle = np.deg2rad((i * 30 - offset + 90) % 360)
    angle = np.deg2rad(ajustar_angulo(i * 30, planetas['ASC']))

    x0, y0 = 0.75 * np.cos(angle), 0.75 * np.sin(angle)
    x1, y1 = 1.0 * np.cos(angle), 1.0 * np.sin(angle)
    ax.plot([x0, x1], [y0, y1], color='lightgray', lw=0.8)


# Dibujar casas (círculo interno)
for i, casa_grado in enumerate(casas):
#    angle = np.deg2rad((360 - casa_grado + 90) % 360)
    angle = np.deg2rad(ajustar_angulo(casa_grado, planetas['ASC']))

    x0, y0 = 0.5 * np.cos(angle), 0.5 * np.sin(angle)
    x1, y1 = 0.75 * np.cos(angle), 0.75 * np.sin(angle)
    ax.plot([x0, x1], [y0, y1], color='black', lw=1.2)
    ax.text(0.47 * np.cos(angle), 0.47 * np.sin(angle), str(i+1), fontsize=9, ha='center', va='center', color='black')

# Destacar ASC
#theta_asc = np.deg2rad((360 - planetas['ASC'] + 90) % 360)
theta_asc = np.deg2rad(ajustar_angulo(planetas['ASC'], planetas['ASC']))

x0, y0 = 0.5 * np.cos(theta_asc), 0.5 * np.sin(theta_asc)
x1, y1 = 1.0 * np.cos(theta_asc), 1.0 * np.sin(theta_asc)
ax.plot([x0, x1], [y0, y1], color='red', lw=2)
ax.text(1.08 * np.cos(theta_asc), 1.08 * np.sin(theta_asc), "ASC", fontsize=10, ha='center', va='center', color='red')

# Dibujar planetas en el anillo intermedio
for planeta, grado in planetas.items():
#    theta = np.deg2rad((360 - grado + 90) % 360)
    theta = np.deg2rad(ajustar_angulo(grado, planetas['ASC']))

    x, y = 0.65 * np.cos(theta), 0.65 * np.sin(theta)
    ax.plot(x, y, 'o', color=colores.get(planeta, 'black'), markersize=8)
    ax.text(0.70 * np.cos(theta), 0.70 * np.sin(theta), planeta, fontsize=16, ha='center', va='center', color=colores.get(planeta, 'black'))

# Aspectos con orbes personalizados
orbes = {
    "conjunción": (0, 10, 'black'),
    "oposición": (180, 10, 'red'),
    "trígono": (120, 8, 'green'),
    "cuadratura": (90, 8, 'red'),
    "sextil": (60, 6, 'green')
}
#dibujar_aspectos(ax, planetas, orbes)
dibujar_aspectos(ax, planetas, orbes, planetas['ASC'])

ax.set_title("Carta Astral - Mandala Zodiacal", fontsize=16, pad=20, color='navy')
# Círculo interior decorativo
circle = plt.Circle((0, 0), 0.75, transform=ax.transData, fill=False, color='gray', linewidth=0.6, linestyle='dotted')
ax.add_patch(circle)

plt.savefig("carta_astral_doble_circulo.png", dpi=300, bbox_inches='tight')
plt.show()

