import geopandas as gpd
import json
from utils.geo_data_loader import GeoDataLoader
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import folium
from folium import plugins
import streamlit as st
from typing import Dict, List, Tuple


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
            # Carregar dados geográficos dos municípios
            st.info("Carregando delimitações municipais...")

            # Criar GeoJSON baseado nos dados disponíveis
            municipal_geojson = GeoDataLoader.create_municipal_geojson_from_data(
                municipios_df)

            if municipal_geojson and municipal_geojson['features']:
                self._add_municipal_boundaries_to_map(
                    m, municipal_geojson, polos_df)
            else:
                st.warning("Usando representação simplificada dos municípios.")
                # Fallback para o método anterior
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
            return self.create_municipal_coverage_map(polos_df, municipios_df, map_config)

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
            municipio_nome = feature['properties'].get('name', '').upper().strip()
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
                aliases=['Município:', 'UF:', 'Total Alunos:', 'Distância (km):', 'Polo Próximo:'],
                localize=True,
                labels=True,
                style="background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;"
            ),
            tooltip=folium.GeoJsonTooltip(
                fields=['name', 'uf'],
                aliases=['Município:', 'UF:'],
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

                # Carregar dados geográficos por estado
                geo_data = GeoDataLoader.load_municipal_boundaries_by_state(uf)

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
                    background-color: purple;
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
