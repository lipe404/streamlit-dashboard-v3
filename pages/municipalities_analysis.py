import streamlit as st
import pandas as pd
import plotly.express as px
from . import BasePage


class MunicipalitiesAnalysis(BasePage):
    """Página de análise de municípios e alunos"""

    def render(self, polos_df, municipios_df, alunos_df):
        st.markdown('<h2 class="section-header">📊 Análise de Municípios e Alunos</h2>',
                    unsafe_allow_html=True)

        if not self.check_data_availability(municipios_df, "municípios"):
            return

        # Seletor para top N
        top_n = st.selectbox("Selecione o número de municípios:", [
                             10, 20, 50], index=0)

        # Renderizar seções
        self._render_top_municipalities(municipios_df, top_n)
        self._render_correlation_analysis(municipios_df)
        self._render_correlation_matrix(municipios_df)

    def _render_top_municipalities(self, municipios_df, top_n):
        """Renderiza análise dos top municípios"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"🏆 Top {top_n} Municípios com Mais Alunos")
            try:
                if 'TOTAL_ALUNOS' in municipios_df.columns and 'MUNICIPIO_IBGE' in municipios_df.columns:
                    # Filtrar municípios com alunos > 0
                    municipios_com_alunos = municipios_df[municipios_df[
                        'TOTAL_ALUNOS'] > 0]

                    if not municipios_com_alunos.empty:
                        top_cidades = municipios_com_alunos.nlargest(
                            top_n, 'TOTAL_ALUNOS')

                        fig_top_cidades = px.bar(
                            top_cidades,
                            x='TOTAL_ALUNOS',
                            y='MUNICIPIO_IBGE',
                            orientation='h',
                            title=f'Top {top_n} Municípios com Mais Alunos',
                            color='TOTAL_ALUNOS',
                            color_continuous_scale='Viridis'
                        )

                        fig_top_cidades.update_layout(
                            xaxis_title='Número de Alunos',
                            yaxis_title='Município',
                            yaxis={'categoryorder': 'total ascending'}
                        )

                        st.plotly_chart(fig_top_cidades,
                                        use_container_width=True)
                    else:
                        st.info("Nenhum município com alunos encontrado.")
                else:
                    st.info("Colunas necessárias não encontradas.")
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {str(e)}")

        with col2:
            st.subheader("📈 Alunos por UF")
            try:
                if 'UF' in municipios_df.columns and 'TOTAL_ALUNOS' in municipios_df.columns:
                    alunos_por_uf = municipios_df.groupby(
                        'UF')['TOTAL_ALUNOS'].sum().reset_index()
                    alunos_por_uf = alunos_por_uf[alunos_por_uf[
                        'TOTAL_ALUNOS'] > 0]

                    if not alunos_por_uf.empty:
                        fig_uf = px.bar(
                            alunos_por_uf,
                            x='UF',
                            y='TOTAL_ALUNOS',
                            title='Distribuição de Alunos por Estado',
                            color='TOTAL_ALUNOS',
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig_uf, use_container_width=True)
                    else:
                        st.info("Dados insuficientes para gerar o gráfico.")
                else:
                    st.info("Colunas necessárias não encontradas.")
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {str(e)}")

    def _render_correlation_analysis(self, municipios_df):
        """Renderiza análises de correlação"""
        st.subheader("🔍 Análises de Correlação")

        col3, col4 = st.columns(2)

        with col3:
            st.subheader("📏 Distância vs Alunos")
            try:
                required_cols = ['DISTANCIA_KM', 'TOTAL_ALUNOS',
                                 'REGIAO', 'MUNICIPIO_IBGE', 'UF']
                if all(col in municipios_df.columns for col in required_cols):
                    # Filtrar dados válidos
                    dados_validos = municipios_df[
                        (municipios_df['DISTANCIA_KM'] > 0) &
                        (municipios_df['TOTAL_ALUNOS'] > 0)
                    ]

                    if not dados_validos.empty and len(dados_validos) > 5:
                        fig_scatter = px.scatter(
                            dados_validos,
                            x='DISTANCIA_KM',
                            y='TOTAL_ALUNOS',
                            color='REGIAO',
                            size='TOTAL_ALUNOS',
                            hover_data=['MUNICIPIO_IBGE', 'UF'],
                            title='Relação entre Distância do Polo e Número de Alunos'
                        )

                        fig_scatter.update_layout(
                            xaxis_title='Distância do Polo (km)',
                            yaxis_title='Número de Alunos'
                        )

                        st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.info("Dados insuficientes para gerar o gráfico.")
                else:
                    st.info("Colunas necessárias não encontradas.")
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {str(e)}")

        with col4:
            st.subheader("📦 Distribuição de Distâncias por UF")
            try:
                if 'DISTANCIA_KM' in municipios_df.columns and 'UF' in municipios_df.columns:
                    # Filtrar dados válidos
                    dados_validos = municipios_df[municipios_df[
                        'DISTANCIA_KM'] > 0]

                    if not dados_validos.empty and len(dados_validos) > 10:
                        fig_boxplot = px.box(
                            dados_validos,
                            x='UF',
                            y='DISTANCIA_KM',
                            title='Distribuição de Distâncias por Estado'
                        )

                        fig_boxplot.update_layout(
                            xaxis_title='Estado (UF)',
                            yaxis_title='Distância (km)',
                            xaxis={'categoryorder': 'total descending'}
                        )

                        st.plotly_chart(fig_boxplot, use_container_width=True)
                    else:
                        st.info("Dados insuficientes para gerar o gráfico.")
                else:
                    st.info("Colunas necessárias não encontradas.")
            except Exception as e:
                st.error(f"Erro ao gerar gráfico: {str(e)}")

    def _render_correlation_matrix(self, municipios_df):
        """Renderiza matriz de correlação"""
        st.subheader("🌡️ Matriz de Correlação")
        try:
            # Selecionar apenas colunas numéricas
            numeric_cols = ['LAT', 'LNG', 'DISTANCIA_KM', 'TOTAL_ALUNOS']
            available_cols = [
                col for col in numeric_cols if col in municipios_df.columns]

            if len(available_cols) >= 2:
                # Filtrar dados válidos
                dados_numericos = municipios_df[available_cols].copy()
                dados_numericos = dados_numericos.dropna()

                if not dados_numericos.empty and len(dados_numericos) > 10:
                    corr_matrix = dados_numericos.corr()

                    fig_corr = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        title='Matriz de Correlação - Variáveis Numéricas',
                        color_continuous_scale='RdBu'
                    )

                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.info(
                        "Dados insuficientes para gerar a matriz.")
            else:
                st.info("Colunas numéricas insuficientes para correlação.")
        except Exception as e:
            st.error(f"Erro ao gerar matriz de correlação: {str(e)}")
