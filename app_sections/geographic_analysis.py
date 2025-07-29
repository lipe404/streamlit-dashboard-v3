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
            ["Mapa de Polos", "Mapa de Cobertura Municipal",
                "Gráficos de Distribuição"]
        )

        if geo_option == "Mapa de Polos":
            self._render_polos_map(polos_df)
        elif geo_option == "Mapa de Cobertura Municipal":
            self._render_municipal_coverage_map(polos_df, municipios_df)
        elif geo_option == "Gráficos de Distribuição":
            self._render_distribution_charts(polos_df)

    def _render_polos_map(self, polos_df):
        """Renderiza mapa de localização dos polos"""
        st.subheader("🗺️ Localização dos Polos")
        mapa_polos = self.viz.create_polos_map(polos_df, self.map_config)
        st_folium(mapa_polos, width=700, height=500)

    def _render_municipal_coverage_map(self, polos_df, municipios_df):
        """Renderiza mapa de cobertura municipal com delimitações"""
        st.subheader("🗺️ Cobertura Municipal dos Polos")

        # Informações sobre o mapa
        st.info("""
        **Legenda do Mapa:**
        - 🟤 **Marrom**: Municípios com polos ativos
        - 🔵 **Azul**: Municípios no raio de 100km dos polos
        - ⚫ **Cinza**: Municípios fora da cobertura
        - 🎓 **Marcadores Vermelhos**: Localização dos polos

        **Nota**: As delimitações mostram as fronteiras reais dos municípios.
        """)

        # Verificar se há dados de municípios
        if not self.check_data_availability(municipios_df, "municípios"):
            st.warning(
                "Dados de municípios necessários para criar o mapa.")
            return

        # Opções de visualização
        map_type = st.radio(
            "Escolha o tipo de delimitação:",
            ["Delimitações Simplificadas",
                "Delimitações IBGE (Mais Detalhado)"],
            help="Delimitações IBGE são mais precisas mas podem demorar."
        )

        # Aprimorar dados municipais
        from utils.data_processor import DataProcessor
        municipios_enhanced = DataProcessor.enhance_municipal_data_for_coverage(
            municipios_df, polos_df
        )

        # Criar o mapa
        try:
            if map_type == "Delimitações IBGE (Mais Detalhado)":
                with st.spinner(
                        "Carregando delimitações detalhadas do IBGE..."):
                    mapa_cobertura = self.viz.create_municipal_coverage_map_ibge(
                        polos_df, municipios_enhanced, self.map_config
                    )
            else:
                with st.spinner("Carregando delimitações simplificadas..."):
                    mapa_cobertura = self.viz.create_municipal_coverage_map_with_boundaries(
                        polos_df, municipios_enhanced, self.map_config
                    )

            st_folium(mapa_cobertura, width=700, height=500)

            # Estatísticas de cobertura
            self._display_coverage_stats(polos_df, municipios_enhanced)

        except Exception as e:
            st.error(f"Erro ao criar mapa de cobertura: {str(e)}")
            st.exception(e)  # Para debug

    def _display_coverage_stats(self, polos_df, municipios_df):
        """Exibe estatísticas de cobertura"""
        try:
            # Calcular estatísticas
            total_municipios = len(municipios_df)

            # Municípios com polos
            municipios_com_polos = 0
            if 'UNIDADE_POLO' in municipios_df.columns:
                municipios_com_polos = municipios_df['UNIDADE_POLO'].notna(
                ).sum()

            # Municípios na cobertura (distância <= 100km)
            municipios_cobertura = 0
            if 'DISTANCIA_KM' in municipios_df.columns:
                municipios_cobertura = (
                    municipios_df['DISTANCIA_KM'] <= 100).sum()

            # Exibir métricas
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Municípios", total_municipios)

            with col2:
                st.metric("Municípios com Polos", municipios_com_polos)

            with col3:
                st.metric("Municípios na Cobertura", municipios_cobertura)

            with col4:
                cobertura_pct = (
                    municipios_cobertura / total_municipios * 100
                    ) if total_municipios > 0 else 0
                st.metric("% Cobertura", f"{cobertura_pct:.1f}%")

        except Exception as e:
            st.warning(
                "Não foi possível calcular as estatísticas de cobertura.")

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
