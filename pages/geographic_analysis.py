import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
from . import BasePage


class GeographicAnalysis(BasePage):
    """Página de análise geográfica dos polos"""

    def render(self, polos_df, municipios_df, alunos_df):
        st.markdown('<h2 class="section-header">📍 Análise Geográfica dos Polos</h2>',
                    unsafe_allow_html=True)

        if not self.check_data_availability(polos_df, "polos"):
            return

        # Subseções
        geo_option = st.selectbox(
            "Escolha o tipo de visualização:",
            ["Mapa de Polos", "Mapa de Calor", "Gráficos de Distribuição"]
        )

        if geo_option == "Mapa de Polos":
            self._render_polos_map(polos_df)
        elif geo_option == "Mapa de Calor":
            self._render_heatmap(polos_df)
        elif geo_option == "Gráficos de Distribuição":
            self._render_distribution_charts(polos_df)

    def _render_polos_map(self, polos_df):
        """Renderiza mapa de localização dos polos"""
        st.subheader("🗺️ Localização dos Polos")
        mapa_polos = self.viz.create_polos_map(polos_df, self.map_config)
        st_folium(mapa_polos, width=700, height=500)

    def _render_heatmap(self, polos_df):
        """Renderiza mapa de calor"""
        st.subheader("🔥 Densidade de Polos")
        mapa_calor = self.viz.create_heatmap(polos_df, self.map_config)
        st_folium(mapa_calor, width=700, height=500)

    def _render_distribution_charts(self, polos_df):
        """Renderiza gráficos de distribuição"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Polos por Estado")
            fig_estados = self.viz.create_polos_by_state_chart(polos_df)
            st.plotly_chart(fig_estados, use_container_width=True)

        with col2:
            st.subheader("🥧 Distribuição por Região")
            fig_regioes = self.viz.create_polos_by_region_pie(polos_df)
            st.plotly_chart(fig_regioes, use_container_width=True)
