import streamlit as st
import pandas as pd
import plotly.express as px
from . import BasePage
from typing import List


class VendasAnalysis(BasePage):
    """Página de análise de vendas"""

    def render(self, vendas_df):
        st.markdown('<h2 class="section-header">💰 Análise de Vendas</h2>',
                    unsafe_allow_html=True)

        if not self.check_data_availability(vendas_df, "vendas"):
            return

        # Métricas principais
        self._display_sales_metrics(vendas_df)

        # Análise de parcerias
        self._render_partnership_analysis(vendas_df)

        # Análise temporal
        self._render_temporal_analysis(vendas_df)

        # Análise de cursos e modalidades
        self._render_courses_modalities_analysis(vendas_df)

        # Análise comparativa (barras)
        self._render_comparative_analysis(vendas_df)

        # Análise Comparativa Detalhada (linhas)
        self._render_detailed_comparative_analysis(vendas_df)

    def _display_sales_metrics(self, vendas_df):
        """Exibe métricas principais de vendas"""
        try:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_vendas = len(vendas_df)
                st.metric("Total de Vendas", f"{total_vendas:,}")

            with col2:
                if 'TIPO_PARCERIA' in vendas_df.columns:
                    tipos_parceria = vendas_df['TIPO_PARCERIA'].nunique()
                    st.metric("Tipos de Parceria", tipos_parceria)

            with col3:
                if 'NIVEL' in vendas_df.columns:
                    modalidades = vendas_df['NIVEL'].nunique()
                    st.metric("Modalidades", modalidades)

            with col4:
                if 'CURSO' in vendas_df.columns:
                    cursos_unicos = vendas_df['CURSO'].nunique()
                    st.metric("Cursos Únicos", cursos_unicos)

            # Métricas adicionais
            if 'ANO' in vendas_df.columns and not vendas_df.empty:  # Adicionado 'and not vendas_df.empty'
                col5, col6, col7, col8 = st.columns(4)

                with col5:
                    anos_ativos = vendas_df['ANO'].nunique()
                    st.metric("Anos com Vendas", anos_ativos)

                with col6:
                    if 'MES_ANO' in vendas_df.columns:
                        meses_ativos = vendas_df['MES_ANO'].nunique()
                        st.metric("Meses com Vendas", meses_ativos)

                with col7:
                    # Vendas no ano mais recente presente nos dados
                    ano_mais_recente = vendas_df['ANO'].max()
                    vendas_ano_recente = len(
                        vendas_df[vendas_df['ANO'] == ano_mais_recente])
                    st.metric(f"Vendas em {ano_mais_recente}",
                              f"{vendas_ano_recente:,}")

                with col8:
                    if 'MES_ANO' in vendas_df.columns and vendas_df['MES_ANO'].nunique() > 0:
                        media_vendas_mes = len(
                            vendas_df) / vendas_df['MES_ANO'].nunique()
                        st.metric("Média Vendas/Mês",
                                  f"{media_vendas_mes:.1f}")
                    else:
                        st.metric("Média Vendas/Mês", "N/A")

        except Exception as e:
            st.error(f"Erro ao calcular métricas: {str(e)}")

    def _render_partnership_analysis(self, vendas_df):
        """Renderiza análise de parcerias"""
        st.subheader("🤝 Análise por Tipo de Parceria")

        if 'TIPO_PARCERIA' not in vendas_df.columns or vendas_df.empty:
            st.warning(
                "Dados de tipo de parceria não disponíveis ou DataFrame vazio.")
            return

        col1, col2 = st.columns([1, 2])

        with col1:
            # Filtro de parcerias
            st.subheader("🔍 Filtros")
            parcerias_disponiveis = sorted(
                vendas_df['TIPO_PARCERIA'].dropna().unique())
            parcerias_selecionadas = st.multiselect(
                "Selecione tipos de parceria:",
                parcerias_disponiveis,
                default=parcerias_disponiveis,
                help="Escolha quais tipos de parceria incluir na análise"
            )

            if parcerias_selecionadas:
                # Estatísticas das parcerias selecionadas
                vendas_filtradas_parceria = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                    parcerias_selecionadas)]

                st.subheader("📊 Estatísticas")
                for parceria in parcerias_selecionadas:
                    vendas_parceria = len(
                        vendas_df[vendas_df['TIPO_PARCERIA'] == parceria])
                    if vendas_parceria > 0:
                        percentual = (vendas_parceria / len(vendas_df) * 100)
                        st.metric(
                            f"{parceria}",
                            f"{vendas_parceria:,}",
                            f"{percentual:.1f}% do total"
                        )
                    else:
                        st.metric(f"{parceria}", "0", "0.0%")
            else:
                st.info("Nenhuma parceria selecionada.")

        with col2:
            # Gráfico de pizza
            if parcerias_selecionadas:
                try:
                    fig_parceria = self.viz.create_sales_partnership_pie(
                        vendas_df, parcerias_selecionadas
                    )
                    st.plotly_chart(fig_parceria, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico de parcerias: {str(e)}")
            else:
                st.info("Selecione uma ou mais parcerias para visualizar o gráfico.")

    def _render_temporal_analysis(self, vendas_df):
        """Renderiza análise temporal"""
        st.subheader("📈 Análise Temporal de Vendas")

        if 'MES_ANO' not in vendas_df.columns or vendas_df.empty:
            st.warning("Dados temporais não disponíveis ou DataFrame vazio.")
            return

        # Controles
        col_control1, col_control2 = st.columns(2)

        with col_control1:
            agrupamento = st.selectbox(
                "Agrupar por:",
                ["modalidade", "parceria"],
                help="Escolha como agrupar as linhas do gráfico"
            )

        with col_control2:
            # Filtros baseados no agrupamento
            filtros_selecionados = []
            if agrupamento == "modalidade" and 'NIVEL' in vendas_df.columns:
                opcoes_filtro = sorted(vendas_df['NIVEL'].dropna().unique())
                filtros_selecionados = st.multiselect(
                    "Filtrar modalidades:",
                    opcoes_filtro,
                    default=opcoes_filtro[:5] if len(
                        opcoes_filtro) > 5 else opcoes_filtro
                )
            elif agrupamento == "parceria" and 'TIPO_PARCERIA' in vendas_df.columns:
                opcoes_filtro = sorted(
                    vendas_df['TIPO_PARCERIA'].dropna().unique())
                filtros_selecionados = st.multiselect(
                    "Filtrar parcerias:",
                    opcoes_filtro,
                    default=opcoes_filtro
                )

        if not filtros_selecionados:
            st.info("Selecione pelo menos um filtro para o gráfico temporal.")
            return

        # Gráfico temporal
        try:
            fig_timeline = self.viz.create_sales_timeline_chart(
                vendas_df, agrupamento, filtros_selecionados
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico temporal: {str(e)}")

        # Análise de sazonalidade
        if 'MES_NOME' in vendas_df.columns and not vendas_df.empty:
            st.subheader("🌊 Análise de Sazonalidade")

            try:
                # É importante usar MES_ANO para a contagem e depois MES_NOME para exibição
                vendas_por_mes_series = vendas_df.groupby('MES_NOME').size()

                # Ordenar meses corretamente
                ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

                vendas_por_mes_reindexado = vendas_por_mes_series.reindex(
                    ordem_meses, fill_value=0)

                vendas_por_mes_ord = vendas_por_mes_reindexado.reset_index()
                vendas_por_mes_ord.columns = ['MES_NOME', 'Vendas']

                vendas_por_mes_ord['MES_NOME'] = pd.Categorical(
                    vendas_por_mes_ord['MES_NOME'],
                    categories=ordem_meses,
                    ordered=True
                )

                fig_sazonalidade = px.bar(
                    vendas_por_mes_ord,
                    x='MES_NOME',
                    y='Vendas',
                    title='Vendas por Mês (Sazonalidade)',
                    labels={'MES_NOME': 'Mês', 'Vendas': 'Número de Vendas'},
                    color='Vendas',
                    color_continuous_scale='Viridis'
                )

                fig_sazonalidade.update_layout(
                    xaxis=dict(tickangle=45),
                    height=400
                )

                st.plotly_chart(fig_sazonalidade, use_container_width=True)

                # Insights de sazonalidade
                if not vendas_por_mes_ord.empty:
                    mes_maior_venda = vendas_por_mes_ord.loc[vendas_por_mes_ord['Vendas'].idxmax(
                    )]['MES_NOME']
                    mes_menor_venda = vendas_por_mes_ord.loc[vendas_por_mes_ord['Vendas'].idxmin(
                    )]['MES_NOME']

                    col_insight1, col_insight2 = st.columns(2)
                    with col_insight1:
                        st.success(
                            f"🔥 **Pico de vendas**: {mes_maior_venda} ({vendas_por_mes_ord['Vendas'].max():,} vendas)")
                    with col_insight2:
                        st.info(
                            f"📉 **Menor volume**: {mes_menor_venda} ({vendas_por_mes_ord['Vendas'].min():,} vendas)")
                else:
                    st.info("Dados insuficientes para análise de sazonalidade.")

            except Exception as e:
                st.error(f"Erro na análise de sazonalidade: {str(e)}")

    def _render_courses_modalities_analysis(self, vendas_df):
        """Renderiza análise de cursos e modalidades"""
        st.subheader("📚 Análise de Cursos e Modalidades")

        if vendas_df.empty:
            st.warning(
                "Dados de vendas não disponíveis para análise de cursos e modalidades.")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Top cursos por parceria
            st.subheader("🏆 Top Cursos por Parceria")

            top_n_cursos = st.selectbox(
                "Número de cursos por parceria:",
                [5, 10, 15, 20],
                index=1,
                key="top_cursos_parceria_select"  # Adicionado key única
            )

            try:
                fig_cursos_parceria = self.viz.create_top_courses_by_partnership_chart(
                    vendas_df, top_n_cursos
                )
                st.plotly_chart(fig_cursos_parceria, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar gráfico de top cursos por parceria: {str(e)}")

        with col2:
            # Modalidades por mês
            st.subheader("📅 Modalidades Mais Vendidas por Mês")

            try:
                fig_modalidades_mes = self.viz.create_modalities_by_month_chart(
                    vendas_df)
                st.plotly_chart(fig_modalidades_mes, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar gráfico de modalidades por mês: {str(e)}")

        # Análise detalhada de modalidades
        if 'NIVEL' in vendas_df.columns and not vendas_df.empty:  # Adicionado 'and not vendas_df.empty'
            st.subheader("📋 Ranking de Modalidades")

            modalidades_ranking = vendas_df['NIVEL'].value_counts(
            ).reset_index()
            modalidades_ranking.columns = ['Modalidade', 'Vendas']
            modalidades_ranking['Percentual'] = (
                modalidades_ranking['Vendas'] / modalidades_ranking['Vendas'].sum() * 100).round(1)
            modalidades_ranking['Ranking'] = range(
                1, len(modalidades_ranking) + 1)

            # Reordenar colunas
            modalidades_ranking = modalidades_ranking[[
                'Ranking', 'Modalidade', 'Vendas', 'Percentual']]

            st.dataframe(
                modalidades_ranking,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Dados de modalidades não disponíveis para ranking.")

        # --- NOVOS GRÁFICOS SOLICITADOS ---
        st.markdown("---")  # Separador visual

        # Inicializa as variáveis com um valor padrão para garantir que sempre existam.
        # Caso as condições IFs abaixo sejam FALSAS, estas variáveis ainda estarão definidas.
        # Valor padrão (ex: o do index=1 do selectbox)
        top_n_modalidades_parceiro = 5
        # Valor padrão (ex: o do index=1 do selectbox)
        top_n_modalidades_mensal = 3

        # 1. Top Modalidades Mais Vendidas por Tipo de Parceiro
        st.subheader("🏆 Top Modalidades por Tipo de Parceiro")
        if 'NIVEL' in vendas_df.columns and 'TIPO_PARCERIA' in vendas_df.columns and not vendas_df.empty:
            top_n_modalidades_parceiro = st.selectbox(
                "Número de modalidades por tipo de parceiro:",
                [3, 5, 10],
                index=1,
                key="top_modalidades_parceiro_select"
            )
            try:
                fig_top_modal_parceiro = self.viz.create_top_modalities_by_partnership_chart(
                    vendas_df, top_n_modalidades_parceiro
                )
                st.plotly_chart(fig_top_modal_parceiro,
                                use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar gráfico de top modalidades por parceiro: {str(e)}")
        else:
            st.info(
                "Dados de modalidades ou tipo de parceiro não disponíveis para esta análise.")

        st.markdown("---")  # Separador visual

        # 2. Top Modalidades Vendidas Mês a Mês por Cada Tipo de Parceiro
        st.subheader("📈 Evolução Mensal das Modalidades por Parceiro")
        if 'MES_ANO' in vendas_df.columns and 'NIVEL' in vendas_df.columns and 'TIPO_PARCERIA' in vendas_df.columns and not vendas_df.empty:
            top_n_modalidades_mensal = st.selectbox(
                "Número de modalidades para evolução mensal:",
                [2, 3, 5],
                index=1,
                key="top_modalidades_mensal_select"
            )
            try:
                fig_modalidades_mensal_parceiro = self.viz.create_modalities_monthly_by_partnership_chart(
                    vendas_df, top_n_modalidades_mensal
                )
                st.plotly_chart(fig_modalidades_mensal_parceiro,
                                use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar gráfico de evolução mensal de modalidades por parceiro: {str(e)}")
        else:
            st.info(
                "Dados temporais, de modalidades ou tipo de parceiro não disponíveis para esta análise.")

    def _render_comparative_analysis(self, vendas_df):
        """Renderiza análise comparativa (gráficos de barras)"""
        st.subheader(
            "⚖️ Análise Comparativa (Barras)")  # Renomeado para clareza

        if vendas_df.empty:
            st.warning(
                "Dados de vendas não disponíveis para análise comparativa.")
            return

        # Controles de comparação
        col_comp1, col_comp2, col_comp3 = st.columns(3)

        with col_comp1:
            tipo_comparacao = st.selectbox(
                "Tipo de comparação:",
                ["meses", "parcerias", "modalidades"],
                key="tipo_comparacao_select",  # Adicionado key única
                help="Escolha o que deseja comparar"
            )

        # Definir opções baseadas no tipo
        opcoes = []
        if tipo_comparacao == "meses" and 'MES_NOME' in vendas_df.columns:
            opcoes = sorted(vendas_df['MES_NOME'].dropna().unique())
        elif tipo_comparacao == "parcerias" and 'TIPO_PARCERIA' in vendas_df.columns:
            opcoes = sorted(vendas_df['TIPO_PARCERIA'].dropna().unique())
        elif tipo_comparacao == "modalidades" and 'NIVEL' in vendas_df.columns:
            opcoes = sorted(vendas_df['NIVEL'].dropna().unique())

        if len(opcoes) < 2:
            st.info(
                f"Dados insuficientes para comparação de {tipo_comparacao}.")
            return

        with col_comp2:
            periodo1 = st.selectbox(
                f"Primeiro {'mês' if tipo_comparacao == 'meses' else 'parceria' if tipo_comparacao == 'parcerias' else 'modalidade'}:",
                opcoes,
                key="periodo1_select"  # Adicionado key única
            )

        with col_comp3:
            opcoes_periodo2 = [opt for opt in opcoes if opt != periodo1]
            if not opcoes_periodo2:
                st.info(
                    f"Não há segundo {tipo_comparacao[:-1]} disponível para comparação.")
                return

            periodo2 = st.selectbox(
                f"Segundo {'mês' if tipo_comparacao == 'meses' else 'parceria' if tipo_comparacao == 'parcerias' else 'modalidade'}:",
                opcoes_periodo2,
                key="periodo2_select"  # Adicionado key única
            )

        # Gerar comparação
        if periodo1 and periodo2:
            try:
                fig_comparacao = self.viz.create_sales_comparison_chart(
                    vendas_df, tipo_comparacao, periodo1, periodo2
                )
                st.plotly_chart(fig_comparacao, use_container_width=True)

                # Insights da comparação
                self._display_comparison_insights(
                    vendas_df, tipo_comparacao, periodo1, periodo2)

            except Exception as e:
                st.error(f"Erro ao gerar comparação: {str(e)}")

    def _display_comparison_insights(self, vendas_df: pd.DataFrame, tipo_comparacao: str, periodo1: str, periodo2: str):
        """Exibe insights da comparação"""
        try:
            vendas_p1 = 0
            vendas_p2 = 0

            if tipo_comparacao == "meses":
                vendas_p1 = len(vendas_df[vendas_df['MES_NOME'] == periodo1])
                vendas_p2 = len(vendas_df[vendas_df['MES_NOME'] == periodo2])
            elif tipo_comparacao == "parcerias":
                vendas_p1 = len(
                    vendas_df[vendas_df['TIPO_PARCERIA'] == periodo1])
                vendas_p2 = len(
                    vendas_df[vendas_df['TIPO_PARCERIA'] == periodo2])
            else:  # modalidades
                vendas_p1 = len(vendas_df[vendas_df['NIVEL'] == periodo1])
                vendas_p2 = len(vendas_df[vendas_df['NIVEL'] == periodo2])

            # Calcular diferença
            diferenca = vendas_p1 - vendas_p2
            percentual = (diferenca / vendas_p2 * 100) if vendas_p2 > 0 else 0

            # Exibir insights
            col_insight1, col_insight2, col_insight3 = st.columns(3)

            with col_insight1:
                st.metric(f"Vendas - {periodo1}", f"{vendas_p1:,}")

            with col_insight2:
                st.metric(f"Vendas - {periodo2}", f"{vendas_p2:,}")

            with col_insight3:
                delta_color = "normal"
                if diferenca > 0:
                    delta_text = f"+{diferenca:,} ({percentual:+.1f}%)"
                    delta_color = "normal"
                elif diferenca < 0:
                    delta_text = f"{diferenca:,} ({percentual:.1f}%)"
                    delta_color = "inverse"
                else:
                    delta_text = "Sem diferença"

                st.metric("Diferença", delta_text)

        except Exception as e:
            st.warning(f"Não foi possível calcular insights: {str(e)}")

    def _render_detailed_comparative_analysis(self, vendas_df: pd.DataFrame):
        st.subheader("📊 Análise Comparativa Detalhada (Evolução em Linha)")

        if vendas_df.empty:
            st.warning(
                "Dados de vendas não disponíveis para análise detalhada de comparação.")
            return

        # NOVO: Filtro por Tipo de Parceria
        st.markdown("#### Filtrar por Tipo de Parceria")
        available_partnership_types = sorted(
            vendas_df['TIPO_PARCERIA'].dropna().unique().tolist())
        selected_partnership_types_filter = st.multiselect(
            "Selecione o(s) tipo(s) de parceria(s) a incluir:",
            available_partnership_types,
            default=available_partnership_types,  # Seleciona todos por padrão
            key="detailed_comp_partnership_filter"
        )

        # Filtrar o DataFrame de vendas com base na seleção
        if selected_partnership_types_filter:
            vendas_df_filtered_by_partnership = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                selected_partnership_types_filter)]
        else:
            st.info(
                "Nenhum tipo de parceria selecionado. Por favor, selecione para ver a análise.")
            return

        if vendas_df_filtered_by_partnership.empty:
            st.info("Nenhum dado encontrado para os tipos de parceria selecionados.")
            return

        st.markdown("---")  # Separador visual
        st.markdown("#### Selecione os Critérios de Comparação")

        comparison_options = {
            "Entre Tipos de Parceria": "tipos_parceria",
            "Mesmo Mês em Anos Diferentes": "mesmo_mes_anos_diferentes"
        }

        # Removendo "Entre Parceiros Específicos (por Aluno)" para evitar complexidade com o novo filtro de parceria
        # Se você quiser reintroduzi-lo, precisará de uma lógica mais complexa para combinar os filtros.
        # "Entre Parceiros Específicos (por Aluno)": "parceiros_especificos",

        selected_comparison_type_label = st.selectbox(
            "Escolha o tipo de comparação:",
            list(comparison_options.keys()),
            key="detailed_comp_type_select"  # Chave única para o selectbox
        )

        comparison_key = comparison_options[selected_comparison_type_label]

        item1 = None
        item2 = None
        show_cumulative_checkbox = False  # Initialize the variable

        # A lógica de seleção de item1 e item2 agora usa 'vendas_df_filtered_by_partnership'
        # e é adaptada aos tipos de comparação restantes.

        if comparison_key == "tipos_parceria":
            # Aqui, as opções para seleção de tipo de parceria já são os tipos filtrados
            available_types = sorted(
                vendas_df_filtered_by_partnership['TIPO_PARCERIA'].dropna().unique().tolist())

            if len(available_types) < 2:
                st.info(
                    "Dados insuficientes para comparar tipos de parceria (pelo menos 2 tipos de parceria únicos necessários no filtro acima).")
                return
            col1, col2 = st.columns(2)
            with col1:
                item1 = st.selectbox(
                    "Selecione o primeiro tipo:", available_types, key="type1_comp_select")
            with col2:
                item2 = st.selectbox("Selecione o segundo tipo:", [
                                     t for t in available_types if t != item1], key="type2_comp_select")

        elif comparison_key == "mesmo_mes_anos_diferentes":
            available_months = sorted(
                vendas_df_filtered_by_partnership['MES_NOME'].dropna().unique().tolist())
            if not available_months:
                st.info(
                    "Nenhum mês disponível para comparação de anos para os tipos de parceria selecionados.")
                return

            selected_month = st.selectbox(
                "Selecione o mês para comparar:", available_months, key="month_for_year_comp_select")

            available_years_for_month = sorted(
                vendas_df_filtered_by_partnership[vendas_df_filtered_by_partnership['MES_NOME'] == selected_month]['ANO'].dropna().unique().astype(int).tolist())

            if len(available_years_for_month) < 2:
                st.info(
                    f"Dados insuficientes para comparar anos no mês de {selected_month} (pelo menos 2 anos com dados neste mês e tipos de parceria selecionados necessários).")
                return

            col1, col2 = st.columns(2)
            with col1:
                year1 = st.selectbox(
                    f"Selecione o primeiro ano para {selected_month}:", available_years_for_month, key="year1_comp_select")
            with col2:
                years_for_second_select = [
                    y for y in available_years_for_month if y != year1]
                if not years_for_second_select:
                    st.warning("Não há outro ano para comparar neste mês.")
                    return
                year2 = st.selectbox(
                    f"Selecione o segundo ano para {selected_month}:", years_for_second_select, key="year2_comp_select")

            item1 = f"{selected_month} - {year1}"
            item2 = f"{selected_month} - {year2}"

            # NOVO: Checkbox for cumulative
            st.markdown("---")
            show_cumulative_checkbox = st.checkbox(
                "Ver evolução de vendas cumulativo", key="cumulative_sales_checkbox")

        # Renderizar gráfico se os itens forem selecionados
        if item1 and item2:
            try:
                # Passa o DataFrame JÁ FILTRADO pelo tipo de parceria
                # Pass the show_cumulative_checkbox state
                fig = self.viz.create_detailed_sales_comparison_timeline(
                    vendas_df_filtered_by_partnership, comparison_key, item1, item2, show_cumulative=show_cumulative_checkbox)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar o gráfico de comparação detalhada: {str(e)}")
                st.exception(e)  # Para ver o stack trace completo
        else:
            st.info(
                "Selecione os critérios de comparação acima para visualizar o gráfico.")
