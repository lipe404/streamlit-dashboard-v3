import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from . import BasePage
from typing import Dict, List


class AlignmentAnalysis(BasePage):
    """Página de análise geográfica e demográfica de vendas"""

    def render(self, polos_df, municipios_df, vendas_df):
        st.markdown(
            '<h2 class="section-header">🔄 Análise Geográfica e Demográfica</h2>',
            unsafe_allow_html=True)

        if not self.check_data_availability(vendas_df, "vendas"):
            return

        # Verificar se temos dados geográficos
        if 'CIDADE' not in vendas_df.columns or 'UF' not in vendas_df.columns:
            st.warning(
                "Dados geográficos (Cidade/UF) não disponíveis nos dados de vendas.")
            return

        # FILTRAR DADOS GEOGRÁFICOS VÁLIDOS
        vendas_df_filtered = self._filter_valid_geographic_data(vendas_df)

        if vendas_df_filtered.empty:
            st.error(
                "❌ Nenhum dado com informações geográficas válidas encontrado.")
            return

        # Exibir informações sobre a filtragem
        self._display_data_filtering_info(vendas_df, vendas_df_filtered)

        # Métricas principais geográficas
        self._display_geographic_metrics(vendas_df_filtered)

        # Análise por Estado
        self._render_state_analysis(vendas_df_filtered)

        # Análise por Região
        self._render_region_analysis(vendas_df_filtered)

        # Análise de Cidades
        self._render_city_analysis(vendas_df_filtered)

        # Análise de Cursos por Localização
        self._render_courses_by_location(vendas_df_filtered)

        # Análise de Modalidades por Localização
        self._render_modalities_by_location(vendas_df_filtered)

        # Análise de Parcerias por Localização
        self._render_partnerships_by_location(vendas_df_filtered)

        # Mapa de Distribuição Geográfica
        self._render_geographic_distribution_map(vendas_df_filtered, polos_df)

    def _filter_valid_geographic_data(self, vendas_df):
        """Filtra apenas dados com informações geográficas válidas"""
        try:
            # Criar cópia para não modificar o original
            df_filtered = vendas_df.copy()

            # Filtros para dados geográficos válidos
            valid_conditions = []

            # Filtrar UF válidos (não vazios, não nulos, não "Não identificado")
            if 'UF' in df_filtered.columns:
                valid_conditions.append(
                    df_filtered['UF'].notna() &
                    (df_filtered['UF'] != '') &
                    (df_filtered['UF'].str.strip() != '') &
                    (df_filtered['UF'].str.upper() != 'NÃO IDENTIFICADO') &
                    (df_filtered['UF'].str.upper() != 'NAO IDENTIFICADO') &
                    (df_filtered['UF'] != 'nan')
                )

            # Filtrar CIDADE válidas (não vazias, não nulas, não "Não identificado")
            if 'CIDADE' in df_filtered.columns:
                valid_conditions.append(
                    df_filtered['CIDADE'].notna() &
                    (df_filtered['CIDADE'] != '') &
                    (df_filtered['CIDADE'].str.strip() != '') &
                    (df_filtered['CIDADE'].str.upper() != 'NÃO IDENTIFICADO') &
                    (df_filtered['CIDADE'].str.upper() != 'NAO IDENTIFICADO') &
                    (df_filtered['CIDADE'] != 'nan')
                )

            # Filtrar REGIAO válidas (não "Não identificado")
            if 'REGIAO' in df_filtered.columns:
                valid_conditions.append(
                    df_filtered['REGIAO'].notna() &
                    (df_filtered['REGIAO'] != '') &
                    (df_filtered['REGIAO'].str.strip() != '') &
                    (df_filtered['REGIAO'].str.upper() != 'NÃO IDENTIFICADO') &
                    (df_filtered['REGIAO'].str.upper() != 'NAO IDENTIFICADO') &
                    (df_filtered['REGIAO'] != 'nan')
                )

            # Aplicar todos os filtros
            if valid_conditions:
                final_condition = valid_conditions[0]
                for condition in valid_conditions[1:]:
                    final_condition = final_condition & condition

                df_filtered = df_filtered[final_condition]

            return df_filtered

        except Exception as e:
            st.error(f"Erro ao filtrar dados geográficos: {str(e)}")
            return pd.DataFrame()

    def _display_data_filtering_info(self, original_df, filtered_df):
        """Exibe informações sobre a filtragem de dados"""
        total_original = len(original_df)
        total_filtered = len(filtered_df)
        removed_count = total_original - total_filtered
        percentage_valid = (total_filtered / total_original *
                            100) if total_original > 0 else 0

        st.info(f"""
        📊 **Filtragem de Dados Geográficos:**
        - **Total de registros:** {total_original:,}
        - **Registros com dados geográficos válidos:** {total_filtered:,} ({percentage_valid:.1f}%)
        - **Registros removidos (sem dados geográficos):** {removed_count:,}
        
        ℹ️ *Esta análise considera apenas vendas com informações completas de Cidade, UF e Região.*
        """)

    def _display_geographic_metrics(self, vendas_df):
        """Exibe métricas principais geográficas"""
        st.subheader("📊 Métricas Geográficas Principais")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_estados = vendas_df['UF'].nunique(
            ) if 'UF' in vendas_df.columns else 0
            st.metric("Estados com Vendas", total_estados)

        with col2:
            total_cidades = vendas_df['CIDADE'].nunique(
            ) if 'CIDADE' in vendas_df.columns else 0
            st.metric("Cidades com Vendas", total_cidades)

        with col3:
            total_regioes = vendas_df['REGIAO'].nunique(
            ) if 'REGIAO' in vendas_df.columns else 0
            st.metric("Regiões Atendidas", total_regioes)

        with col4:
            concentracao_top5_estados = self._calculate_concentration_top5_states(
                vendas_df)
            st.metric("Concentração Top 5 Estados",
                      f"{concentracao_top5_estados:.1f}%")

    def _calculate_concentration_top5_states(self, vendas_df):
        """Calcula a concentração de vendas nos top 5 estados"""
        if 'UF' not in vendas_df.columns or vendas_df.empty:
            return 0

        vendas_por_estado = vendas_df['UF'].value_counts()
        top5_vendas = vendas_por_estado.head(5).sum()
        total_vendas = len(vendas_df)

        return (top5_vendas / total_vendas * 100) if total_vendas > 0 else 0

    def _render_state_analysis(self, vendas_df):
        """Renderiza análise por estado"""
        st.subheader("🗺️ Análise por Estado")

        if 'UF' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de UF não disponíveis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Ranking de estados
            st.markdown("#### 🏆 Ranking de Estados")

            vendas_por_estado = vendas_df['UF'].value_counts().reset_index()
            vendas_por_estado.columns = ['UF', 'Total_Vendas']
            vendas_por_estado['Percentual'] = (
                vendas_por_estado['Total_Vendas'] / len(vendas_df) * 100).round(2)
            vendas_por_estado['Ranking'] = range(1, len(vendas_por_estado) + 1)

            # Reordenar colunas
            vendas_por_estado = vendas_por_estado[[
                'Ranking', 'UF', 'Total_Vendas', 'Percentual']]

            st.dataframe(vendas_por_estado.head(
                10), use_container_width=True, hide_index=True)

        with col2:
            # Gráfico de barras dos top estados
            st.markdown("#### 📊 Top 10 Estados")

            top_estados = vendas_por_estado.head(10)

            fig_estados = px.bar(
                top_estados,
                x='Total_Vendas',
                y='UF',
                orientation='h',
                title='Top 10 Estados por Número de Vendas',
                color='Total_Vendas',
                color_continuous_scale='Viridis',
                text='Total_Vendas'
            )

            fig_estados.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=400,
                showlegend=False
            )

            fig_estados.update_traces(textposition='outside')

            st.plotly_chart(fig_estados, use_container_width=True)

        # Análise detalhada por estado selecionado
        st.markdown("#### 🔍 Análise Detalhada por Estado")

        estados_disponiveis = sorted(vendas_df['UF'].dropna().unique())
        estado_selecionado = st.selectbox(
            "Selecione um estado para análise detalhada:",
            estados_disponiveis,
            key="estado_analise_detalhada"
        )

        if estado_selecionado:
            self._render_detailed_state_analysis(vendas_df, estado_selecionado)

    def _render_detailed_state_analysis(self, vendas_df, estado):
        """Renderiza análise detalhada de um estado específico"""
        vendas_estado = vendas_df[vendas_df['UF'] == estado]

        col1, col2, col3 = st.columns(3)

        with col1:
            total_vendas_estado = len(vendas_estado)
            st.metric(f"Vendas em {estado}", f"{total_vendas_estado:,}")

        with col2:
            cidades_estado = vendas_estado['CIDADE'].nunique(
            ) if 'CIDADE' in vendas_estado.columns else 0
            st.metric(f"Cidades em {estado}", cidades_estado)

        with col3:
            cursos_estado = vendas_estado['CURSO'].nunique(
            ) if 'CURSO' in vendas_estado.columns else 0
            st.metric(f"Cursos em {estado}", cursos_estado)

        # Análises específicas do estado
        col_det1, col_det2 = st.columns(2)

        with col_det1:
            # Top cidades do estado
            if 'CIDADE' in vendas_estado.columns:
                st.markdown(f"**🏙️ Top Cidades - {estado}**")
                cidades_estado = vendas_estado['CIDADE'].value_counts().head(5)

                fig_cidades = px.bar(
                    x=cidades_estado.values,
                    y=cidades_estado.index,
                    orientation='h',
                    title=f'Top 5 Cidades - {estado}',
                    color=cidades_estado.values,
                    color_continuous_scale='Blues'
                )

                fig_cidades.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    height=300,
                    showlegend=False
                )

                st.plotly_chart(fig_cidades, use_container_width=True)

        with col_det2:
            # Top cursos do estado
            if 'CURSO' in vendas_estado.columns:
                st.markdown(f"**📚 Top Cursos - {estado}**")
                cursos_estado = vendas_estado['CURSO'].value_counts().head(5)

                fig_cursos = px.bar(
                    x=cursos_estado.values,
                    y=cursos_estado.index,
                    orientation='h',
                    title=f'Top 5 Cursos - {estado}',
                    color=cursos_estado.values,
                    color_continuous_scale='Oranges'
                )

                fig_cursos.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    height=300,
                    showlegend=False
                )

                st.plotly_chart(fig_cursos, use_container_width=True)

    def _render_region_analysis(self, vendas_df):
        """Renderiza análise por região"""
        st.subheader("🌎 Análise por Região")

        if 'REGIAO' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de região não disponíveis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de pizza por região
            vendas_por_regiao = vendas_df['REGIAO'].value_counts()

            fig_regiao_pie = px.pie(
                values=vendas_por_regiao.values,
                names=vendas_por_regiao.index,
                title='Distribuição de Vendas por Região',
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig_regiao_pie.update_traces(
                textposition='inside',
                textinfo='percent+label'
            )

            st.plotly_chart(fig_regiao_pie, use_container_width=True)

        with col2:
            # Análise de modalidades por região
            if 'NIVEL' in vendas_df.columns:
                st.markdown("#### 🎓 Modalidades Mais Vendidas por Região")

                modalidades_regiao = vendas_df.groupby(
                    ['REGIAO', 'NIVEL']).size().reset_index(name='Vendas')
                top_modalidades_regiao = modalidades_regiao.loc[modalidades_regiao.groupby('REGIAO')[
                    'Vendas'].idxmax()]

                fig_modal_regiao = px.bar(
                    top_modalidades_regiao,
                    x='REGIAO',
                    y='Vendas',
                    color='NIVEL',
                    title='Modalidade Mais Vendida por Região',
                    text='Vendas'
                )

                fig_modal_regiao.update_traces(textposition='outside')
                fig_modal_regiao.update_layout(height=400)

                st.plotly_chart(fig_modal_regiao, use_container_width=True)

        # Tabela resumo por região
        st.markdown("#### 📋 Resumo Detalhado por Região")

        resumo_regiao = self._create_region_summary(vendas_df)
        if not resumo_regiao.empty:
            st.dataframe(resumo_regiao, use_container_width=True,
                         hide_index=True)

    def _create_region_summary(self, vendas_df):
        """Cria resumo detalhado por região"""
        if 'REGIAO' not in vendas_df.columns or vendas_df.empty:
            return pd.DataFrame()

        try:
            resumo = vendas_df.groupby('REGIAO').agg({
                'CIDADE': 'nunique',
                'UF': 'nunique',
                'CURSO': 'nunique',
                'NIVEL': 'nunique',
                'TIPO_PARCERIA': lambda x: x.mode().iloc[0] if not x.empty else 'N/A'
            }).reset_index()

            # Adicionar contagem de vendas
            vendas_por_regiao = vendas_df['REGIAO'].value_counts(
            ).reset_index()
            vendas_por_regiao.columns = ['REGIAO', 'Total_Vendas']

            resumo = resumo.merge(vendas_por_regiao, on='REGIAO', how='left')

            # Renomear colunas
            resumo.columns = ['Região', 'Cidades', 'Estados', 'Cursos',
                              'Modalidades', 'Parceria_Dominante', 'Total_Vendas']

            # Calcular percentual
            resumo['Percentual'] = (
                resumo['Total_Vendas'] / len(vendas_df) * 100).round(2)

            # Ordenar por total de vendas
            resumo = resumo.sort_values('Total_Vendas', ascending=False)

            return resumo

        except Exception as e:
            st.error(f"Erro ao criar resumo por região: {str(e)}")
            return pd.DataFrame()

    def _render_city_analysis(self, vendas_df):
        """Renderiza análise por cidade"""
        st.subheader("🏙️ Análise por Cidade")

        if 'CIDADE' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de cidade não disponíveis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Top cidades
            st.markdown("#### 🏆 Top 15 Cidades")

            top_cidades = vendas_df['CIDADE'].value_counts().head(
                15).reset_index()
            top_cidades.columns = ['Cidade', 'Vendas']

            fig_cidades = px.bar(
                top_cidades,
                x='Vendas',
                y='Cidade',
                orientation='h',
                title='Top 15 Cidades por Número de Vendas',
                color='Vendas',
                color_continuous_scale='Plasma',
                text='Vendas'
            )

            fig_cidades.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                height=500,
                showlegend=False
            )

            fig_cidades.update_traces(textposition='outside')

            st.plotly_chart(fig_cidades, use_container_width=True)

        with col2:
            # Análise de concentração urbana
            st.markdown("#### 📈 Concentração Urbana")

            vendas_por_cidade = vendas_df['CIDADE'].value_counts()
            total_cidades = len(vendas_por_cidade)

            # Calcular concentração
            top5_cidades = vendas_por_cidade.head(5).sum()
            top10_cidades = vendas_por_cidade.head(10).sum()
            top20_cidades = vendas_por_cidade.head(20).sum()

            concentracao_data = {
                'Grupo': ['Top 5 Cidades', 'Top 10 Cidades', 'Top 20 Cidades'],
                'Vendas': [top5_cidades, top10_cidades, top20_cidades],
                'Percentual': [
                    (top5_cidades / len(vendas_df) * 100),
                    (top10_cidades / len(vendas_df) * 100),
                    (top20_cidades / len(vendas_df) * 100)
                ]
            }

            df_concentracao = pd.DataFrame(concentracao_data)

            fig_concentracao = px.bar(
                df_concentracao,
                x='Grupo',
                y='Percentual',
                title='Concentração de Vendas por Grupos de Cidades',
                color='Percentual',
                color_continuous_scale='Reds',
                text='Percentual'
            )

            fig_concentracao.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside'
            )

            fig_concentracao.update_layout(height=400)

            st.plotly_chart(fig_concentracao, use_container_width=True)

            # Métricas de concentração
            st.markdown("**📊 Métricas de Concentração:**")
            st.write(f"• **Total de cidades:** {total_cidades:,}")
            st.write(
                f"• **Top 5 cidades:** {(top5_cidades/len(vendas_df)*100):.1f}% das vendas")
            st.write(
                f"• **Top 10 cidades:** {(top10_cidades/len(vendas_df)*100):.1f}% das vendas")

    def _render_courses_by_location(self, vendas_df):
        """Renderiza análise de cursos por localização"""
        st.subheader("📚 Cursos Mais Vendidos por Localização")

        if 'CURSO' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de cursos não disponíveis.")
            return

        # Filtros
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            tipo_localizacao = st.selectbox(
                "Tipo de localização:",
                ["Por Estado", "Por Região", "Por Cidade"],
                key="curso_localizacao_tipo"
            )

        with col_filter2:
            top_n_cursos = st.selectbox(
                "Número de cursos por localização:",
                [3, 5, 10, 15],
                index=1,
                key="curso_localizacao_top_n"
            )

        # Determinar coluna de agrupamento
        if tipo_localizacao == "Por Estado":
            location_col = 'UF'
        elif tipo_localizacao == "Por Região":
            location_col = 'REGIAO'
        else:  # Por Cidade
            location_col = 'CIDADE'

        if location_col not in vendas_df.columns:
            st.warning(f"Dados de {location_col} não disponíveis.")
            return

        # Criar análise
        cursos_por_localizacao = vendas_df.groupby(
            [location_col, 'CURSO']).size().reset_index(name='Vendas')

        # Obter top cursos por localização
        top_cursos_localizacao = []

        for localizacao in cursos_por_localizacao[location_col].unique():
            loc_data = cursos_por_localizacao[cursos_por_localizacao[location_col] == localizacao]
            top_loc = loc_data.nlargest(top_n_cursos, 'Vendas')
            top_cursos_localizacao.append(top_loc)

        if top_cursos_localizacao:
            dados_finais = pd.concat(top_cursos_localizacao, ignore_index=True)

            # Limitar a 10 localizações para melhor visualização
            top_localizacoes = vendas_df[location_col].value_counts().head(
                10).index
            dados_finais = dados_finais[dados_finais[location_col].isin(
                top_localizacoes)]

            if not dados_finais.empty:
                fig_cursos_loc = px.bar(
                    dados_finais,
                    x=location_col,
                    y='Vendas',
                    color='CURSO',
                    title=f'Top {top_n_cursos} Cursos Mais Vendidos {tipo_localizacao}',
                    text='Vendas'
                )

                fig_cursos_loc.update_layout(
                    height=600,
                    xaxis=dict(tickangle=45),
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02
                    ),
                    margin=dict(r=300)
                )

                fig_cursos_loc.update_traces(textposition='outside')

                st.plotly_chart(fig_cursos_loc, use_container_width=True)

    def _render_modalities_by_location(self, vendas_df):
        """Renderiza análise de modalidades por localização"""
        st.subheader("🎓 Modalidades por Localização")

        if 'NIVEL' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de modalidades não disponíveis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Heatmap de modalidades por região
            if 'REGIAO' in vendas_df.columns:
                st.markdown("#### 🔥 Heatmap: Modalidades por Região")

                modalidades_regiao = pd.crosstab(
                    vendas_df['NIVEL'], vendas_df['REGIAO'])

                fig_heatmap = px.imshow(
                    modalidades_regiao.values,
                    x=modalidades_regiao.columns,
                    y=modalidades_regiao.index,
                    color_continuous_scale='Viridis',
                    title='Distribuição de Modalidades por Região',
                    text_auto=True
                )

                fig_heatmap.update_layout(height=400)

                st.plotly_chart(fig_heatmap, use_container_width=True)

        with col2:
            # Modalidade dominante por estado
            if 'UF' in vendas_df.columns:
                st.markdown("#### 🏆 Modalidade Dominante por Estado")

                modalidades_estado = vendas_df.groupby(
                    ['UF', 'NIVEL']).size().reset_index(name='Vendas')
                modalidade_dominante = modalidades_estado.loc[modalidades_estado.groupby('UF')[
                    'Vendas'].idxmax()]

                # Top 10 estados
                top_estados = vendas_df['UF'].value_counts().head(10).index
                modalidade_dominante = modalidade_dominante[modalidade_dominante['UF'].isin(
                    top_estados)]

                fig_modal_estado = px.bar(
                    modalidade_dominante,
                    x='UF',
                    y='Vendas',
                    color='NIVEL',
                    title='Modalidade Dominante por Estado (Top 10)',
                    text='Vendas'
                )

                fig_modal_estado.update_traces(textposition='outside')
                fig_modal_estado.update_layout(height=400)

                st.plotly_chart(fig_modal_estado, use_container_width=True)

    def _render_partnerships_by_location(self, vendas_df):
        """Renderiza análise de parcerias por localização"""
        st.subheader("🤝 Parcerias por Localização")

        if 'TIPO_PARCERIA' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados de parcerias não disponíveis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Distribuição de parcerias por região
            if 'REGIAO' in vendas_df.columns:
                st.markdown("#### 🌎 Parcerias por Região")

                parcerias_regiao = pd.crosstab(
                    vendas_df['REGIAO'], vendas_df['TIPO_PARCERIA'], normalize='index') * 100

                fig_parceria_regiao = px.bar(
                    parcerias_regiao.reset_index(),
                    x='REGIAO',
                    y=parcerias_regiao.columns.tolist(),
                    title='Distribuição de Parcerias por Região (%)',
                    barmode='stack'
                )

                fig_parceria_regiao.update_layout(height=400)

                st.plotly_chart(fig_parceria_regiao, use_container_width=True)

        with col2:
            # Top estados por tipo de parceria
            st.markdown("#### 🏆 Top Estados por Tipo de Parceria")

            tipo_parceria_selecionado = st.selectbox(
                "Selecione o tipo de parceria:",
                vendas_df['TIPO_PARCERIA'].unique(),
                key="parceria_estado_select"
            )

            if tipo_parceria_selecionado:
                vendas_parceria = vendas_df[vendas_df['TIPO_PARCERIA']
                                            == tipo_parceria_selecionado]

                if 'UF' in vendas_parceria.columns:
                    top_estados_parceria = vendas_parceria['UF'].value_counts().head(
                        10)

                    fig_estados_parceria = px.bar(
                        x=top_estados_parceria.values,
                        y=top_estados_parceria.index,
                        orientation='h',
                        title=f'Top 10 Estados - {tipo_parceria_selecionado}',
                        color=top_estados_parceria.values,
                        color_continuous_scale='Blues'
                    )

                    fig_estados_parceria.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        height=400,
                        showlegend=False
                    )

                    st.plotly_chart(fig_estados_parceria,
                                    use_container_width=True)

    def _render_geographic_distribution_map(self, vendas_df, polos_df):
        """Renderiza mapa de distribuição geográfica"""
        st.subheader("🗺️ Mapa de Distribuição Geográfica")

        if vendas_df.empty:
            st.warning("Dados de vendas não disponíveis para o mapa.")
            return

        try:
            # Criar dados agregados por estado
            vendas_por_estado = vendas_df['UF'].value_counts().reset_index()
            vendas_por_estado.columns = ['UF', 'Total_Vendas']

            # Criar mapa coroplético do Brasil (simulado com dados disponíveis)
            fig_map = px.scatter_geo(
                vendas_por_estado,
                locations='UF',
                size='Total_Vendas',
                hover_name='UF',
                hover_data={'Total_Vendas': True},
                title='Distribuição de Vendas por Estado',
                size_max=50,
                projection='natural earth',
                locationmode='geojson-id'
            )

            fig_map.update_geos(
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular'
            )

            fig_map.update_layout(height=600)

            st.plotly_chart(fig_map, use_container_width=True)

        except Exception as e:
            st.info("Mapa geográfico não disponível. Exibindo dados em tabela.")

            # Fallback: mostrar dados em tabela
            vendas_por_estado = vendas_df['UF'].value_counts().reset_index()
            vendas_por_estado.columns = ['Estado (UF)', 'Total de Vendas']
            vendas_por_estado['Percentual'] = (
                vendas_por_estado['Total de Vendas'] / len(vendas_df) * 100).round(2)

            st.dataframe(vendas_por_estado,
                         use_container_width=True, hide_index=True)
