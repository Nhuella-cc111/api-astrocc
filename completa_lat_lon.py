#!/usr/bin/env python3
"""
Pre-carga de lat/lon desde Excel usando LocationIQ o Google Geocoding.
- Lee un Excel con columnas: ciudad, provincia, pais (minúsculas).
- Geocodifica y agrega lat, lon, ciudad_normalizada, provincia_normalizada y label_geocoder.
- Usa caché local para no repetir consultas.
- Exporta un Excel listo para subir a Supabase.

Novedades:
- Soporte robusto de argumentos con argparse.
- Manejo seguro de rutas con pathlib.Path.
- Carga de .env con find_dotenv(..., override=True).
- Fuerza engine="openpyxl" al leer .xlsx (evita errores de pandas).
- Normalización de ciudad (remueve "Municipio de ", "Distrito ciudad de ", "Distrito de ", "Departamento de", "Dpto./Depto. de", "Partido de", "Comuna de").
- Nueva columna provincia_normalizada (remueve "Provincia de ", "Province of ", y sufijo "province/provincia").

Requisitos:
    pip install pandas requests python-dotenv openpyxl

Variables de entorno (.env en la misma carpeta o en algún padre):
    GEOCODER_PROVIDER=locationiq   # o "google"
    LOCATIONIQ_KEY=tu_token_locationiq (formato pk.... si es LocationIQ)
    GOOGLE_API_KEY=tu_api_key_google
    # Opcional Supabase REST
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...

Uso:
    python pre_carga_geocodificacion_excel_a_supabase.py "C:/ruta/input.xlsx" "C:/ruta/output_geocodificado.xlsx"
    # Si omites el segundo argumento, genera input_geocodificado.xlsx en la misma carpeta.
"""
import os
import sys
import time
import json
import re
import warnings
import argparse
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests
from dotenv import load_dotenv, find_dotenv

warnings.simplefilter("ignore", category=FutureWarning)

# -------------------- Utilidades --------------------

def slug(s: str) -> str:
    return (
        str(s or "").strip()
        .replace("  ", " ")
        .replace(",,", ",")
        .lower()
    )


def build_query(ciudad: str, provincia: str, pais: str) -> str:
    partes = [str(ciudad or "").strip(), str(provincia or "").strip(), str(pais or "").strip()]
    partes = [p for p in partes if p]
    return ", ".join(partes)


def iso2_from_country(pais: str) -> Optional[str]:
    m = {
        "argentina": "ar",
        "uruguay": "uy",
        "chile": "cl",
        "paraguay": "py",
        "brasil": "br",
        "bolivia": "bo",
        "peru": "pe",
        "mexico": "mx",
        "spain": "es",
        "españa": "es",
    }
    return m.get((pais or "").strip().lower())


def normalize_city_label(s: Optional[str]) -> str:
    """Quita prefijos como 'Municipio de ', 'Distrito ciudad de ', 'Distrito de ', 'Departamento de', 'Dpto./Depto. de', 'Partido de', 'Comuna de' (ignora mayúsculas)."""
    s = (s or "").strip()
    if not s:
        return ""
    s = re.sub(r"^\s*(municipio\s+de|distrito\s+ciudad\s+de|distrito\s+de|departamento\s+de|dpto\.?\s+de|depto\.?\s+de|partido\s+de|comuna\s+de)\s+", "", s, flags=re.IGNORECASE)
    return s.strip(" ,")


def normalize_province_label(s: Optional[str]) -> str:
    """Quita 'Provincia de ', 'Province of ' y el sufijo 'province/provincia'."""
    s = (s or "").strip()
    if not s:
        return ""
    # prefijos comunes
    s = re.sub(r"^\s*(provincia\s+de|province\s+of)\s+", "", s, flags=re.IGNORECASE)
    # sufijo 'Province' o 'Provincia'
    s = re.sub(r"\s*\b(province|provincia)\b\.?$", "", s, flags=re.IGNORECASE)
    return s.strip(" ,")


# -------------------- Proveedores --------------------

class Geocoder:
    def geocode(self, query: str, country_hint: Optional[str] = None) -> Optional[Dict]:
        raise NotImplementedError


