from supabase import create_client
import requests



url = "https://amjskrqaoiuabscecmji.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtanNrcnFhb2l1YWJzY2VjbWppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5Nzg3NDksImV4cCI6MjA2NjU1NDc0OX0.t_9h25ehDGBWGz39YmMPdeeaFyWpQcoDR0POt5Y3CXQ"


supabase = create_client(url, key)

datos = {
    
    "nombre": "Test Karina",
    "fecha_nac": '09/09/1987',
    "hora": 2,
    "minuto": 15,
    "ciudad": "Andorra",
    "provincia": "Andorra la Vella",
    "pais": "Andorra",
    "lat": 42.5069391,
    "lon": 1.5212467,
    "sol": "Virgo",
    "gr_sol": "15°48'09\"",
    "c_sol": 3,
    "ascen": "Cáncer",
    "gr_asc": "15°48'09\"",
    "luna": "Aries",
    "gr_luna": "05°47'32\"",
    "c_luna": 10,
    "id": 1
}

respuesta = supabase.table("resultados").insert(datos).execute()
print(respuesta)
