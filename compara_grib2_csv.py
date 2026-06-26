#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compara dados de um arquivo GRIB2 (u, v, t, gh, r) com limites de CSVs.
Gera relatório de estouros (>15% da faixa).

Uso: python compara_grib2_csv.py arquivo.grib2

author: Rodrigues, L.F. - luflarois@gmail.com
Date: 26Jun2026
License: CC-GPL V3.0
"""

import os
import sys
import numpy as np
import pandas as pd
import pygrib

# Parâmetros
TOLERANCIA = 0.15
NIVEIS_REF = [1000.0, 900.0, 850.0, 800.0, 700.0, 600.0, 500.0, 300.0, 200.0, 100.0, 50.0]
FAIXAS_LAT = [(-90, -60), (-60, -30), (-30, 0), (0, 30), (30, 60), (60, 90)]
NOMES_VAR = ['UGRD', 'VGRD', 'TMP', 'HGT', 'RH']
NOMES_CSV = {'TMP': 'temp.csv', 'HGT': 'geo.csv', 'RH': 'umid.csv', 'WIND': 'vento.csv'}

# Mapeamento dos shortNames do GRIB para os nomes padrão
VAR_MAP = {
    'u': 'UGRD', 'UGRD': 'UGRD',
    'v': 'VGRD', 'VGRD': 'VGRD',
    't': 'TMP', 'TMP': 'TMP',
    'gh': 'HGT', 'HGT': 'HGT',
    'r': 'RH', 'RH': 'RH'
}

def ler_csv_limites(arquivo):
    """Lê arquivo CSV com limites (min, max) por nível e faixa latitudinal."""
    df = pd.read_csv(arquivo, skiprows=3, header=None, names=['nivel'] + [f'v{i}' for i in range(1, 13)])
    limites = {}
    for _, row in df.iterrows():
        nivel = float(row['nivel'])
        if nivel not in NIVEIS_REF:
            continue
        mins = [row[f'v{2*i-1}'] for i in range(1, 7)]
        maxs = [row[f'v{2*i}']   for i in range(1, 7)]
        limites[nivel] = list(zip(mins, maxs))
    return limites

def mapear_faixa_lat(lat):
    for i, (lim_inf, lim_sup) in enumerate(FAIXAS_LAT):
        if lim_inf <= lat < lim_sup:
            return i
    return -1

def nivel_mais_proximo(nivel, niveis_ref, tol=0.05):
    """Retorna o nível de referência mais próximo dentro de tolerância (5%)."""
    for ref in niveis_ref:
        if abs(nivel - ref) / ref <= tol:
            return ref
    return None

def ler_grib2(arquivo_grib):
    """Lê o GRIB2 e retorna campos organizados, coordenadas e níveis."""
    grb = pygrib.open(arquivo_grib)
    campos = {}
    niveis_encontrados = set()
    lats = None
    lons = None
    short_names_disponiveis = set()

    for msg in grb:
        try:
            sn = msg.shortName
            nivel = float(msg.level)
            short_names_disponiveis.add(sn)
        except:
            continue

        # Mapear para nome padrão
        if sn not in VAR_MAP:
            continue
        var_padrao = VAR_MAP[sn]

        # Extrair coordenadas na primeira mensagem útil
        if lats is None:
            try:
                lats, lons = msg.latlons()
                lats = lats[:, 0]   # vetor de latitudes
                lons = lons[0, :]   # vetor de longitudes
            except:
                continue

        # Verificar se o nível está na lista de referência (com tolerância)
        ref_nivel = nivel_mais_proximo(nivel, NIVEIS_REF, tol=0.05)
        if ref_nivel is None:
            continue

        # Armazenar dados
        if var_padrao not in campos:
            campos[var_padrao] = {}
        campos[var_padrao][ref_nivel] = msg.values
        niveis_encontrados.add(ref_nivel)

    grb.close()
    niveis_ordenados = sorted(niveis_encontrados)

    if not campos:
        print("Nenhum campo compatível encontrado.")
        print("ShortNames disponíveis no GRIB:", sorted(short_names_disponiveis))
        return {}, None, None, []

    # Mostrar quais variáveis e níveis foram lidos
    print("Variáveis e níveis encontrados:")
    for var in sorted(campos.keys()):
        nvs = sorted(campos[var].keys())
        print(f"  {var}: {nvs}")

    return campos, lats, lons, niveis_ordenados

def verificar_estouros(var, data, nivel, lats, lons, limites_min, limites_max):
    estouros = []
    if nivel not in limites_min:
        return estouros

    for i, lat in enumerate(lats):
        iband = mapear_faixa_lat(lat)
        if iband == -1:
            continue
        vmin = limites_min[nivel][iband]
        vmax = limites_max[nivel][iband]
        if np.isnan(vmin) or np.isnan(vmax):
            continue
        faixa = vmax - vmin
        if faixa == 0:
            continue
        lim_inf = vmin - TOLERANCIA * faixa
        lim_sup = vmax + TOLERANCIA * faixa

        for j, lon in enumerate(lons):
            valor = data[i, j]
            if np.isnan(valor):
                continue
            if valor < lim_inf or valor > lim_sup:
                if valor < vmin:
                    pct = (vmin - valor) / faixa * 100.0
                else:
                    pct = (valor - vmax) / faixa * 100.0
                estouros.append({
                    'lat': lat,
                    'lon': lon,
                    'nivel': nivel,
                    'variavel': var,
                    'valor': valor,
                    'minimo': vmin,
                    'maximo': vmax,
                    'percentual': pct
                })
    return estouros

def gerar_relatorio(estouros, arquivo_saida='outliers_report.txt'):
    with open(arquivo_saida, 'w') as f:
        f.write('='*70 + '\n')
        f.write('RELATÓRIO DE ESTOUROS (limites ultrapassados em >15% da faixa)\n')
        f.write('='*70 + '\n')
        f.write(f"{'Lat':>8} {'Lon':>8} {'Nível(hPa)':>10} {'Variável':>10} {'Valor':>10} {'Mínimo':>10} {'Máximo':>10} {'%Extrap':>10}\n")
        f.write('-'*70 + '\n')
        for e in estouros:
            f.write(f"{e['lat']:8.2f} {e['lon']:8.2f} {e['nivel']:10.1f} {e['variavel']:>10} {e['valor']:10.2f} {e['minimo']:10.2f} {e['maximo']:10.2f} {e['percentual']:10.1f}\n")
    print(f"Relatório gerado em '{arquivo_saida}'")

def main():
    # Verifica se o arquivo GRIB foi passado como argumento
    if len(sys.argv) < 2:
        print("Uso: python compara_grib2_csv.py arquivo.grib2")
        sys.exit(1)

    grib_file = sys.argv[1]
    if not os.path.exists(grib_file):
        print(f"Arquivo GRIB2 '{grib_file}' não encontrado.")
        sys.exit(1)

    # Ler limites dos CSVs
    limites = {}
    for var, arquivo in NOMES_CSV.items():
        if not os.path.exists(arquivo):
            print(f"Arquivo CSV '{arquivo}' não encontrado.")
            sys.exit(1)
        limites[var] = ler_csv_limites(arquivo)

    limites_min = {}
    limites_max = {}
    for var, dados in limites.items():
        limites_min[var] = {niv: [par[0] for par in faixas] for niv, faixas in dados.items()}
        limites_max[var] = {niv: [par[1] for par in faixas] for niv, faixas in dados.items()}

    print(f"Lendo arquivo GRIB2: {grib_file}")
    campos, lats, lons, niveis = ler_grib2(grib_file)
    if not campos:
        sys.exit(1)

    # Calcular magnitude do vento
    wind_mag = {}
    for nivel in niveis:
        if 'UGRD' in campos and nivel in campos['UGRD'] and 'VGRD' in campos and nivel in campos['VGRD']:
            u = campos['UGRD'][nivel]
            v = campos['VGRD'][nivel]
            wind_mag[nivel] = np.sqrt(u**2 + v**2)

    print("Verificando estouros...")
    todos_estouros = []

    # Verificar TMP, HGT, RH
    for var in ['TMP', 'HGT', 'RH']:
        if var not in campos:
            print(f"Variável {var} não encontrada no GRIB2.")
            continue
        for nivel in niveis:
            if nivel not in campos[var]:
                continue
            data = campos[var][nivel]
            if var not in limites_min or nivel not in limites_min[var]:
                continue
            est = verificar_estouros(var, data, nivel, lats, lons,
                                     limites_min[var], limites_max[var])
            todos_estouros.extend(est)

    # Verificar vento (magnitude)
    for nivel in niveis:
        if nivel in wind_mag:
            data = wind_mag[nivel]
            if 'WIND' not in limites_min or nivel not in limites_min['WIND']:
                continue
            est = verificar_estouros('WIND', data, nivel, lats, lons,
                                     limites_min['WIND'], limites_max['WIND'])
            todos_estouros.extend(est)

    if todos_estouros:
        gerar_relatorio(todos_estouros)
    else:
        print("Nenhum estouro encontrado.")

if __name__ == '__main__':
    main()