class LocationIQGeocoder(Geocoder):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def geocode(self, query: str, country_hint: Optional[str] = None) -> Optional[Dict]:
        params = {
            "key": self.api_key,
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "normalizecity": 1,
            "dedupe": 1,
        }
        if country_hint:
            params["countrycodes"] = country_hint
        try:
            r = self.session.get("https://us1.locationiq.com/v1/search", params=params, timeout=20)
            if r.status_code == 429:
                time.sleep(2)
                r = self.session.get("https://us1.locationiq.com/v1/search", params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data:
                item = data[0]
                lat = float(item.get("lat"))
                lon = float(item.get("lon"))
                label = item.get("display_name")
                addr = item.get("address", {})
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("hamlet")
                prov = addr.get("state") or addr.get("region") or addr.get("province")
                return {
                    "lat": lat,
                    "lon": lon,
                    "label": label,
                    "city_std": city or "",
                    "prov_std": prov or "",
                    "provider": "locationiq",
                }
        except Exception:
            return None
        return None


class GoogleGeocoder(Geocoder):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def geocode(self, query: str, country_hint: Optional[str] = None) -> Optional[Dict]:
        params = {"address": query, "key": self.api_key}
        if country_hint:
            params["components"] = f"country:{country_hint}"
        try:
            r = self.session.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "OK" and data.get("results"):
                res0 = data["results"][0]
                loc = res0["geometry"]["location"]
                lat = float(loc["lat"])
                lon = float(loc["lng"])  # Google usa 'lng'
                label = res0.get("formatted_address")
                city = ""
                prov = ""
                for comp in res0.get("address_components", []):
                    types = comp.get("types", [])
                    if not city and ("locality" in types or "administrative_area_level_2" in types):
                        city = comp.get("long_name", "")
                    if not prov and "administrative_area_level_1" in types:
                        prov = comp.get("long_name", "")
                return {
                    "lat": lat,
                    "lon": lon,
                    "label": label,
                    "city_std": city,
                    "prov_std": prov,
                    "provider": "google",
                }
        except Exception:
            return None
        return None


# -------------------- Caché simple en CSV --------------------

class GeoCache:
    def __init__(self, path: str = "cache_geocoding.csv"):
        self.path = path
        self.data: Dict[str, Dict] = {}
        if os.path.exists(self.path):
            try:
                df = pd.read_csv(self.path)
                for _, row in df.iterrows():
                    self.data[str(row["query_key"])]= {
                        "lat": row.get("lat"),
                        "lon": row.get("lon"),
                        "label": row.get("label", ""),
                        "city_std": row.get("city_std", ""),
                        "prov_std": row.get("prov_std", ""),
                        "provider": row.get("provider", "")
                    }
            except Exception:
                pass

    def get(self, query_key: str) -> Optional[Dict]:
        return self.data.get(query_key)

    def set(self, query_key: str, value: Dict):
        self.data[query_key] = value

    def flush(self):
        if not self.data:
            return
        rows = [{"query_key": k, **v} for k, v in self.data.items()]
        pd.DataFrame(rows).to_csv(self.path, index=False)


# -------------------- Supabase REST insert (opcional) --------------------

def insert_supabase_rest(table: str, rows: list) -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[Supabase] Variables no definidas. Se omite el insert.")
        return
    endpoint = url.rstrip("/") + f"/rest/v1/{table}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    r = requests.post(endpoint, headers=headers, data=json.dumps(rows), timeout=60)
    try:
        r.raise_for_status()
        print(f"[Supabase] Insertados {len(rows)} registros en {table}.")
    except Exception:
        print("[Supabase] Error:", r.status_code, r.text)
        raise


# -------------------- Argumentos y Main --------------------

def parse_args():
    p = argparse.ArgumentParser(description="Geocodificación masiva para rtas_form desde Excel")
    p.add_argument("input", help="Ruta al Excel de entrada (.xlsx) o CSV")
    p.add_argument("output", nargs="?", help="Ruta al Excel de salida (.xlsx). Si se omite, genera *_geocodificado.xlsx")
    return p.parse_args()


def read_table(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf == ".xlsx":
        try:
            return pd.read_excel(path, engine="openpyxl")
        except ImportError:
            raise SystemExit("Falta 'openpyxl'. Instala: pip install openpyxl")
    elif suf == ".csv":
        return pd.read_csv(path)
    else:
        raise SystemExit("Formato no soportado. Usa .xlsx o .csv")


def write_excel(df: pd.DataFrame, path: Path):
    try:
        df.to_excel(path, index=False)
    except ImportError:
        raise SystemExit("Falta 'openpyxl' para escribir .xlsx. Instala: pip install openpyxl")


def main():
    # Cargar .env esté donde esté (proyecto, padre, etc.) y permitir override
    load_dotenv(find_dotenv(), override=True)

    args = parse_args()
    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo de entrada: {in_path}")
    out_path = Path(args.output).expanduser().resolve() if args.output else in_path.with_name(in_path.stem + "_geocodificado.xlsx")

    provider = (os.getenv("GEOCODER_PROVIDER") or "locationiq").strip().lower()
    polite_delay = 0.0

    if provider == "locationiq":
        key = os.getenv("LOCATIONIQ_KEY")
        if not key:
            raise SystemExit("Falta LOCATIONIQ_KEY en .env o en variables de entorno.")
        geocoder: Geocoder = LocationIQGeocoder(key)
        polite_delay = 1.1  # evitar 429 en planes con 1 req/seg
    elif provider == "google":
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise SystemExit("Falta GOOGLE_API_KEY en .env o en variables de entorno.")
        geocoder = GoogleGeocoder(key)
        polite_delay = 0.0
    else:
        raise SystemExit("GEOCODER_PROVIDER debe ser 'locationiq' o 'google'")

    print(f"Proveedor: {provider}")

    df = read_table(in_path)

    for col in ["ciudad", "provincia", "pais"]:
        if col not in df.columns:
            raise SystemExit(f"Falta columna obligatoria: {col}")

    # Preparar consultas únicas
    df["_query"] = df.apply(lambda r: build_query(r.get("ciudad", ""), r.get("provincia", ""), r.get("pais", "")), axis=1)
    df["_key"] = df["_query"].apply(lambda s: slug(s))
    unicos = [k for k in df["_key"].unique().tolist() if k]

    cache = GeoCache()
    resultados: Dict[str, Dict] = {}

    for qkey in unicos:
        query = df.loc[df["_key"] == qkey, "_query"].iloc[0]
        cached = cache.get(qkey)
        if cached is not None:
            resultados[qkey] = cached
            continue

        hint = iso2_from_country(query.split(",")[-1]) if "," in query else None
        resp = geocoder.geocode(query, country_hint=hint)
        if resp is None and "," in query:
            partes = [p.strip() for p in query.split(",") if p.strip()]
            if len(partes) >= 2:
                fallback = ", ".join([partes[0], partes[-1]])
                resp = geocoder.geocode(fallback, country_hint=hint)

        if resp:
            resultados[qkey] = resp
            cache.set(qkey, resp)
        else:
            vacio = {"lat": None, "lon": None, "label": "", "city_std": "", "prov_std": "", "provider": provider}
            resultados[qkey] = vacio
            cache.set(qkey, vacio)

        if polite_delay:
            time.sleep(polite_delay)

    cache.flush()

    # Volcar resultados al DF (con normalización pedida)
    def _city_norm(row):
        val = resultados.get(row["_key"], {}).get("city_std") or str(row.get("ciudad", ""))
        return normalize_city_label(val)

    def _prov_norm(row):
        val = resultados.get(row["_key"], {}).get("prov_std") or str(row.get("provincia", ""))
        return normalize_province_label(val)

    df["lat"] = df["_key"].apply(lambda k: resultados.get(k, {}).get("lat"))
    df["lon"] = df["_key"].apply(lambda k: resultados.get(k, {}).get("lon"))
    df["ciudad_normalizada"] = df.apply(_city_norm, axis=1)
    df["provincia_normalizada"] = df.apply(_prov_norm, axis=1)
    df["label_geocoder"] = df["_key"].apply(lambda k: resultados.get(k, {}).get("label"))
    df["geocoder"] = df["_key"].apply(lambda k: resultados.get(k, {}).get("provider"))

    # Orden de columnas (deja las originales primero)
    base_cols = [
        "ciudad", "provincia", "pais",
        "lat", "lon",
        "ciudad_normalizada", "provincia_normalizada",
        "label_geocoder", "geocoder"
    ]
    cols_order = []
    for c in base_cols:
        if c in df.columns or c in [
            "lat", "lon", "ciudad_normalizada", "provincia_normalizada", "label_geocoder", "geocoder"
        ]:
            cols_order.append(c)
    for c in df.columns:
        if c not in cols_order and not c.startswith("_"):
            cols_order.append(c)

    df = df[[c for c in cols_order if c in df.columns]]

    write_excel(df, out_path)
    print(f"Archivo generado: {out_path} ({len(df)} filas)")

    # --- (OPCIONAL) Insertar directamente en Supabase ---
    # if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    #     filas = []
    #     for _, r in df.iterrows():
    #         filas.append({
    #             "ciudad": r.get("ciudad"),
    #             "provincia": r.get("provincia"),
    #             "pais": r.get("pais"),
    #             "lat": r.get("lat"),
    #             "lon": r.get("lon"),
    #             # agrega aquí el resto de campos requeridos por rtas_form
    #         })
    #     insert_supabase_rest("rtas_form", filas)


if __name__ == "__main__":
    main()

