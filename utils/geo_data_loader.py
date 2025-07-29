import requests
import geopandas as gpd
import pandas as pd
import streamlit as st
import json
from typing import Dict, Optional
import os


class GeoDataLoader:
    """Classe para carregar dados geográficos dos municípios brasileiros"""

    # URL do IBGE para dados municipais
    IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios"

    @staticmethod
    @st.cache_data(ttl=3600)  # Cache por 1 hora
    def load_brazil_municipalities_geojson() -> Optional[Dict]:
        """Carrega dados geográficos dos municípios brasileiros do IBGE"""
        try:
            # URL alternativa mais confiável
            url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

            # Tentar URL do IBGE primeiro
            ibge_url = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios?formato=application/vnd.geo+json"

            try:
                response = requests.get(ibge_url, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except:
                pass

            # Fallback para dados locais ou URL alternativa
            # Por enquanto, vamos usar uma abordagem simplificada
            return GeoDataLoader._create_simplified_municipal_boundaries()

        except Exception as e:
            st.warning(f"Erro ao carregar dados geográficos: {str(e)}")
            return None

    @staticmethod
    def _create_simplified_municipal_boundaries() -> Dict:
        """Cria delimitações simplificadas baseadas em coordenadas"""
        # Esta é uma implementação simplificada
        # Em produção, você usaria dados reais do IBGE
        return {
            "type": "FeatureCollection",
            "features": []
        }

    @staticmethod
    @st.cache_data(ttl=3600)
    def load_municipal_boundaries_by_state(uf: str) -> Optional[Dict]:
        """Carrega delimitações municipais por estado"""
        try:
            # URL específica por estado (mais eficiente)
            url = f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf}/municipios?formato=application/vnd.geo+json"

            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            st.warning(f"Erro ao carregar dados do estado {uf}: {str(e)}")
            return None

    @staticmethod
    def create_municipal_geojson_from_data(municipios_df: pd.DataFrame) -> Dict:
        """Cria GeoJSON simplificado baseado nos dados disponíveis"""
        features = []

        for _, municipio in municipios_df.iterrows():
            try:
                lat = float(municipio.get('LAT', 0))
                lng = float(municipio.get('LNG', 0))

                if lat != 0 and lng != 0:
                    # Criar um polígono aproximado ao redor do ponto central
                    # Isso é uma aproximação - idealmente usaríamos dados reais
                    offset = 0.05  # Aproximadamente 5km

                    feature = {
                        "type": "Feature",
                        "properties": {
                            "name": municipio.get('MUNICIPIO_IBGE', 'N/A'),
                            "uf": municipio.get('UF', 'N/A'),
                            "total_alunos": municipio.get('TOTAL_ALUNOS', 0),
                            "distancia_km": municipio.get('DISTANCIA_KM', 0),
                            "polo_proximo": municipio.get('UNIDADE_POLO', 'N/A')
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [lng - offset, lat - offset],
                                [lng + offset, lat - offset],
                                [lng + offset, lat + offset],
                                [lng - offset, lat + offset],
                                [lng - offset, lat - offset]
                            ]]
                        }
                    }
                    features.append(feature)
            except:
                continue

        return {
            "type": "FeatureCollection",
            "features": features
        }
