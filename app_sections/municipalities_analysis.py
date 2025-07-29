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
                             10, 20, 50, 100], index=0)

        # Renderizar seções
        self._render_top_municipalities(municipios_df, top_n)
        self._render_correlation_analysis(municipios_df)
        self._render_comparative_analysis(
            municipios_df, polos_df)  # Nova seção

    def _render_top_municipalities(self, municipios_df, top_n):
        """Renderiza análise dos top municípios"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"🏆 Top {top_n} Municípios com Mais Alunos")
            try:
                if 'TOTAL_ALUNOS' in municipios_df.columns and 'MUNICIPIO_IBGE' in municipios_df.columns:
                    # Filtrar municípios com alunos > 0
                    municipios_com_alunos = municipios_df[municipios_df['TOTAL_ALUNOS'] > 0]

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
                    alunos_por_uf = alunos_por_uf[alunos_por_uf['TOTAL_ALUNOS'] > 0]

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
                    dados_validos = municipios_df[municipios_df['DISTANCIA_KM'] > 0]

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

    def _render_comparative_analysis(self, municipios_df, polos_df):
        """Renderiza análise comparativa de alunos vs polos"""
        st.subheader("⚖️ Análise Comparativa: Alunos vs Polos")

        # Verificar se há dados de polos
        if not self.check_data_availability(polos_df, "polos"):
            return

        # Controles de filtro
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            filter_type = st.selectbox(
                "Filtrar por:",
                ["UF", "REGIAO"],
                help="Escolha se deseja filtrar por Estado (UF) ou Região"
            )

        with col_filter2:
            # Obter valores únicos para o filtro
            if filter_type == "UF":
                filter_options = [
                    "Todos"] + sorted(municipios_df['UF'].dropna().unique().tolist())
            else:
                filter_options = [
                    "Todos"] + sorted(municipios_df['REGIAO'].dropna().unique().tolist())

            filter_value = st.selectbox(
                f"Selecione {filter_type}:",
                filter_options
            )

        # Gráfico comparativo principal
        try:
            fig_comparison = self.viz.create_students_vs_polos_comparison(
                municipios_df, polos_df, filter_type, filter_value
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico comparativo: {str(e)}")

        # Análise de eficiência
        col_eff1, col_eff2 = st.columns(2)

        with col_eff1:
            st.subheader("📊 Eficiência por Estado")
            try:
                fig_efficiency_uf = self.viz.create_efficiency_analysis_chart(
                    municipios_df, polos_df, "UF"
                )
                st.plotly_chart(fig_efficiency_uf, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar análise de eficiência por UF: {str(e)}")

        with col_eff2:
            st.subheader("🌎 Eficiência por Região")
            try:
                fig_efficiency_regiao = self.viz.create_efficiency_analysis_chart(
                    municipios_df, polos_df, "REGIAO"
                )
                st.plotly_chart(fig_efficiency_regiao,
                                use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar análise de eficiência por Região: {str(e)}")

        # Tabela resumo
        self._render_summary_table(
            municipios_df, polos_df, filter_type, filter_value)

    def _render_summary_table(self, municipios_df, polos_df, filter_type, filter_value):
        """Renderiza tabela resumo da análise"""
        st.subheader("📋 Resumo da Análise")

        try:
            # Filtrar dados se necessário
            if filter_value != "Todos":
                municipios_filtered = municipios_df[municipios_df[filter_type]
                                                    == filter_value]
                polos_filtered = polos_df[polos_df[filter_type]
                                          == filter_value]
            else:
                municipios_filtered = municipios_df.copy()
                polos_filtered = polos_df.copy()

            # Calcular estatísticas por grupo
            group_col = filter_type

            summary_stats = municipios_filtered.groupby(group_col).agg({
                'TOTAL_ALUNOS': ['sum', 'mean', 'count'],
                'DISTANCIA_KM': 'mean'
            }).round(2)

            summary_stats.columns = [
                'Total_Alunos', 'Media_Alunos_por_Municipio', 'Num_Municipios', 'Distancia_Media_km']
            summary_stats = summary_stats.reset_index()

            # Adicionar dados de polos
            polos_stats = polos_filtered.groupby(
                group_col).size().reset_index(name='Total_Polos')
            summary_final = pd.merge(
                summary_stats, polos_stats, on=group_col, how='outer').fillna(0)

            # Calcular eficiência
            summary_final['Alunos_por_Polo'] = summary_final.apply(
                lambda row: round(
                    row['Total_Alunos'] / row['Total_Polos'], 1) if row['Total_Polos'] > 0 else 0,
                axis=1
            )

            # Renomear colunas para exibição
            summary_final.columns = [
                group_col, 'Total de Alunos', 'Média Alunos/Município',
                'Nº Municípios', 'Distância Média (km)', 'Total de Polos', 'Alunos por Polo'
            ]

            # Ordenar por eficiência
            summary_final = summary_final.sort_values(
                'Alunos por Polo', ascending=False)

            # Exibir tabela
            st.dataframe(
                summary_final,
                use_container_width=True,
                hide_index=True
            )

        except Exception as e:
            st.error(f"Erro ao gerar tabela resumo: {str(e)}")
