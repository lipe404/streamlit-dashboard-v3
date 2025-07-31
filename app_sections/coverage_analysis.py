import streamlit as st
from streamlit_folium import st_folium
import plotly.express as px
from utils.data_processor import DataProcessor
from . import BasePage


class CoverageAnalysis(BasePage):
    """Página de análise de cobertura e eficiência"""

    def render(self, polos_df, municipios_df, alunos_df):
        st.markdown('<h2 class="section-header">🎯 Análise de Cobertura e Eficiência</h2>',
                    unsafe_allow_html=True)

        if not (self.check_data_availability(polos_df, "polos") and
                self.check_data_availability(municipios_df, "municípios")):
            return

        # Calcular métricas de cobertura
        metrics = DataProcessor.calculate_coverage_metrics(
            polos_df, municipios_df)

        # Exibir métricas de cobertura
        self._display_coverage_metrics(metrics, polos_df)

        # Mapa de cobertura
        self._render_coverage_map(polos_df, municipios_df)

        # Análise por região
        self._render_regional_analysis(municipios_df)

    def _display_coverage_metrics(self, metrics, polos_df):
        """Exibe métricas de cobertura"""
        # Quatro colunas para as métricas originais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Municípios Cobertos",
                      f"{metrics.get('municipios_cobertos', 0)}/{
                          metrics.get('total_municipios', 0)}")

        with col2:
            st.metric("% Cobertura",
                      f"{metrics.get('percentual_cobertura', 0):.1f}%")

        with col3:
            st.metric("Distância Média",
                      f"{metrics.get('distancia_media', 0):.1f} km")

        with col4:
            eficiencia = metrics.get(
                'alunos_cobertos', 0) / len(polos_df) if len(
                    polos_df) > 0 else 0
            st.metric("Alunos por Polo", f"{eficiencia:.0f}")

        # Novas métricas em uma nova linha para melhor visualização
        st.markdown("---")  # Adiciona um separador visual
        col5, col6 = st.columns(2)

        with col5:
            st.metric("Municípios Cobertos c/ Alunos",
                      f"{metrics.get('municipios_cobertos_com_alunos', 0)}/{
                          metrics.get('total_municipios_com_alunos', 0)}")

        with col6:
            st.metric("% Cobertura c/ Alunos",
                      f"{metrics.get('percentual_cobertura_com_alunos', 0):.1f}%")

    def _render_coverage_map(self, polos_df, municipios_df):
        """Renderiza mapa de cobertura"""
        st.subheader("🗺️ Mapa de Cobertura (Raio 100km)")
        mapa_cobertura = self.viz.create_coverage_map(
            polos_df, municipios_df, self.map_config)
        st_folium(mapa_cobertura, width=700, height=500)

    def _render_regional_analysis(self, municipios_df):
        """Renderiza análise por região"""
        st.subheader("�� Eficiência por Região")

        if 'REGIAO' in municipios_df.columns:
            eficiencia_regiao = municipios_df.groupby('REGIAO').agg({
                'TOTAL_ALUNOS': 'sum',
                'DISTANCIA_KM': 'mean',
                'MUNICIPIO_IBGE': 'count'
            }).reset_index()

            eficiencia_regiao.columns = [
                'Região', 'Total Alunos', 'Distância Média', 'Municípios']

            # Calcular eficiência (alunos por município)
            eficiencia_regiao['Eficiência'] = eficiencia_regiao[
                'Total Alunos'] / \
                eficiencia_regiao['Municípios']

            col1, col2 = st.columns(2)

            with col1:
                fig_regiao_alunos = px.bar(
                    eficiencia_regiao, x='Região', y='Total Alunos',
                    title='Total de Alunos por Região')
                st.plotly_chart(fig_regiao_alunos, use_container_width=True)

            with col2:
                fig_regiao_dist = px.bar(
                    eficiencia_regiao, x='Região', y='Distância Média',
                                         title='Distância Média por Região')
                st.plotly_chart(fig_regiao_dist, use_container_width=True)

            # Tabela de eficiência
            st.subheader("📋 Resumo de Eficiência por Região")
            st.dataframe(eficiencia_regiao.round(2), use_container_width=True)
