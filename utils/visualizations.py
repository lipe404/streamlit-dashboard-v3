import geopandas as gpd
import json
# from utils.geo_data_loader import GeoDataLoader # Removido se não estiver em uso para evitar erro de importação
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import folium
from folium import plugins
import streamlit as st
from typing import Dict, List, Tuple, Any
from streamlit_folium import st_folium


class Visualizations:
    """Classe para criar visualizações interativas"""

    def __init__(self, colors: Dict[str, str]):
        self.colors = colors

    def create_polos_map(
            self, polos_df: pd.DataFrame, map_config: Dict) -> folium.Map:
        """Cria mapa interativo dos polos"""
        m = folium.Map(
            location=[map_config['center_lat'], map_config['center_lon']],
            zoom_start=map_config['zoom']
        )

        if not polos_df.empty:
            for _, polo in polos_df.iterrows():
                try:
                    lat_val = polo.get('lat', None)
                    lng_val = polo.get('long', None)

                    if pd.notna(lat_val) and pd.notna(lng_val):
                        folium.Marker(
                            location=[float(lat_val), float(lng_val)],
                            popup=f"""
                            <b>{polo.get('UNIDADE', 'N/A')}</b><br>
                            Cidade: {polo.get('CIDADE', 'N/A')}<br>
                            UF: {polo.get('UF', 'N/A')}<br>
                            Endereço: {polo.get('ENDERECO', 'N/A')}
                            """,
                            tooltip=polo.get('UNIDADE', 'N/A'),
                            icon=folium.Icon(
                                color='blue',
                                icon='graduation-cap', prefix='fa')
                        ).add_to(m)
                except Exception as e:
                    continue

        return m

    # Adicione este método à classe Visualizations
    def create_municipal_coverage_map_with_boundaries(
            self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame,
            map_config: Dict) -> folium.Map:
        """Cria mapa de cobertura municipal com delimitações geográficas reais"""

        # Criar mapa base
        m = folium.Map(
            location=[map_config['center_lat'], map_config['center_lon']],
            zoom_start=map_config['zoom'],
            tiles='OpenStreetMap'
        )

        try:
            # REMOVIDO: Uso de GeoDataLoader direto, pois não está definido no código fornecido.
            # Se você tem um geo_data_loader.py, mantenha essa parte e o import.
            # municipal_geojson = GeoDataLoader.create_municipal_geojson_from_data(
            #     municipios_df)
            # if municipal_geojson and municipal_geojson['features']:
            #     self._add_municipal_boundaries_to_map(
            #         m, municipal_geojson, polos_df)
            # else:
            st.warning("Usando representação simplificada dos municípios.")
            self._add_municipal_coverage_layers(m, polos_df, municipios_df)

            # Adicionar polos
            if not polos_df.empty:
                self._add_polos_to_coverage_map(m, polos_df)

            # Adicionar controle de camadas
            folium.LayerControl().add_to(m)

            # Adicionar legenda
            self._add_coverage_legend(m)

        except Exception as e:
            st.error(f"Erro ao criar mapa com delimitações: {str(e)}")
            # Fallback para método anterior
            return self.create_coverage_map(polos_df, municipios_df, map_config)

        return m

    def _add_municipal_boundaries_to_map(self, m, geojson_data, polos_df):
        """Adiciona delimitações municipais reais ao mapa"""

        # Identificar municípios com polos
        municipios_com_polos = set()
        if not polos_df.empty and 'CIDADE' in polos_df.columns:
            municipios_com_polos = set(
                polos_df['CIDADE'].dropna().str.upper().str.strip())

        def style_function(feature):
            """Define o estilo de cada município baseado na cobertura"""
            municipio_nome = feature['properties'].get(
                'name', '').upper().strip()
            distancia = feature['properties'].get('distancia_km', 999)

            # Determinar cor
            if municipio_nome in municipios_com_polos:
                color = '#8B4513'  # Marrom para municípios com polo
                opacity = 0.8
            elif distancia <= 100:
                color = '#4169E1'  # Azul para cobertura
                opacity = 0.6
            else:
                color = '#808080'  # Cinza para fora da cobertura
                opacity = 0.4

            return {
                'fillColor': color,
                'color': 'white',
                'weight': 1,
                'fillOpacity': opacity,
                'opacity': 1
            }

        def highlight_function(feature):
            """Destaque ao passar o mouse"""
            return {
                'fillColor': '#ffff00',
                'color': 'black',
                'weight': 3,
                'fillOpacity': 0.9,
                'opacity': 1
            }

        # Adicionar camada GeoJSON
        folium.GeoJson(
            geojson_data,
            style_function=style_function,
            highlight_function=highlight_function,
            popup=folium.GeoJsonPopup(
                fields=['name', 'uf', 'total_alunos',
                        'distancia_km', 'polo_proximo'],
                aliases=['Município:', 'UF:', 'Total Alunos:',
                         'Distância (km):', 'Polo Próximo:'],
                localize=True,
                labels=True,
                style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;"
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=['name', 'uf'],
                aliases=['Município:'],
                style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;"
            )
        ).add_to(m)

    # Método alternativo usando dados reais do IBGE (mais avançado)
    def create_municipal_coverage_map_ibge(
            self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame,
            map_config: Dict) -> folium.Map:
        """Versão avançada usando dados reais do IBGE"""

        m = folium.Map(
            location=[map_config['center_lat'], map_config['center_lon']],
            zoom_start=map_config['zoom'],
            tiles='OpenStreetMap'
        )

        try:
            # Obter estados únicos dos dados
            estados = municipios_df['UF'].dropna().unique()

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uf in enumerate(estados):
                status_text.text(f'Carregando delimitações de {uf}...')

                # REMOVIDO: Uso de GeoDataLoader direto.
                # geo_data = GeoDataLoader.load_municipal_boundaries_by_state(uf)
                geo_data = None  # Placeholder

                if geo_data:
                    # Filtrar municípios do estado atual
                    municipios_uf = municipios_df[municipios_df['UF'] == uf]

                    # Adicionar dados de cobertura ao GeoJSON
                    self._enhance_geojson_with_coverage_data(
                        geo_data, municipios_uf, polos_df)

                    # Adicionar ao mapa
                    self._add_state_boundaries_to_map(m, geo_data, uf)

                progress_bar.progress((i + 1) / len(estados))

            progress_bar.empty()
            status_text.empty()

            # Adicionar polos
            if not polos_df.empty:
                self._add_polos_to_coverage_map(m, polos_df)

            # Adicionar controle de camadas
            folium.LayerControl().add_to(m)

            # Adicionar legenda
            self._add_coverage_legend(m)

        except Exception as e:
            st.error(f"Erro ao carregar dados do IBGE: {str(e)}")
            # Fallback
            return self.create_municipal_coverage_map_with_boundaries(polos_df, municipios_df, map_config)

        return m

    def _enhance_geojson_with_coverage_data(self, geo_data, municipios_df, polos_df):
        """Adiciona dados de cobertura ao GeoJSON do IBGE"""

        # Criar dicionário de lookup para os dados
        municipios_dict = {}
        for _, municipio in municipios_df.iterrows():
            nome = municipio.get('MUNICIPIO_IBGE', '').upper().strip()
            municipios_dict[nome] = {
                'total_alunos': municipio.get('TOTAL_ALUNOS', 0),
                'distancia_km': municipio.get('DISTANCIA_KM', 999),
                'polo_proximo': municipio.get('UNIDADE_POLO', 'N/A')
            }

        # Municípios com polos
        municipios_com_polos = set()
        if not polos_df.empty and 'CIDADE' in polos_df.columns:
            municipios_com_polos = set(
                polos_df['CIDADE'].dropna().str.upper().str.strip())

        # Atualizar features do GeoJSON
        for feature in geo_data.get('features', []):
            nome_municipio = feature.get('properties', {}).get(
                'name', '').upper().strip()

            # Adicionar dados de cobertura
            if nome_municipio in municipios_dict:
                feature['properties'].update(municipios_dict[nome_municipio])
            else:
                feature['properties'].update({
                    'total_alunos': 0,
                    'distancia_km': 999,
                    'polo_proximo': 'N/A'
                })

            # Adicionar flag de polo
            feature['properties']['tem_polo'] = nome_municipio in municipios_com_polos

    def _add_state_boundaries_to_map(self, m, geo_data, uf):
        """Adiciona delimitações de um estado ao mapa"""

        def style_function(feature):
            """Define estilo baseado na cobertura"""
            tem_polo = feature['properties'].get('tem_polo', False)
            distancia = feature['properties'].get('distancia_km', 999)

            if tem_polo:
                return {
                    'fillColor': '#8B4513',  # Marrom
                    'color': 'white',
                    'weight': 1,
                    'fillOpacity': 0.8,
                    'opacity': 1
                }
            elif distancia <= 100:
                return {
                    'fillColor': '#4169E1',  # Azul
                    'color': 'white',
                    'weight': 1,
                    'fillOpacity': 0.6,
                    'opacity': 1
                }
            else:
                return {
                    'fillColor': '#808080',  # Cinza
                    'color': 'white',
                    'weight': 1,
                    'fillOpacity': 0.4,
                    'opacity': 1
                }

        # Adicionar camada com nome do estado
        folium.GeoJson(
            geo_data,
            style_function=style_function,
            popup=folium.GeoJsonPopup(
                fields=['name', 'total_alunos',
                        'distancia_km', 'polo_proximo'],
                aliases=['Município:', 'Total Alunos:',
                         'Distância (km):', 'Polo Próximo:'],
                localize=True,
                labels=True,
                style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;"
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=['name'],
                aliases=['Município:'],
                style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;"
            ),
            name=f'Municípios - {uf}'
        ).add_to(m)

    def _add_municipal_coverage_layers(self, m, polos_df, municipios_df):
        """Adiciona camadas de municípios coloridos por cobertura"""

        # Identificar municípios com polos
        municipios_com_polos = set()
        if not polos_df.empty and 'CIDADE' in polos_df.columns:
            municipios_com_polos = set(polos_df['CIDADE'].dropna().str.upper())

        # Processar cada município
        for _, municipio in municipios_df.iterrows():
            try:
                lat_val = municipio.get('LAT', None)
                lng_val = municipio.get('LNG', None)

                if pd.notna(lat_val) and pd.notna(lng_val):
                    lat_float = float(lat_val)
                    lng_float = float(lng_val)

                    # Determinar cor baseada no tipo de cobertura
                    cor, tipo_cobertura = self._determine_municipality_color(
                        municipio, municipios_com_polos
                    )

                    # Criar marcador circular para representar o município
                    folium.CircleMarker(
                        location=[lat_float, lng_float],
                        radius=8,
                        popup=self._create_municipality_popup(
                            municipio, tipo_cobertura),
                        tooltip=f"{municipio.get(
                            'MUNICIPIO_IBGE', 'N/A')} - {tipo_cobertura}",
                        color='white',
                        weight=2,
                        fillColor=cor,
                        fillOpacity=0.8
                    ).add_to(m)

            except Exception as e:
                continue

    def _determine_municipality_color(self, municipio, municipios_com_polos):
        """Determina a cor do município baseado no tipo de cobertura"""

        municipio_nome = str(municipio.get('MUNICIPIO_IBGE', '')).upper()
        distancia = municipio.get('DISTANCIA_KM', 999)

        # Verificar se tem polo
        if municipio_nome in municipios_com_polos:
            return '#8B4513', 'Município com Polo'  # Roxo/Marrom

        # Verificar se está na cobertura (100km)
        try:
            dist_float = float(distancia) if pd.notna(distancia) else 999
            if dist_float <= 100:
                return '#4169E1', 'Cobertura 100km'  # Azul
            else:
                return '#808080', 'Fora da Cobertura'  # Cinza
        except:
            return '#808080', 'Fora da Cobertura'  # Cinza

    def _create_municipality_popup(self, municipio, tipo_cobertura):
        """Cria popup informativo para o município"""

        municipio_nome = municipio.get('MUNICIPIO_IBGE', 'N/A')
        uf = municipio.get('UF', 'N/A')
        distancia = municipio.get('DISTANCIA_KM', 'N/A')
        total_alunos = municipio.get('TOTAL_ALUNOS', 0)
        polo_proximo = municipio.get('UNIDADE_POLO', 'N/A')

        # Formatar distância
        if pd.notna(distancia) and distancia != 'N/A':
            try:
                dist_str = f"{float(distancia):.1f} km"
            except:
                dist_str = "N/A"
        else:
            dist_str = "N/A"

        popup_html = f"""
        <div style="width: 250px;">
            <h4 style="margin-bottom: 10px; color: #2c3e50;">
                <b>{municipio_nome}</b>
            </h4>
            <hr style="margin: 5px 0;">
            <p style="margin: 5px 0;"><b>Estado:</b> {uf}</p>
            <p style="margin: 5px 0;"><b>Tipo:</b> {tipo_cobertura}</p>
            <p style="margin: 5px 0;"><b>Distância do Polo:</b> {dist_str}</p>
            <p style="margin: 5px 0;"><b>Total de Alunos:</b> {
            total_alunos}</p>
            <p style="margin: 5px 0;"><b>Polo Mais Próximo:</b> {
            polo_proximo}</p>
        </div>
        """

        return popup_html

    def _add_polos_to_coverage_map(self, m, polos_df):
        """Adiciona marcadores dos polos ao mapa de cobertura"""

        for _, polo in polos_df.iterrows():
            try:
                lat_val = polo.get('lat', None)
                lng_val = polo.get('long', None)

                if pd.notna(lat_val) and pd.notna(lng_val):
                    lat_float = float(lat_val)
                    lng_float = float(lng_val)

                    # Marcador do polo
                    folium.Marker(
                        location=[lat_float, lng_float],
                        popup=f"""
                        <div style="width: 200px;">
                            <h4 style="color: #c0392b;"><b>🎓 {
                            polo.get('UNIDADE', 'N/A')}</b></h4>
                            <hr>
                            <p><b>Cidade:</b> {
                            polo.get('CIDADE', 'N/A')}</p>
                            <p><b>UF:</b> {
                            polo.get('UF', 'N/A')}</p>
                            <p><b>Endereço:</b> {
                            polo.get('ENDERECO', 'N/A')}</p>
                        </div>
                        """,
                        tooltip=f"🎓 {polo.get('UNIDADE', 'N/A')}",
                        icon=folium.Icon(
                            color='red',
                            icon='graduation-cap',
                            prefix='fa'
                        )
                    ).add_to(m)

                    # Círculo de cobertura (100km) - opcional, mais sutil
                    folium.Circle(
                        location=[lat_float, lng_float],
                        radius=100000,  # 100km em metros
                        color='red',
                        fillColor='red',
                        fillOpacity=0.05,
                        weight=1,
                        opacity=0.3
                    ).add_to(m)

            except Exception as e:
                continue

    def _add_coverage_legend(self, m):
        """Adiciona legenda ao mapa de cobertura"""

        legend_html = '''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 220px; height: 250px;
                    background-color: white;
                    border:2px solid grey; z-index:9999;
                    font-size:12px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.2);">

        <h4 style="margin-top: 0; margin-bottom: 10px; color: black;">
            📍 Legenda de Cobertura
        </h4>

        <div style="margin: 5px 0;">
            <span style="color: #8B4513; font-size: 16px;">●</span>
            <span style="margin-left: 5px;">Município com Polo</span>
        </div>

        <div style="margin: 5px 0;">
            <span style="color: #4169E1; font-size: 16px;">●</span>
            <span style="margin-left: 5px;">Cobertura 100km</span>
        </div>

        <div style="margin: 5px 0;">
            <span style="color: #808080; font-size: 16px;">●</span>
            <span style="margin-left: 5px;">Fora da Cobertura</span>
        </div>

        <div style="margin: 5px 0;">
            <span style="color: #c0392b; font-size: 16px;">📍</span>
            <span style="margin-left: 5px;">Localização do Polo</span>
        </div>

        </div>
        '''

        m.get_root().html.add_child(folium.Element(legend_html))

    def create_coverage_map(
        self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame,
            map_config: Dict) -> folium.Map:
        """Cria mapa de cobertura com raios de 100km"""
        m = folium.Map(
            location=[map_config['center_lat'], map_config['center_lon']],
            zoom_start=map_config['zoom']
        )

        # Adicionar polos com raios de cobertura
        if not polos_df.empty:
            for _, polo in polos_df.iterrows():
                try:
                    lat_val = polo.get('lat', None)
                    lng_val = polo.get('long', None)

                    if pd.notna(lat_val) and pd.notna(lng_val):
                        lat_float = float(lat_val)
                        lng_float = float(lng_val)

                        # Marcador do polo
                        folium.Marker(
                            location=[lat_float, lng_float],
                            popup=f"<b>{polo.get('UNIDADE', 'N/A')}</b>",
                            icon=folium.Icon(
                                color='red',
                                icon='graduation-cap',
                                prefix='fa')
                        ).add_to(m)

                        # Círculo de cobertura (100km)
                        folium.Circle(
                            location=[lat_float, lng_float],
                            radius=100000,  # 100km em metros
                            color='blue',
                            fillColor='lightblue',
                            fillOpacity=0.1,
                            weight=2
                        ).add_to(m)
                except:
                    continue

        # Adicionar municípios coloridos por cobertura
        if not municipios_df.empty:
            for _, municipio in municipios_df.iterrows():
                try:
                    lat_val = municipio.get('LAT', None)
                    lng_val = municipio.get('LNG', None)
                    dist_val = municipio.get('DISTANCIA_KM', 0)

                    if pd.notna(lat_val) and pd.notna(lng_val):
                        lat_float = float(lat_val)
                        lng_float = float(lng_val)

                        # Verificar distância de forma segura
                        try:
                            dist_float = float(dist_val) if pd.notna(
                                dist_val) else 999
                        except:
                            dist_float = 999

                        color = 'green' if dist_float <= 100 else 'orange'

                        folium.CircleMarker(
                            location=[lat_float, lng_float],
                            radius=3,
                            popup=f"""
                            <b>{municipio.get('MUNICIPIO_IBGE', 'N/A')}</b><br>
                            UF: {municipio.get('UF', 'N/A')}<br>
                            Distância: {dist_float:.1f} km<br>
                            Alunos: {municipio.get('TOTAL_ALUNOS', 0)}
                            """,
                            color=color,
                            fillColor=color,
                            fillOpacity=0.7
                        ).add_to(m)
                except:
                    continue

        return m

    def create_polos_by_state_chart(self, polos_df: pd.DataFrame) -> go.Figure:
        """Gráfico de barras: Polos por Estado"""
        if polos_df.empty or 'UF' not in polos_df.columns:
            return go.Figure()

        try:
            polos_por_uf = polos_df['UF'].value_counts().reset_index()
            polos_por_uf.columns = ['UF', 'Quantidade']

            fig = px.bar(
                polos_por_uf,
                x='UF',
                y='Quantidade',
                title='Distribuição de Polos por Estado',
                color='Quantidade',
                color_continuous_scale='Blues'
            )

            fig.update_layout(
                xaxis_title='Estado (UF)',
                yaxis_title='Número de Polos',
                showlegend=False
            )

            return fig
        except:
            return go.Figure()

    def create_polos_by_region_pie(self, polos_df: pd.DataFrame) -> go.Figure:
        """Gráfico de pizza: Distribuição por região"""
        if polos_df.empty or 'REGIAO' not in polos_df.columns:
            return go.Figure()

        try:
            polos_por_regiao = polos_df['REGIAO'].value_counts()

            fig = px.pie(
                values=polos_por_regiao.values,
                names=polos_por_regiao.index,
                title='Distribuição de Polos por Região'
            )

            return fig
        except:
            return go.Figure()

    def create_top_cities_chart(
            self, municipios_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Gráfico de barras: Top cidades com mais alunos"""
        if municipios_df.empty or 'TOTAL_ALUNOS' not in municipios_df.columns:
            return go.Figure()

        try:
            top_cidades = municipios_df.nlargest(top_n, 'TOTAL_ALUNOS')

            fig = px.bar(
                top_cidades,
                x='TOTAL_ALUNOS',
                y='MUNICIPIO_IBGE',
                orientation='h',
                title=f'Top {top_n} Municípios com Mais Alunos',
                color='TOTAL_ALUNOS',
                color_continuous_scale='Viridis'
            )

            fig.update_layout(
                xaxis_title='Número de Alunos',
                yaxis_title='Município',
                yaxis={'categoryorder': 'total ascending'}
            )

            return fig
        except:
            return go.Figure()

    def create_distance_vs_students_scatter(
            self, municipios_df: pd.DataFrame) -> go.Figure:
        """Scatter plot: Distância vs Número de Alunos"""
        if municipios_df.empty:
            return go.Figure()

        try:
            required_cols = ['DISTANCIA_KM', 'TOTAL_ALUNOS',
                             'REGIAO', 'MUNICIPIO_IBGE', 'UF']
            if not all(col in municipios_df.columns for col in required_cols):
                return go.Figure()

            fig = px.scatter(
                municipios_df,
                x='DISTANCIA_KM',
                y='TOTAL_ALUNOS',
                color='REGIAO',
                size='TOTAL_ALUNOS',
                hover_data=['MUNICIPIO_IBGE', 'UF'],
                title='Relação entre Distância do Polo e Número de Alunos'
            )

            fig.update_layout(
                xaxis_title='Distância do Polo (km)',
                yaxis_title='Número de Alunos'
            )

            return fig
        except:
            return go.Figure()

    def create_distance_boxplot(
            self, municipios_df: pd.DataFrame) -> go.Figure:
        """Boxplot: Distribuição de distâncias por UF"""
        if municipios_df.empty or 'DISTANCIA_KM' not in municipios_df.columns or 'UF' not in municipios_df.columns:
            return go.Figure()

        try:
            fig = px.box(
                municipios_df,
                x='UF',
                y='DISTANCIA_KM',
                title='Distribuição de Distâncias por Estado'
            )

            fig.update_layout(
                xaxis_title='Estado (UF)',
                yaxis_title='Distância (km)',
                xaxis={'categoryorder': 'total descending'}
            )

            return fig
        except:
            return go.Figure()

    def create_correlation_heatmap(
            self, municipios_df: pd.DataFrame) -> go.Figure:
        """Heatmap de correlação"""
        if municipios_df.empty:
            return go.Figure()

        try:
            # Selecionar apenas colunas numéricas
            numeric_cols = ['LAT', 'LNG', 'DISTANCIA_KM', 'TOTAL_ALUNOS']
            available_cols = [
                col for col in numeric_cols if col in municipios_df.columns]

            if len(available_cols) < 2:
                return go.Figure()

            corr_matrix = municipios_df[available_cols].corr()

            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title='Matriz de Correlação - Variáveis Numéricas',
                color_continuous_scale='RdBu'
            )

            return fig
        except:
            return go.Figure()

    def create_students_by_course_chart(
            self, alunos_df: pd.DataFrame) -> go.Figure:
        """Gráfico de barras: Distribuição de alunos por curso"""
        if alunos_df.empty or 'CURSO' not in alunos_df.columns:
            return go.Figure()

        try:
            cursos_count = alunos_df['CURSO'].value_counts().head(15)

            fig = px.bar(
                x=cursos_count.values,
                y=cursos_count.index,
                orientation='h',
                title='Top 15 Cursos Mais Demandados',
                color=cursos_count.values,
                color_continuous_scale='Plasma'
            )

            fig.update_layout(
                xaxis_title='Número de Alunos',
                yaxis_title='Curso',
                yaxis={'categoryorder': 'total ascending'}
            )

            return fig
        except:
            return go.Figure()

    def create_alignment_analysis(self, alunos_df: pd.DataFrame) -> go.Figure:
        """Análise de alinhamento polo atual vs ideal"""
        if alunos_df.empty or 'POLO' not in alunos_df.columns or 'POLO_MAIS_PROXIMO' not in alunos_df.columns:
            return go.Figure()

        try:
            # Calcular alinhamento
            alunos_df['ALINHADO'] = alunos_df['POLO'] == alunos_df[
                'POLO_MAIS_PROXIMO']
            alignment_counts = alunos_df['ALINHADO'].value_counts()

            fig = px.pie(
                values=alignment_counts.values,
                names=[
                    'Desalinhado' if not x else 'Alinhado' for x in alignment_counts.index],
                title='Alinhamento: Polo Atual vs Polo Ideal',
                color_discrete_map={'Alinhado': 'green', 'Desalinhado': 'red'}
            )

            return fig
        except:
            return go.Figure()

    def create_sankey_diagram(self, alunos_df: pd.DataFrame) -> go.Figure:
        """Diagrama Sankey para fluxo de realocação"""
        if alunos_df.empty or 'POLO' not in alunos_df.columns or 'POLO_MAIS_PROXIMO' not in alunos_df.columns:
            return go.Figure()

        try:
            # Filtrar apenas alunos desalinhados
            desalinhados = alunos_df[alunos_df['POLO']
                                     != alunos_df['POLO_MAIS_PROXIMO']]

            if desalinhados.empty:
                return go.Figure()

            # Contar fluxos
            fluxos = desalinhados.groupby(
                ['POLO', 'POLO_MAIS_PROXIMO']).size().reset_index(name='count')

            # Preparar dados para Sankey
            all_polos = list(
                set(fluxos['POLO'].tolist() + fluxos[
                    'POLO_MAIS_PROXIMO'].tolist()))
            polo_to_idx = {polo: idx for idx, polo in enumerate(all_polos)}

            source = [polo_to_idx[polo] for polo in fluxos['POLO']]
            target = [polo_to_idx[polo]
                      for polo in fluxos['POLO_MAIS_PROXIMO']]
            value = fluxos['count'].tolist()

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_polos,
                    color="blue"
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value
                )
            )])

            fig.update_layout(
                title_text="Fluxo de Realocação de Alunos", font_size=10)

            return fig
        except:
            return go.Figure()

    def create_students_vs_polos_comparison(
            self, municipios_df: pd.DataFrame, polos_df: pd.DataFrame,
            filter_type: str = "UF", filter_value: str = "Todos") -> go.Figure:
        """Cria gráfico mesclado comparativo de alunos vs polos por filtro"""

        if municipios_df.empty or polos_df.empty:
            return go.Figure()

        try:
            # Filtrar dados baseado no filtro selecionado
            if filter_value != "Todos":
                if filter_type == "UF":
                    municipios_filtered = municipios_df[municipios_df['UF']
                                                        == filter_value]
                    polos_filtered = polos_df[polos_df['UF'] == filter_value]
                else:  # REGIAO
                    municipios_filtered = municipios_df[municipios_df['REGIAO']
                                                        == filter_value]
                    polos_filtered = polos_df[polos_df['REGIAO']
                                              == filter_value]
            else:
                municipios_filtered = municipios_df.copy()
                polos_filtered = polos_df.copy()

            if municipios_filtered.empty or polos_filtered.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado encontrado para o filtro selecionado",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            # Agrupar dados por UF ou REGIAO
            group_col = filter_type if filter_type in [
                'UF', 'REGIAO'] else 'UF'

            # Calcular total de alunos por grupo
            alunos_por_grupo = municipios_filtered.groupby(
                group_col)['TOTAL_ALUNOS'].sum().reset_index()
            alunos_por_grupo = alunos_por_grupo[alunos_por_grupo['TOTAL_ALUNOS'] > 0]

            # Calcular total de polos por grupo
            polos_por_grupo = polos_filtered.groupby(
                group_col).size().reset_index(name='TOTAL_POLOS')

            # Merge dos dados
            dados_comparacao = pd.merge(
                alunos_por_grupo, polos_por_grupo, on=group_col, how='outer').fillna(0)

            if dados_comparacao.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado para comparação",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            # Ordenar por total de alunos
            dados_comparacao = dados_comparacao.sort_values(
                'TOTAL_ALUNOS', ascending=True)

            # Calcular eficiência (alunos por polo)
            dados_comparacao['EFICIENCIA'] = dados_comparacao.apply(
                lambda row: row['TOTAL_ALUNOS'] /
                row['TOTAL_POLOS'] if row['TOTAL_POLOS'] > 0 else 0,
                axis=1
            )

            # Criar subplot com eixos Y secundários
            fig = make_subplots(
                specs=[[{"secondary_y": True}]],
                subplot_titles=[
                    f"Comparativo Alunos vs Polos {f'- {filter_value}' if filter_value != 'Todos' else ''}"]
            )

            # Gráfico de barras para número de alunos (eixo Y primário)
            fig.add_trace(
                go.Bar(
                    x=dados_comparacao[group_col],
                    y=dados_comparacao['TOTAL_ALUNOS'],
                    name='Total de Alunos',
                    marker_color='rgba(65, 105, 225, 0.8)',  # Azul
                    text=dados_comparacao['TOTAL_ALUNOS'],
                    textposition='outside',
                    texttemplate='%{text:,.0f}',
                    hovertemplate='<b>%{x}</b><br>Alunos: %{y:,.0f}<extra></extra>'
                ),
                secondary_y=False
            )

            # Gráfico de linha para número de polos (eixo Y secundário)
            fig.add_trace(
                go.Scatter(
                    x=dados_comparacao[group_col],
                    y=dados_comparacao['TOTAL_POLOS'],
                    mode='lines+markers+text',
                    name='Total de Polos',
                    line=dict(color='rgba(255, 99, 71, 1)',
                              width=3),  # Vermelho
                    marker=dict(size=10, color='rgba(255, 99, 71, 1)'),
                    text=dados_comparacao['TOTAL_POLOS'],
                    textposition='top center',
                    texttemplate='%{text:.0f}',
                    hovertemplate='<b>%{x}</b><br>Polos: %{y:.0f}<extra></extra>'
                ),
                secondary_y=True
            )

            # Gráfico de linha para eficiência (alunos por polo)
            fig.add_trace(
                go.Scatter(
                    x=dados_comparacao[group_col],
                    y=dados_comparacao['EFICIENCIA'],
                    mode='lines+markers',
                    name='Alunos por Polo',
                    line=dict(color='rgba(50, 205, 50, 1)',
                              width=2, dash='dash'),  # Verde
                    marker=dict(size=8, color='rgba(50, 205, 50, 1)'),
                    hovertemplate='<b>%{x}</b><br>Eficiência: %{y:.1f} alunos/polo<extra></extra>'
                ),
                secondary_y=True
            )

            # Configurar eixos
            fig.update_xaxes(
                title_text=f"{group_col}",
                tickangle=45 if len(dados_comparacao) > 8 else 0
            )

            fig.update_yaxes(
                title_text="<b>Número de Alunos</b>",
                secondary_y=False,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            )

            fig.update_yaxes(
                title_text="<b>Número de Polos / Eficiência</b>",
                secondary_y=True,
                showgrid=False
            )

            # Layout geral
            fig.update_layout(
                title={
                    'text': f"<b>Análise Comparativa: Alunos vs Polos vs Eficiência</b>",
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                ),
                height=500,
                margin=dict(t=80, b=50, l=50, r=50)
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_efficiency_analysis_chart(
            self, municipios_df: pd.DataFrame, polos_df: pd.DataFrame,
            filter_type: str = "UF") -> go.Figure:
        """Cria gráfico de análise de eficiência detalhada"""

        if municipios_df.empty or polos_df.empty:
            return go.Figure()

        try:
            # Agrupar dados
            group_col = filter_type

            # Calcular métricas por grupo
            alunos_stats = municipios_df.groupby(group_col).agg({
                'TOTAL_ALUNOS': ['sum', 'mean', 'count'],
                'DISTANCIA_KM': 'mean'
            }).round(2)

            alunos_stats.columns = [
                'Total_Alunos', 'Media_Alunos_Municipio', 'Num_Municipios', 'Distancia_Media']
            alunos_stats = alunos_stats.reset_index()

            polos_stats = polos_df.groupby(
                group_col).size().reset_index(name='Total_Polos')

            # Merge
            efficiency_data = pd.merge(
                alunos_stats, polos_stats, on=group_col, how='outer').fillna(0)

            # Calcular eficiências
            efficiency_data['Alunos_por_Polo'] = efficiency_data.apply(
                lambda row: row['Total_Alunos'] /
                row['Total_Polos'] if row['Total_Polos'] > 0 else 0,
                axis=1
            )

            efficiency_data['Municipios_por_Polo'] = efficiency_data.apply(
                lambda row: row['Num_Municipios'] /
                row['Total_Polos'] if row['Total_Polos'] > 0 else 0,
                axis=1
            )

            # Filtrar dados válidos
            efficiency_data = efficiency_data[efficiency_data['Total_Alunos'] > 0]
            efficiency_data = efficiency_data.sort_values(
                'Alunos_por_Polo', ascending=False)

            # Criar gráfico de barras horizontal
            fig = go.Figure()

            fig.add_trace(go.Bar(
                y=efficiency_data[group_col],
                x=efficiency_data['Alunos_por_Polo'],
                orientation='h',
                name='Alunos por Polo',
                marker_color='rgba(65, 105, 225, 0.8)',
                text=efficiency_data['Alunos_por_Polo'].round(1),
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                            'Alunos por Polo: %{x:.1f}<br>' +
                            'Total Alunos: %{customdata[0]:,.0f}<br>' +
                            'Total Polos: %{customdata[1]:.0f}<br>' +
                            'Distância Média: %{customdata[2]:.1f} km<extra></extra>',
                customdata=efficiency_data[[
                    'Total_Alunos', 'Total_Polos', 'Distancia_Media']].values
            ))

            fig.update_layout(
                title={
                    'text': f"<b>Eficiência por {group_col}: Alunos por Polo</b>",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="Alunos por Polo",
                yaxis_title=group_col,
                height=max(400, len(efficiency_data) * 30),
                margin=dict(l=100, r=50, t=60, b=50)
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar análise de eficiência: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_courses_by_region_chart(self, alunos_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Cria gráfico de cursos mais demandados por região"""

        if alunos_df.empty or 'CURSO' not in alunos_df.columns or 'REGIAO' not in alunos_df.columns:
            return go.Figure().add_annotation(
                text="Dados de cursos ou regiões não disponíveis",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )

        try:
            # Filtrar dados válidos
            dados_validos = alunos_df.dropna(subset=['CURSO', 'REGIAO'])

            if dados_validos.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado válido encontrado",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            # Agrupar por região e curso
            cursos_por_regiao = dados_validos.groupby(
                ['REGIAO', 'CURSO']).size().reset_index(name='Total_Alunos')

            # Obter top cursos por região
            top_cursos_regiao = []

            for regiao in cursos_por_regiao['REGIAO'].unique():
                regiao_data = cursos_por_regiao[cursos_por_regiao['REGIAO'] == regiao]
                top_regiao = regiao_data.nlargest(top_n, 'Total_Alunos')
                top_cursos_regiao.append(top_regiao)

            # Concatenar todos os dados
            dados_finais = pd.concat(dados_finais, ignore_index=True)

            if dados_finais.empty:
                return go.Figure().add_annotation(
                    text="Nenhum curso encontrado",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            # Criar gráfico de barras agrupadas
            fig = px.bar(
                dados_finais,
                x='REGIAO',
                y='Total_Alunos',
                color='CURSO',
                title=f'Top {top_n} Cursos Mais Demandados por Região',
                labels={
                    'Total_Alunos': 'Número de Alunos',
                    'REGIAO': 'Região',
                    'CURSO': 'Curso'
                },
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig.update_layout(
                xaxis_title='Região',
                yaxis_title='Número de Alunos',
                legend_title='Cursos',
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(r=200)  # Espaço para a legenda
            )

            # Adicionar valores nas barras
            fig.update_traces(
                texttemplate='%{y}',
                textposition='outside'
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_courses_by_region_heatmap(self, alunos_df: pd.DataFrame, top_courses: int = 15) -> go.Figure:
        """Cria heatmap de cursos por região"""

        if alunos_df.empty or 'CURSO' not in alunos_df.columns or 'REGIAO' not in alunos_df.columns:
            return go.Figure()

        try:
            # Filtrar dados válidos
            dados_validos = alunos_df.dropna(subset=['CURSO', 'REGIAO'])

            if dados_validos.empty:
                return go.Figure()

            # Obter top cursos gerais
            top_cursos_gerais = dados_validos['CURSO'].value_counts().head(
                top_courses).index.tolist()

            # Filtrar apenas os top cursos
            dados_filtrados = dados_validos[dados_validos['CURSO'].isin(
                top_cursos_gerais)]

            # Criar tabela cruzada
            heatmap_data = pd.crosstab(
                dados_filtrados['CURSO'], dados_filtrados['REGIAO'])

            # Ordenar por total de alunos
            heatmap_data['Total'] = heatmap_data.sum(axis=1)
            heatmap_data = heatmap_data.sort_values('Total', ascending=False)
            heatmap_data = heatmap_data.drop('Total', axis=1)

            # Criar heatmap
            fig = px.imshow(
                heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                color_continuous_scale='Viridis',
                title=f'Heatmap: Top {top_courses} Cursos por Região',
                labels=dict(x="Região", y="Curso", color="Número de Alunos")
            )

            # Adicionar valores nas células
            fig.update_traces(
                text=heatmap_data.values,
                texttemplate="%{text}",
                textfont={"size": 10}
            )

            fig.update_layout(
                height=max(400, len(heatmap_data) * 25),
                margin=dict(l=200, r=50, t=60, b=50)
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar heatmap: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_regional_course_summary(self, alunos_df: pd.DataFrame) -> pd.DataFrame:
        """Cria tabela resumo de cursos por região"""

        if alunos_df.empty or 'CURSO' not in alunos_df.columns or 'REGIAO' not in alunos_df.columns:
            return pd.DataFrame()

        try:
            # Filtrar dados válidos
            dados_validos = alunos_df.dropna(subset=['CURSO', 'REGIAO'])

            if dados_validos.empty:
                return pd.DataFrame()

            # Estatísticas por região
            resumo_regiao = dados_validos.groupby('REGIAO').agg({
                'CURSO': ['count', 'nunique'],
                'CPF': 'nunique' if 'CPF' in dados_validos.columns else 'count'
            }).round(2)

            resumo_regiao.columns = ['Total_Matriculas',
                                     'Cursos_Distintos', 'Alunos_Unicos']
            resumo_regiao = resumo_regiao.reset_index()

            # Calcular curso mais popular por região
            curso_popular = dados_validos.groupby(
                ['REGIAO', 'CURSO']).size().reset_index(name='count')
            curso_mais_popular = curso_popular.loc[curso_popular.groupby('REGIAO')[
                'count'].idxmax()]
            curso_mais_popular = curso_mais_popular[[
                'REGIAO', 'CURSO', 'count']]
            curso_mais_popular.columns = [
                'REGIAO', 'Curso_Mais_Popular', 'Alunos_Curso_Popular']

            # Merge dos dados
            resumo_final = pd.merge(
                resumo_regiao, curso_mais_popular, on='REGIAO', how='left')

            # Calcular média de alunos por curso
            resumo_final['Media_Alunos_por_Curso'] = (
                resumo_final['Total_Matriculas'] /
                resumo_final['Cursos_Distintos']
            ).round(1)

            # Ordenar por total de matrículas
            resumo_final = resumo_final.sort_values(
                'Total_Matriculas', ascending=False)

            return resumo_final

        except Exception as e:
            return pd.DataFrame()

    # Métodos para análise de vendas
    def create_sales_partnership_pie(self, vendas_df: pd.DataFrame, selected_partnerships: List[str] = None, custom_title: str = None) -> go.Figure:
        """Cria gráfico de pizza das vendas por tipo de parceria com título customizável"""

        if vendas_df.empty or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure()

        try:
            # Filtrar por parcerias selecionadas se especificado
            if selected_partnerships:
                vendas_filtered = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                    selected_partnerships)]
            else:
                vendas_filtered = vendas_df.copy()

            if vendas_filtered.empty:
                return go.Figure()

            # Contar vendas por tipo de parceria
            vendas_por_parceria = vendas_filtered['TIPO_PARCERIA'].value_counts(
            )

            # Calcular percentuais
            total_vendas = vendas_por_parceria.sum()
            percentuais = (vendas_por_parceria / total_vendas * 100).round(1)

            # Definir cores específicas para cada tipo de parceria (mantendo suas cores originais)
            cores_parceria = {
                'Parceiro Comercial': '#FF6B6B',      # Vermelho claro
                'Parceiro Polo': '#4ECDC4',           # Verde água
                'Comercial Interno': '#45B7D1',       # Azul
                # Cores adicionais caso apareçam novos tipos
                'Outros': '#96CEB4',                  # Verde claro
                'Indefinido': '#FFEAA7'               # Amarelo claro
            }

            # Aplicar cores baseadas nos tipos de parceria encontrados
            cores_aplicadas = []
            for parceria in vendas_por_parceria.index:
                if parceria in cores_parceria:
                    cores_aplicadas.append(cores_parceria[parceria])
                else:
                    # Usar cores padrão se o tipo não estiver mapeado
                    cores_default = ['#96CEB4', '#FFEAA7',
                                     '#DDA0DD', '#98FB98', '#F0E68C']
                    idx = len(cores_aplicadas) % len(cores_default)
                    cores_aplicadas.append(cores_default[idx])

            # Título dinâmico (usar custom_title se fornecido, senão usar o padrão)
            titulo = custom_title if custom_title else 'Distribuição de Vendas por Tipo de Parceria'

            # Criar gráfico de pizza
            fig = go.Figure(data=[go.Pie(
                labels=vendas_por_parceria.index,
                values=vendas_por_parceria.values,
                textinfo='label+percent+value',
                texttemplate='<b>%{label}</b><br>%{percent}<br>(%{value} vendas)',
                hovertemplate='<b>%{label}</b><br>' +
                            'Vendas: %{value:,}<br>' +
                            'Percentual: %{percent}<br>' +
                            'Total Geral: ' + f'{total_vendas:,} vendas<br>' +
                            '<extra></extra>',
                            marker=dict(
                                colors=cores_aplicadas,
                                line=dict(color='#FFFFFF', width=2)
                            ),
                            textfont=dict(size=12),
                            # Destacar a maior fatia puxando-a ligeiramente
                            pull=[0.05 if i == 0 else 0 for i in range(
                                len(vendas_por_parceria))]
                            )])

            fig.update_layout(
                title={
                    'text': f'<b>{titulo}</b>',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                    font=dict(size=11)
                ),
                margin=dict(t=60, b=50, l=20, r=150),
                # Adicionar anotação com total de vendas
                annotations=[
                    dict(
                        text=f'<b>Total: {total_vendas:,} vendas</b>',
                        x=0.5, y=-0.15,
                        xref='paper', yref='paper',
                        showarrow=False,
                        font=dict(size=14, color='#2C3E50'),
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='#BDC3C7',
                        borderwidth=1,
                        borderpad=4
                    )
                ]
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_sales_timeline_chart(self, vendas_df: pd.DataFrame, group_by: str = "modalidade",
                                    selected_filters: List[str] = None) -> go.Figure:
        """Cria gráfico de linha temporal das vendas"""

        if vendas_df.empty or 'MES_ANO' not in vendas_df.columns:
            return go.Figure()

        try:
            # Determinar coluna de agrupamento
            group_column = 'NIVEL' if group_by == "modalidade" else 'TIPO_PARCERIA'

            if group_column not in vendas_df.columns:
                return go.Figure()

            # Filtrar dados se especificado
            if selected_filters:
                vendas_filtered = vendas_df[vendas_df[group_column].isin(
                    selected_filters)]
            else:
                vendas_filtered = vendas_df.copy()

            if vendas_filtered.empty:
                return go.Figure()

            # Agrupar por mês e categoria
            vendas_timeline = vendas_filtered.groupby(
                ['MES_ANO', group_column]).size().reset_index(name='Vendas')

            # Criar gráfico de linha
            fig = px.line(
                vendas_timeline,
                x='MES_ANO',
                y='Vendas',
                color=group_column,
                title=f'Evolução das Vendas por {group_by.title()}',
                markers=True,
                line_shape='spline'
            )

            fig.update_layout(
                xaxis_title='Período (Mês/Ano)',
                yaxis_title='Número de Vendas',
                hovermode='x unified',
                legend_title=group_by.title(),
                height=500,
                xaxis=dict(tickangle=45)
            )

            # Personalizar hover
            fig.update_traces(
                hovertemplate='<b>%{fullData.name}</b><br>' +
                'Período: %{x}<br>' +
                'Vendas: %{y}<br>' +
                '<extra></extra>'
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_top_courses_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Cria gráfico dos top cursos por tipo de parceria"""

        if vendas_df.empty or 'CURSO' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure()

        try:
            # Agrupar por parceria e curso
            cursos_por_parceria = vendas_df.groupby(
                ['TIPO_PARCERIA', 'CURSO']).size().reset_index(name='Vendas')

            # Obter top cursos por parceria
            top_cursos_parceria = []

            for parceria in cursos_por_parceria['TIPO_PARCERIA'].unique():
                parceria_data = cursos_por_parceria[cursos_por_parceria['TIPO_PARCERIA'] == parceria]
                top_parceria = parceria_data.nlargest(top_n, 'Vendas')
                top_cursos_parceria.append(top_parceria)

            # Concatenar dados
            dados_finais = pd.concat(top_cursos_parceria, ignore_index=True)

            if dados_finais.empty:
                return go.Figure()

            # Criar gráfico de barras agrupadas
            fig = px.bar(
                dados_finais,
                x='TIPO_PARCERIA',
                y='Vendas',
                color='CURSO',
                title=f'Top {top_n} Cursos Mais Vendidos por Tipo de Parceria',
                text='Vendas'
            )

            fig.update_layout(
                xaxis_title='Tipo de Parceria',
                yaxis_title='Número de Vendas',
                legend_title='Cursos',
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(r=250)
            )

            fig.update_traces(textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_modalities_by_month_chart(self, vendas_df: pd.DataFrame) -> go.Figure:
        """Cria gráfico das modalidades mais vendidas por mês"""

        if vendas_df.empty or 'MES_NOME' not in vendas_df.columns or 'NIVEL' not in vendas_df.columns:
            return go.Figure()

        try:
            # Agrupar por mês e modalidade
            modalidades_mes = vendas_df.groupby(
                ['MES_NOME', 'NIVEL']).size().reset_index(name='Vendas')

            # Obter top modalidade por mês
            top_modalidades_mes = modalidades_mes.loc[modalidades_mes.groupby('MES_NOME')[
                'Vendas'].idxmax()]

            # Ordenar meses corretamente
            ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

            top_modalidades_mes['MES_NOME'] = pd.Categorical(
                top_modalidades_mes['MES_NOME'],
                categories=ordem_meses,
                ordered=True
            )

            top_modalidades_mes = top_modalidades_mes.sort_values('MES_NOME')

            # Criar gráfico de barras
            fig = px.bar(
                top_modalidades_mes,
                x='MES_NOME',
                y='Vendas',
                color='NIVEL',
                title='Modalidade Mais Vendida por Mês',
                text='Vendas',
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig.update_layout(
                xaxis_title='Mês',
                yaxis_title='Número de Vendas',
                legend_title='Modalidade',
                height=500,
                xaxis=dict(tickangle=45)
            )

            fig.update_traces(textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    # Top Modalidades por Tipo de Parceiro
    def create_top_modalities_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n_modalities: int = 5) -> go.Figure:
        """
        Cria um gráfico de barras facetado mostrando as top modalidades mais vendidas
        por tipo de parceiro.
        """
        if vendas_df.empty or 'NIVEL' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure().add_annotation(
                text="Dados de modalidades ou tipo de parceria não disponíveis para este gráfico.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )
        try:
            # Agrupar por tipo de parceria e modalidade
            modalidades_por_parceria = vendas_df.groupby(
                ['TIPO_PARCERIA', 'NIVEL']).size().reset_index(name='Vendas')

            # Obter top N modalidades para cada tipo de parceiro
            top_modalidades_por_parceria = []
            for parceria_type in modalidades_por_parceria['TIPO_PARCERIA'].unique():
                subset = modalidades_por_parceria[modalidades_por_parceria['TIPO_PARCERIA'] == parceria_type]
                top_n = subset.nlargest(top_n_modalities, 'Vendas')
                top_modalidades_por_parceria.append(top_n)

            if not top_modalidades_por_parceria:
                return go.Figure().add_annotation(
                    text="Nenhum dado encontrado para as modalidades por tipo de parceria.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            df_top_modalities_partners = pd.concat(
                top_modalidades_por_parceria, ignore_index=True)

            fig = px.bar(
                df_top_modalities_partners,
                x='Vendas',
                y='NIVEL',
                color='NIVEL',
                orientation='h',
                facet_col='TIPO_PARCERIA',
                facet_col_wrap=2,  # Número de colunas de facetas
                title=f'Top {top_n_modalities} Modalidades Mais Vendidas por Tipo de Parceiro',
                labels={'NIVEL': 'Modalidade', 'Vendas': 'Número de Vendas'},
                color_discrete_sequence=px.colors.qualitative.Pastel  # Usar uma paleta mais suave
            )

            fig.update_layout(
                # Ordenar modalidades dentro de cada faceta
                yaxis={'categoryorder': 'total ascending'},
                height=600,
                showlegend=False  # A cor representa a modalidade, mas pode ser redundante com o rótulo Y
            )
            fig.for_each_annotation(lambda a: a.update(
                text=a.text.split("=")[-1]))  # Limpa o título da faceta

            fig.update_traces(texttemplate='%{x}', textposition='outside')

            return fig
        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar o gráfico de top modalidades por tipo de parceiro: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    # Modalidades Vendidas Mês a Mês por Tipo de Parceiro
    def create_modalities_monthly_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n_modalities: int = 3) -> go.Figure:
        """
        Cria um gráfico de linhas facetado mostrando a evolução mensal das vendas
        das top N modalidades para cada tipo de parceiro.
        """
        if vendas_df.empty or 'MES_ANO' not in vendas_df.columns or 'NIVEL' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure().add_annotation(
                text="Dados temporais, de modalidades ou tipo de parceria não disponíveis para este gráfico.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )
        try:
            # 1. Calcular vendas por MES_ANO, TIPO_PARCERIA e NIVEL
            sales_data = vendas_df.groupby(
                ['MES_ANO', 'TIPO_PARCERIA', 'NIVEL']).size().reset_index(name='Vendas')

            # 2. Ordenar MES_ANO para que o gráfico de linha seja contínuo
            sales_data['MES_ANO_ORD'] = pd.to_datetime(sales_data['MES_ANO'])
            sales_data = sales_data.sort_values(
                ['TIPO_PARCERIA', 'MES_ANO_ORD'])

            # 3. Identificar as top N modalidades para cada TIPO_PARCERIA no período total para filtragem consistente
            top_modalities_overall = sales_data.groupby(['TIPO_PARCERIA', 'NIVEL'])[
                'Vendas'].sum().reset_index()
            top_modalities_filtered = []
            for parceria_type in top_modalities_overall['TIPO_PARCERIA'].unique():
                subset = top_modalities_overall[top_modalities_overall['TIPO_PARCERIA']
                                                == parceria_type]
                top_n = subset.nlargest(top_n_modalities, 'Vendas')[
                    'NIVEL'].tolist()
                top_modalities_filtered.extend(
                    [(parceria_type, mod) for mod in top_n])

            # Filtrar o DataFrame principal para incluir apenas as top modalidades identificadas
            # Cria uma tupla (TIPO_PARCERIA, NIVEL) para cada linha e verifica se está nas top_modalities_filtered
            sales_data['temp_key'] = list(
                zip(sales_data['TIPO_PARCERIA'], sales_data['NIVEL']))
            df_filtered_top_modalities = sales_data[sales_data['temp_key'].isin(
                top_modalities_filtered)].copy()
            df_filtered_top_modalities.drop(columns=['temp_key'], inplace=True)

            if df_filtered_top_modalities.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado suficiente encontrado para as top modalidades por tipo de parceiro mensalmente.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            fig = px.line(
                df_filtered_top_modalities,
                x='MES_ANO',
                y='Vendas',
                color='NIVEL',
                facet_col='TIPO_PARCERIA',
                facet_col_wrap=2,
                title=f'Evolução Mensal das Top {top_n_modalities} Modalidades por Tipo de Parceiro',
                labels={'MES_ANO': 'Mês/Ano',
                        'Vendas': 'Número de Vendas', 'NIVEL': 'Modalidade'},
                line_shape='spline',
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_layout(
                xaxis_title='Mês/Ano',
                yaxis_title='Número de Vendas',
                hovermode='x unified',
                height=700,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom",
                            y=1.02, xanchor="right", x=1),
                xaxis=dict(tickangle=45)
            )
            fig.for_each_annotation(lambda a: a.update(
                text=a.text.split("=")[-1]))  # Limpa o título da faceta

            return fig
        except Exception as e:
            st.error(
                f"Erro ao gerar o gráfico de evolução mensal das modalidades por parceiro: {str(e)}")
            return go.Figure().add_annotation(
                text=f"Erro ao gerar o gráfico de evolução mensal das modalidades por parceiro: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    # Métodos para análise de vendas
    def create_sales_partnership_pie(self, vendas_df: pd.DataFrame, selected_partnerships: List[str] = None) -> go.Figure:
        """Cria gráfico de pizza das vendas por tipo de parceria"""

        if vendas_df.empty or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure()

        try:
            # Filtrar por parcerias selecionadas se especificado
            if selected_partnerships:
                vendas_filtered = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                    selected_partnerships)]
            else:
                vendas_filtered = vendas_df.copy()

            if vendas_filtered.empty:
                return go.Figure()

            # Contar vendas por tipo de parceria
            vendas_por_parceria = vendas_filtered['TIPO_PARCERIA'].value_counts(
            )

            # Calcular percentuais
            total_vendas = vendas_por_parceria.sum()
            percentuais = (vendas_por_parceria / total_vendas * 100).round(1)

            # Criar gráfico de pizza
            fig = go.Figure(data=[go.Pie(
                labels=vendas_por_parceria.index,
                values=vendas_por_parceria.values,
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{percent}<br>(%{value} vendas)',
                hovertemplate='<b>%{label}</b><br>' +
                            'Vendas: %{value}<br>' +
                            'Percentual: %{percent}<br>' +
                            '<extra></extra>',
                            marker=dict(
                                colors=['#FF6B6B', '#4ECDC4',
                                        '#45B7D1', '#96CEB4', '#FFEAA7'],
                                line=dict(color='#FFFFFF', width=2)
                            )
                            )])

            fig.update_layout(
                title={
                    'text': '<b>Distribuição de Vendas por Tipo de Parceria</b>',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 16}
                },
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_sales_timeline_chart(self, vendas_df: pd.DataFrame, group_by: str = "modalidade",
                                    selected_filters: List[str] = None) -> go.Figure:
        """Cria gráfico de linha temporal das vendas"""

        if vendas_df.empty or 'MES_ANO' not in vendas_df.columns:
            return go.Figure()

        try:
            # Determinar coluna de agrupamento
            group_column = 'NIVEL' if group_by == "modalidade" else 'TIPO_PARCERIA'

            if group_column not in vendas_df.columns:
                return go.Figure()

            # Filtrar dados se especificado
            if selected_filters:
                vendas_filtered = vendas_df[vendas_df[group_column].isin(
                    selected_filters)]
            else:
                vendas_filtered = vendas_df.copy()

            if vendas_filtered.empty:
                return go.Figure()

            # Agrupar por mês e categoria
            vendas_timeline = vendas_filtered.groupby(
                ['MES_ANO', group_column]).size().reset_index(name='Vendas')

            # Criar gráfico de linha
            fig = px.line(
                vendas_timeline,
                x='MES_ANO',
                y='Vendas',
                color=group_column,
                title=f'Evolução das Vendas por {group_by.title()}',
                markers=True,
                line_shape='spline'
            )

            fig.update_layout(
                xaxis_title='Período (Mês/Ano)',
                yaxis_title='Número de Vendas',
                hovermode='x unified',
                legend_title=group_by.title(),
                height=500,
                xaxis=dict(tickangle=45)
            )

            # Personalizar hover
            fig.update_traces(
                hovertemplate='<b>%{fullData.name}</b><br>' +
                'Período: %{x}<br>' +
                'Vendas: %{y}<br>' +
                '<extra></extra>'
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_top_courses_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Cria gráfico dos top cursos por tipo de parceria"""

        if vendas_df.empty or 'CURSO' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure()

        try:
            # Agrupar por parceria e curso
            cursos_por_parceria = vendas_df.groupby(
                ['TIPO_PARCERIA', 'CURSO']).size().reset_index(name='Vendas')

            # Obter top cursos por parceria
            top_cursos_parceria = []

            for parceria in cursos_por_parceria['TIPO_PARCERIA'].unique():
                parceria_data = cursos_por_parceria[cursos_por_parceria['TIPO_PARCERIA'] == parceria]
                top_parceria = parceria_data.nlargest(top_n, 'Vendas')
                top_cursos_parceria.append(top_parceria)

            # Concatenar dados
            dados_finais = pd.concat(top_cursos_parceria, ignore_index=True)

            if dados_finais.empty:
                return go.Figure()

            # Criar gráfico de barras agrupadas
            fig = px.bar(
                dados_finais,
                x='TIPO_PARCERIA',
                y='Vendas',
                color='CURSO',
                title=f'Top {top_n} Cursos Mais Vendidos por Tipo de Parceria',
                text='Vendas'
            )

            fig.update_layout(
                xaxis_title='Tipo de Parceria',
                yaxis_title='Número de Vendas',
                legend_title='Cursos',
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                margin=dict(r=250)
            )

            fig.update_traces(textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_modalities_by_month_chart(self, vendas_df: pd.DataFrame) -> go.Figure:
        """Cria gráfico das modalidades mais vendidas por mês"""

        if vendas_df.empty or 'MES_NOME' not in vendas_df.columns or 'NIVEL' not in vendas_df.columns:
            return go.Figure()

        try:
            # Agrupar por mês e modalidade
            modalidades_mes = vendas_df.groupby(
                ['MES_NOME', 'NIVEL']).size().reset_index(name='Vendas')

            # Obter top modalidade por mês
            top_modalidades_mes = modalidades_mes.loc[modalidades_mes.groupby('MES_NOME')[
                'Vendas'].idxmax()]

            # Ordenar meses corretamente
            ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

            top_modalidades_mes['MES_NOME'] = pd.Categorical(
                top_modalidades_mes['MES_NOME'],
                categories=ordem_meses,
                ordered=True
            )

            top_modalidades_mes = top_modalidades_mes.sort_values('MES_NOME')

            # Criar gráfico de barras
            fig = px.bar(
                top_modalidades_mes,
                x='MES_NOME',
                y='Vendas',
                color='NIVEL',
                title='Modalidade Mais Vendida por Mês',
                text='Vendas',
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig.update_layout(
                xaxis_title='Mês',
                yaxis_title='Número de Vendas',
                legend_title='Modalidade',
                height=500,
                xaxis=dict(tickangle=45)
            )

            fig.update_traces(textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    # Top Modalidades por Tipo de Parceiro
    def create_top_modalities_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n_modalities: int = 5) -> go.Figure:
        """
        Cria um gráfico de barras facetado mostrando as top modalidades mais vendidas
        por tipo de parceiro.
        """
        if vendas_df.empty or 'NIVEL' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure().add_annotation(
                text="Dados de modalidades ou tipo de parceria não disponíveis para este gráfico.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )
        try:
            # Agrupar por tipo de parceria e modalidade
            modalidades_por_parceria = vendas_df.groupby(
                ['TIPO_PARCERIA', 'NIVEL']).size().reset_index(name='Vendas')

            # Obter top N modalidades para cada tipo de parceiro
            top_modalidades_por_parceria = []
            for parceria_type in modalidades_por_parceria['TIPO_PARCERIA'].unique():
                subset = modalidades_por_parceria[modalidades_por_parceria['TIPO_PARCERIA'] == parceria_type]
                top_n = subset.nlargest(top_n_modalities, 'Vendas')
                top_modalidades_por_parceria.append(top_n)

            if not top_modalidades_por_parceria:
                return go.Figure().add_annotation(
                    text="Nenhum dado encontrado para as modalidades por tipo de parceria.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            df_top_modalities_partners = pd.concat(
                top_modalidades_por_parceria, ignore_index=True)

            fig = px.bar(
                df_top_modalities_partners,
                x='Vendas',
                y='NIVEL',
                color='NIVEL',
                orientation='h',
                facet_col='TIPO_PARCERIA',
                facet_col_wrap=2,  # Número de colunas de facetas
                title=f'Top {top_n_modalities} Modalidades Mais Vendidas por Tipo de Parceiro',
                labels={'NIVEL': 'Modalidade', 'Vendas': 'Número de Vendas'},
                color_discrete_sequence=px.colors.qualitative.Pastel  # Usar uma paleta mais suave
            )

            fig.update_layout(
                # Ordenar modalidades dentro de cada faceta
                yaxis={'categoryorder': 'total ascending'},
                height=600,
                showlegend=False  # A cor representa a modalidade, mas pode ser redundante com o rótulo Y
            )
            fig.for_each_annotation(lambda a: a.update(
                text=a.text.split("=")[-1]))  # Limpa o título da faceta

            fig.update_traces(texttemplate='%{x}', textposition='outside')

            return fig
        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro ao gerar o gráfico de top modalidades por tipo de parceiro: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    # Modalidades Vendidas Mês a Mês por Tipo de Parceiro
    def create_modalities_monthly_by_partnership_chart(self, vendas_df: pd.DataFrame, top_n_modalities: int = 3) -> go.Figure:
        """
        Cria um gráfico de linhas facetado mostrando a evolução mensal das vendas
        das top N modalidades para cada tipo de parceiro.
        """
        if vendas_df.empty or 'MES_ANO' not in vendas_df.columns or 'NIVEL' not in vendas_df.columns or 'TIPO_PARCERIA' not in vendas_df.columns:
            return go.Figure().add_annotation(
                text="Dados temporais, de modalidades ou tipo de parceria não disponíveis para este gráfico.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )
        try:
            # 1. Calcular vendas por MES_ANO, TIPO_PARCERIA e NIVEL
            sales_data = vendas_df.groupby(
                ['MES_ANO', 'TIPO_PARCERIA', 'NIVEL']).size().reset_index(name='Vendas')

            # 2. Ordenar MES_ANO para que o gráfico de linha seja contínuo
            sales_data['MES_ANO_ORD'] = pd.to_datetime(sales_data['MES_ANO'])
            sales_data = sales_data.sort_values(
                ['TIPO_PARCERIA', 'MES_ANO_ORD'])

            # 3. Identificar as top N modalidades para cada TIPO_PARCERIA no período total para filtragem consistente
            top_modalities_overall = sales_data.groupby(['TIPO_PARCERIA', 'NIVEL'])[
                'Vendas'].sum().reset_index()
            top_modalities_filtered = []
            for parceria_type in top_modalities_overall['TIPO_PARCERIA'].unique():
                subset = top_modalities_overall[top_modalities_overall['TIPO_PARCERIA']
                                                == parceria_type]
                top_n = subset.nlargest(top_n_modalities, 'Vendas')[
                    'NIVEL'].tolist()
                top_modalities_filtered.extend(
                    [(parceria_type, mod) for mod in top_n])

            # Filtrar o DataFrame principal para incluir apenas as top modalidades identificadas
            # Cria uma tupla (TIPO_PARCERIA, NIVEL) para cada linha e verifica se está nas top_modalities_filtered
            sales_data['temp_key'] = list(
                zip(sales_data['TIPO_PARCERIA'], sales_data['NIVEL']))
            df_filtered_top_modalities = sales_data[sales_data['temp_key'].isin(
                top_modalities_filtered)].copy()
            df_filtered_top_modalities.drop(columns=['temp_key'], inplace=True)

            if df_filtered_top_modalities.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado suficiente encontrado para as top modalidades por tipo de parceiro mensalmente.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=16)
                )

            fig = px.line(
                df_filtered_top_modalities,
                x='MES_ANO',
                y='Vendas',
                color='NIVEL',
                facet_col='TIPO_PARCERIA',
                facet_col_wrap=2,
                title=f'Evolução Mensal das Top {top_n_modalities} Modalidades por Tipo de Parceiro',
                labels={'MES_ANO': 'Mês/Ano',
                        'Vendas': 'Número de Vendas', 'NIVEL': 'Modalidade'},
                line_shape='spline',
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_layout(
                xaxis_title='Mês/Ano',
                yaxis_title='Número de Vendas',
                hovermode='x unified',
                height=700,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom",
                            y=1.02, xanchor="right", x=1),
                xaxis=dict(tickangle=45)
            )
            fig.for_each_annotation(lambda a: a.update(
                text=a.text.split("=")[-1]))  # Limpa o título da faceta

            return fig
        except Exception as e:
            st.error(
                f"Erro ao gerar o gráfico de evolução mensal das modalidades por parceiro: {str(e)}")
            return go.Figure().add_annotation(
                text=f"Erro ao gerar o gráfico de evolução mensal das modalidades por parceiro: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_sales_comparison_chart(self, vendas_df: pd.DataFrame, comparison_type: str,
                                      period1: str, period2: str) -> go.Figure:
        """Cria gráfico de comparação entre períodos/tipos usando barras agrupadas."""

        if vendas_df.empty:
            return go.Figure()

        try:
            # Colunas para agrupamento
            group_col_data = 'NIVEL'  # Para quando comparison_type é "meses" ou "parcerias"
            group_col_period = 'MES_NOME'  # Para quando comparison_type é "modalidades"

            if comparison_type == "meses":
                # Comparação entre meses
                vendas_p1 = vendas_df[vendas_df['MES_NOME'] == period1]
                vendas_p2 = vendas_df[vendas_df['MES_NOME'] == period2]

                # Agrupar por modalidade (NIVEL)
                p1_data = vendas_p1[group_col_data].value_counts()
                p2_data = vendas_p2[group_col_data].value_counts()

                # Combinar dados
                comparison_df = pd.DataFrame({
                    period1: p1_data,
                    period2: p2_data
                })

                title = f'Comparação de Vendas: {period1} vs {period2}'

            elif comparison_type == "parcerias":
                # Comparação entre tipos de parceria
                vendas_p1 = vendas_df[vendas_df['TIPO_PARCERIA'] == period1]
                vendas_p2 = vendas_df[vendas_df['TIPO_PARCERIA'] == period2]

                # Agrupar por modalidade (NIVEL)
                p1_data = vendas_p1[group_col_data].value_counts()
                p2_data = vendas_p2[group_col_data].value_counts()

                # Combinar dados
                comparison_df = pd.DataFrame({
                    period1: p1_data,
                    period2: p2_data
                })

                title = f'Comparação de Vendas por Parceria: {period1} vs {period2}'

            else:  # comparison_type == "modalidades"
                # Comparação entre modalidades
                vendas_p1 = vendas_df[vendas_df['NIVEL'] == period1]
                vendas_p2 = vendas_df[vendas_df['NIVEL'] == period2]

                # Agrupar por mês (MES_NOME)
                p1_data = vendas_p1[group_col_period].value_counts()
                p2_data = vendas_p2[group_col_period].value_counts()

                # Combinar dados
                comparison_df = pd.DataFrame({
                    period1: p1_data,
                    period2: p2_data
                })

                title = f'Comparação de Modalidades: {period1} vs {period2}'

            # Preencher NaNs com 0 (para categorias que não existem em um dos períodos)
            comparison_df = comparison_df.fillna(0)

            # Reset index e renomear a coluna do índice para 'Categoria'
            # Isso garante que a coluna de ID para o melt será sempre 'Categoria'
            comparison_df = comparison_df.reset_index(names=['Categoria'])

            # Realizar o melt
            comparison_df = comparison_df.melt(
                # A coluna 'Categoria' agora contém os nomes das modalidades/meses
                id_vars='Categoria',
                var_name='Período',
                value_name='Vendas'
            )

            # Criar gráfico de barras agrupadas
            fig = px.bar(
                comparison_df,
                x='Categoria',
                y='Vendas',
                color='Período',
                title=title,
                barmode='group',
                text='Vendas'
            )

            fig.update_layout(
                xaxis_title='Categoria',
                yaxis_title='Número de Vendas',
                height=500,
                xaxis=dict(tickangle=45)
            )

            fig.update_traces(textposition='outside')

            return fig

        except Exception as e:
            # Adicionando st.error para debug
            st.error(f"Erro ao gerar comparação: {str(e)}")
            return go.Figure().add_annotation(
                text=f"Erro ao gerar comparação: {str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )

    def create_detailed_sales_comparison_timeline(self, vendas_df: pd.DataFrame, comparison_type: str, item1: str, item2: str, show_cumulative: bool = False) -> go.Figure:
        """Cria gráfico de linha para comparação detalhada de vendas entre dois itens/períodos."""
        if vendas_df.empty:
            return go.Figure().add_annotation(
                text="DataFrame de vendas vazio.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="gray")
            )

        df_filtered = pd.DataFrame()
        title_suffix = ""
        x_axis_title = "Período (Mês/Ano)"
        plot_x_col = 'MES_ANO'  # Default para MES_ANO
        x_axis_type = 'category'  # Default para categoria (para MES_ANO)
        plot_color_col = ''  # Column used to differentiate lines

        # Cores para as traces de linha e acumulada
        colors_map = {
            # Para quando plot_color_col for MES_ANO
            'MES_ANO': px.colors.qualitative.Dark24,
            # Para quando plot_color_col for ANO (mesmo mes, anos diferentes)
            'ANO': px.colors.qualitative.Plotly
        }

        # Obter cores base dinamicamente para os anos
        # Definir cores base para os dois anos (ou tipos de parceria)
        base_colors = {}
        if comparison_type == "mesmo_mes_anos_diferentes":
            # Extrai os anos dos itens
            year1 = int(item1.split(' - ')[1])
            year2 = int(item2.split(' - ')[1])
            years = [year1, year2]

            # Atribui cores distintas para cada ano
            # Usar uma paleta de cores para garantir que as cores sejam diferentes e distinguíveis
            # Uma boa paleta com cores fortes e distintas
            color_palette = px.colors.qualitative.Bold
            # Cor para o primeiro ano
            base_colors[str(year1)] = color_palette[0]
            # Cor para o segundo ano
            base_colors[str(year2)] = color_palette[1]
        elif comparison_type == "tipos_parceria":
            base_colors[item1] = colors_map['MES_ANO'][0]
            base_colors[item2] = colors_map['MES_ANO'][1]

        try:
            if comparison_type == "parceiros_especificos":
                df_filtered = vendas_df[vendas_df['ALUNO'].isin(
                    [item1, item2])].copy()
                title_suffix = f"Entre Parceiros: {item1} vs {item2}"
                plot_color_col = 'ALUNO'

            elif comparison_type == "tipos_parceria":
                df_filtered = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                    [item1, item2])].copy()
                title_suffix = f"Entre Tipos de Parceria: {item1} vs {item2}"
                plot_color_col = 'TIPO_PARCERIA'

            elif comparison_type == "mesmo_mes_anos_diferentes":
                month_name, year1_str = item1.split(' - ')
                _, year2_str = item2.split(' - ')

                year1 = int(year1_str)
                year2 = int(year2_str)

                df_filtered = vendas_df[(vendas_df['MES_NOME'] == month_name) &
                                        (vendas_df['ANO'].isin([
                                            year1, year2]))].copy()
                title_suffix = f"Vendas em {month_name}: {year1} vs {year2}"
                plot_color_col = 'ANO'  # Each year will be a different line
                plot_x_col = 'DIA_DO_MES'  # X-axis will be day of month
                x_axis_title = "Dia do Mês"
                x_axis_type = 'linear'

                if 'DIA_DO_MES' not in df_filtered.columns:
                    return go.Figure().add_annotation(
                        text="Coluna 'DIA_DO_MES' não disponível para esta comparação. Verifique o processamento de dados.",
                        xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=14, color="red")
                    )
            else:
                return go.Figure().add_annotation(
                    text="Tipo de comparação inválido.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=14, color="gray")
                )

            if df_filtered.empty:
                return go.Figure().add_annotation(
                    text="Nenhum dado encontrado para os filtros selecionados.",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(size=14, color="gray")
                )

            # --- Data Aggregation ---
            if comparison_type == "mesmo_mes_anos_diferentes":
                # Agrupar por dia do mês e ano
                sales_data = df_filtered.groupby(
                    [plot_x_col, plot_color_col]).size().reset_index(
                        name='Vendas')
                sales_data = sales_data.sort_values(plot_x_col)
                sales_data[plot_color_col] = sales_data[plot_color_col].astype(
                    str)  # Ensure year is string for color/legend

                # Crie o gráfico com go.Figure() para controle granular
                fig = go.Figure()

                # Adiciona traces para cada ano (vendas diárias e acumuladas)
                for year_val in sorted(sales_data[plot_color_col].unique()):
                    df_year = sales_data[sales_data[plot_color_col]
                                         == year_val].copy()

                    # Vendas Diárias
                    fig.add_trace(go.Scatter(
                        x=df_year[plot_x_col],
                        y=df_year['Vendas'],
                        mode='lines+markers',
                        name=f'Diário ({year_val})',
                        line=dict(color=base_colors[year_val], width=2),
                        marker=dict(size=8, color=base_colors[year_val]),
                        hovertemplate=f'<b>{month_name} %{{x}} ({year_val})</b><br>Vendas Diárias: %{{y}}<extra></extra>'
                    ))

                    if show_cumulative:
                        # Calcular vendas acumuladas
                        df_year['Vendas_Acumuladas'] = df_year['Vendas'].cumsum()
                        fig.add_trace(go.Scatter(
                            x=df_year[plot_x_col],
                            y=df_year['Vendas_Acumuladas'],
                            mode='lines+markers',
                            name=f'Acumulado ({year_val})',
                            # Linha mais grossa e pontilhada
                            line=dict(
                                color=base_colors[year_val], width=3, dash='dash'),
                            marker=dict(size=8, color=base_colors[year_val]),
                            hovertemplate=f'<b>{month_name} %{{x}} ({year_val})</b><br>Vendas Acumuladas: %{{y}}<extra></extra>'
                        ))

                # Configuração dinâmica do eixo X
                xaxis_config = {
                    'tickangle': 45,
                    'title': x_axis_title,  # Título do eixo X
                    'type': x_axis_type,  # Use o tipo definido dinamicamente
                }

                fig.update_layout(
                    title={
                        'text': f'Evolução de Vendas {title_suffix}',
                        'x': 0.5, 'xanchor': 'center', 'font': {'size': 16}
                    },
                    xaxis=xaxis_config,  # Aplicar a configuração dinâmica
                    yaxis_title='Número de Vendas',
                    hovermode='x unified',
                    legend_title='Legenda',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )

            else:  # comparison_type is "tipos_parceria" or "parceiros_especificos"
                if 'MES_ANO_ORDENAVEL' not in df_filtered.columns:
                    # Garantir que MES_ANO_ORDENAVEL existe para ordenação
                    df_filtered['MES_ANO_ORDENAVEL'] = pd.to_datetime(
                        df_filtered['MES_ANO'])
                sales_data = df_filtered.groupby(
                    ['MES_ANO_ORDENAVEL', plot_color_col]).size().reset_index(
                        name='Vendas')
                sales_data = sales_data.sort_values('MES_ANO_ORDENAVEL')
                sales_data['MES_ANO'] = sales_data[
                    'MES_ANO_ORDENAVEL'].dt.strftime(
                    '%Y-%m')  # Format back to string
                plot_x_col = 'MES_ANO'  # Override x-column for this case

                if sales_data.empty:
                    return go.Figure().add_annotation(
                        text="Dados insuficientes para a evolução temporal.",
                        xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=14, color="gray")
                    )

                # --- Plotting com px.line para outros tipos de comparação ---
                fig = px.line(
                    sales_data,
                    x=plot_x_col,
                    y='Vendas',
                    color=plot_color_col,
                    title=f'Evolução de Vendas {title_suffix}',
                    markers=True,
                    line_shape='spline',
                    color_discrete_sequence=px.colors.qualitative.Dark24
                )

                # Configuração dinâmica do eixo X
                xaxis_config = {
                    'tickangle': 45,
                    'title': x_axis_title,  # Título do eixo X
                    'type': x_axis_type,  # Use o tipo definido dinamicamente
                }
                # Adicionar categoryorder apenas se o tipo for 'category'
                if x_axis_type == 'category':
                    xaxis_config['categoryorder'] = 'category ascending'

                fig.update_layout(
                    xaxis=xaxis_config,  # Aplicar a configuração dinâmica
                    yaxis_title='Número de Vendas',
                    hovermode='x unified',
                    legend_title=title_suffix,
                    height=500,
                )

                fig.update_traces(
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                    '%{xaxis.title.text}: %{x}<br>' +
                    'Vendas: %{y}<br>' +
                    '<extra></extra>'
                )
            # Retorna o gráfico criado (seja com go.Figure ou px.line)
            return fig

        except Exception as e:
            st.error(
                f"Erro ao gerar gráfico detalhado de comparação: {str(e)}")
            return go.Figure().add_annotation(
                text=f"Erro ao gerar gráfico detalhado de comparação: {
                    str(e)}",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="red")
            )
