import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from . import BasePage


class StudentsAnalysis(BasePage):
    """Página de análise de alunos e cursos"""

    def render(self, polos_df, municipios_df, alunos_df):
        st.markdown('<h2 class="section-header">👥 Análise de Alunos e Cursos</h2>',
                    unsafe_allow_html=True)

        if not self.check_data_availability(alunos_df, "alunos"):
            return

        # Análise de cursos
        self._render_course_analysis(alunos_df)

        # Análise por UF
        self._render_uf_analysis(alunos_df)

        # Mapa de densidade
        self._render_density_map(alunos_df, polos_df)

    def _render_course_analysis(self, alunos_df):
        """Renderiza análise de cursos"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📚 Cursos Mais Demandados")
            fig_cursos = self.viz.create_students_by_course_chart(alunos_df)
            st.plotly_chart(fig_cursos, use_container_width=True)

        with col2:
            if 'REGIAO' in alunos_df.columns:
                st.subheader("🌎 Alunos por Região")
                alunos_regiao = alunos_df['REGIAO'].value_counts()
                fig_regiao = px.pie(
                    values=alunos_regiao.values, names=alunos_regiao.index,
                    title='Distribuição de Alunos por Região')
                st.plotly_chart(fig_regiao, use_container_width=True)

    def _render_uf_analysis(self, alunos_df):
        """Renderiza análise por UF"""
        if 'CURSO' in alunos_df.columns and 'UF' in alunos_df.columns:
            st.subheader("📊 Cursos Mais Demandados por UF")

            # Seletor de UF
            ufs_disponiveis = sorted(alunos_df['UF'].dropna().unique())
            uf_selecionada = st.selectbox(
                "Selecione um estado:", ufs_disponiveis)

            if uf_selecionada:
                alunos_uf = alunos_df[alunos_df['UF'] == uf_selecionada]
                cursos_uf = alunos_uf['CURSO'].value_counts().head(10)

                fig_cursos_uf = px.bar(
                    x=cursos_uf.values,
                    y=cursos_uf.index,
                    orientation='h',
                    title=f'Top 10 Cursos em {uf_selecionada}'
                )
                fig_cursos_uf.update_layout(
                    yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_cursos_uf, use_container_width=True)

    def _render_density_map(self, alunos_df, polos_df):
        """Renderiza mapa de densidade de alunos"""
        if 'LAT' in alunos_df.columns and 'LNG' in alunos_df.columns:
            st.subheader("🗺️ Densidade de Alunos por Localização")

            # Filtrar alunos com coordenadas válidas
            alunos_com_coord = alunos_df.dropna(subset=['LAT', 'LNG'])

            if not alunos_com_coord.empty:
                # Criar mapa de densidade
                m = folium.Map(
                    location=[self.map_config['center_lat'],
                              self.map_config['center_lon']],
                    zoom_start=self.map_config['zoom']
                )

                # Dados para heatmap
                heat_data = [[row['LAT'], row['LNG']]
                             for _, row in alunos_com_coord.iterrows()]

                if heat_data:
                    from folium import plugins
                    plugins.HeatMap(heat_data, radius=15).add_to(m)

                    # Adicionar polos ao mapa
                    if not polos_df.empty:
                        for _, polo in polos_df.iterrows():
                            if pd.notna(polo['lat']) and pd.notna(
                                    polo['long']):
                                folium.Marker(
                                    location=[polo['lat'], polo['long']],
                                    popup=f"<b>{polo['UNIDADE']}</b>",
                                    icon=folium.Icon(
                                        color='red',
                                        icon='graduation-cap',
                                        prefix='fa')
                                ).add_to(m)

                    st_folium(m, width=700, height=500)
