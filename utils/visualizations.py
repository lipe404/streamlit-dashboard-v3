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

    def create_heatmap(
            self, polos_df: pd.DataFrame, map_config: Dict) -> folium.Map:
        """Cria mapa de calor dos polos"""
        m = folium.Map(
            location=[map_config['center_lat'], map_config['center_lon']],
            zoom_start=map_config['zoom']
        )

        if not polos_df.empty:
            heat_data = []
            for _, row in polos_df.iterrows():
                try:
                    lat_val = row.get('lat', None)
                    lng_val = row.get('long', None)
                    if pd.notna(lat_val) and pd.notna(lng_val):
                        heat_data.append([float(lat_val), float(lng_val)])
                except:
                    continue

            if heat_data:
                plugins.HeatMap(heat_data, radius=50).add_to(m)

        return m

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
