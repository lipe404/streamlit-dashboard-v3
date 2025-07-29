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
            if 'ANO' in vendas_df.columns:
                col5, col6, col7, col8 = st.columns(4)

                with col5:
                    anos_ativos = vendas_df['ANO'].nunique()
                    st.metric("Anos com Vendas", anos_ativos)

                with col6:
                    if 'MES_ANO' in vendas_df.columns:
                        meses_ativos = vendas_df['MES_ANO'].nunique()
                        st.metric("Meses com Vendas", meses_ativos)

                with col7:
                    vendas_mes_atual = len(
                        vendas_df[vendas_df['ANO'] == vendas_df['ANO'].max()])
                    st.metric("Vendas Ano Atual", vendas_mes_atual)

                with col8:
                    if len(vendas_df) > 0:
                        media_vendas_mes = len(
                            vendas_df) / vendas_df['MES_ANO'].nunique() if 'MES_ANO' in vendas_df.columns else 0
                        st.metric("Média Vendas/Mês",
                                  f"{media_vendas_mes:.1f}")

        except Exception as e:
            st.error(f"Erro ao calcular métricas: {str(e)}")

    def _render_partnership_analysis(self, vendas_df):
        """Renderiza análise de parcerias"""
        st.subheader("🤝 Análise por Tipo de Parceria")

        if 'TIPO_PARCERIA' not in vendas_df.columns:
            st.warning("Dados de tipo de parceria não disponíveis.")
            return

        col1, col2 = st.columns([1, 2])

        with col1:
            # Filtro de parcerias
            st.subheader("🔍 Filtros")
            parcerias_disponiveis = sorted(vendas_df['TIPO_PARCERIA'].unique())
            parcerias_selecionadas = st.multiselect(
                "Selecione tipos de parceria:",
                parcerias_disponiveis,
                default=parcerias_disponiveis,
                help="Escolha quais tipos de parceria incluir na análise"
            )

            if parcerias_selecionadas:
                # Estatísticas das parcerias selecionadas
                vendas_filtradas = vendas_df[vendas_df['TIPO_PARCERIA'].isin(
                    parcerias_selecionadas)]

                st.subheader("📊 Estatísticas")
                for parceria in parcerias_selecionadas:
                    vendas_parceria = len(
                        vendas_df[vendas_df['TIPO_PARCERIA'] == parceria])
                    percentual = (vendas_parceria / len(vendas_df) * 100)
                    st.metric(
                        f"{parceria}",
                        f"{vendas_parceria:,}",
                        f"{percentual:.1f}% do total"
                    )

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

    def _render_temporal_analysis(self, vendas_df):
        """Renderiza análise temporal"""
        st.subheader("📈 Análise Temporal de Vendas")

        if 'MES_ANO' not in vendas_df.columns:
            st.warning("Dados temporais não disponíveis.")
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
            if agrupamento == "modalidade" and 'NIVEL' in vendas_df.columns:
                opcoes_filtro = sorted(vendas_df['NIVEL'].unique())
                filtros_selecionados = st.multiselect(
                    "Filtrar modalidades:",
                    opcoes_filtro,
                    default=opcoes_filtro[:5] if len(
                        opcoes_filtro) > 5 else opcoes_filtro
                )
            elif agrupamento == "parceria" and 'TIPO_PARCERIA' in vendas_df.columns:
                opcoes_filtro = sorted(vendas_df['TIPO_PARCERIA'].unique())
                filtros_selecionados = st.multiselect(
                    "Filtrar parcerias:",
                    opcoes_filtro,
                    default=opcoes_filtro
                )
            else:
                filtros_selecionados = None

        # Gráfico temporal
        try:
            fig_timeline = self.viz.create_sales_timeline_chart(
                vendas_df, agrupamento, filtros_selecionados
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico temporal: {str(e)}")

        # Análise de sazonalidade
        if 'MES_NOME' in vendas_df.columns:
            st.subheader("🌊 Análise de Sazonalidade")

            try:
                vendas_por_mes = vendas_df['MES_NOME'].value_counts()

                # Ordenar meses corretamente
                ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

                vendas_por_mes = vendas_por_mes.reindex(ordem_meses).fillna(0)

                fig_sazonalidade = px.bar(
                    x=vendas_por_mes.index,
                    y=vendas_por_mes.values,
                    title='Vendas por Mês (Sazonalidade)',
                    labels={'x': 'Mês', 'y': 'Número de Vendas'},
                    color=vendas_por_mes.values,
                    color_continuous_scale='Viridis'
                )

                fig_sazonalidade.update_layout(
                    xaxis=dict(tickangle=45),
                    height=400
                )

                st.plotly_chart(fig_sazonalidade, use_container_width=True)

                # Insights de sazonalidade
                mes_maior_venda = vendas_por_mes.idxmax()
                mes_menor_venda = vendas_por_mes.idxmin()

                col_insight1, col_insight2 = st.columns(2)
                with col_insight1:
                    st.success(
                        f"🔥 **Pico de vendas**: {mes_maior_venda} ({vendas_por_mes.max():,} vendas)")
                with col_insight2:
                    st.info(
                        f"📉 **Menor volume**: {mes_menor_venda} ({vendas_por_mes.min():,} vendas)")

            except Exception as e:
                st.error(f"Erro na análise de sazonalidade: {str(e)}")

    def _render_courses_modalities_analysis(self, vendas_df):
        """Renderiza análise de cursos e modalidades"""
        st.subheader("📚 Análise de Cursos e Modalidades")

        col1, col2 = st.columns(2)

        with col1:
            # Top cursos por parceria
            st.subheader("🏆 Top Cursos por Parceria")

            top_n_cursos = st.selectbox(
                "Número de cursos por parceria:",
                [5, 10, 15, 20],
                index=1,
                key="top_cursos"
            )

            try:
                fig_cursos_parceria = self.viz.create_top_courses_by_partnership_chart(
                    vendas_df, top_n_cursos
                )
                st.plotly_chart(fig_cursos_parceria, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de cursos: {str(e)}")

        with col2:
            # Modalidades por mês
            st.subheader("📅 Modalidades Mais Vendidas por Mês")

            try:
                fig_modalidades_mes = self.viz.create_modalities_by_month_chart(
                    vendas_df)
                st.plotly_chart(fig_modalidades_mes, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de modalidades: {str(e)}")

        # Análise detalhada de modalidades
        if 'NIVEL' in vendas_df.columns:
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

    def _render_comparative_analysis(self, vendas_df):
        """Renderiza análise comparativa"""
        st.subheader("⚖️ Análise Comparativa")

        # Controles de comparação
        col_comp1, col_comp2, col_comp3 = st.columns(3)

        with col_comp1:
            tipo_comparacao = st.selectbox(
                "Tipo de comparação:",
                ["meses", "parcerias", "modalidades"],
                help="Escolha o que deseja comparar"
            )

        # Definir opções baseadas no tipo
        if tipo_comparacao == "meses" and 'MES_NOME' in vendas_df.columns:
            opcoes = sorted(vendas_df['MES_NOME'].unique())
        elif tipo_comparacao == "parcerias" and 'TIPO_PARCERIA' in vendas_df.columns:
            opcoes = sorted(vendas_df['TIPO_PARCERIA'].unique())
        elif tipo_comparacao == "modalidades" and 'NIVEL' in vendas_df.columns:
            opcoes = sorted(vendas_df['NIVEL'].unique())
        else:
            opcoes = []

        if len(opcoes) >= 2:
            with col_comp2:
                periodo1 = st.selectbox(
                    f"Primeiro {tipo_comparacao[:-1]}:",
                    opcoes,
                    key="periodo1"
                )

            with col_comp3:
                opcoes_periodo2 = [opt for opt in opcoes if opt != periodo1]
                periodo2 = st.selectbox(
                    f"Segundo {tipo_comparacao[:-1]}:",
                    opcoes_periodo2,
                    key="periodo2"
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
        else:
            st.info(
                f"Dados insuficientes para comparação de {tipo_comparacao}.")

    def _display_comparison_insights(self, vendas_df, tipo_comparacao, periodo1, periodo2):
        """Exibe insights da comparação"""
        try:
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

        comparison_options = {
            "Entre Tipos de Parceria": "tipos_parceria",
            "Mesmo Mês em Anos Diferentes": "mesmo_mes_anos_diferentes"
        }

        selected_comparison_type_label = st.selectbox(
            "Escolha o tipo de comparação:",
            list(comparison_options.keys()),
            key="detailed_comp_type_select"  # Chave única para o selectbox
        )

        comparison_key = comparison_options[selected_comparison_type_label]

        item1 = None
        item2 = None

        if comparison_key == "parceiros_especificos":
            # Usar 'ALUNO' como proxy para parceiros/clientes específicos
            available_partners = sorted(
                vendas_df['ALUNO'].dropna().unique().tolist())
            if len(available_partners) < 2:
                st.info(
                    "Dados insuficientes para comparar parceiros específicos (pelo menos 2 alunos únicos necessários).")
                return
            col1, col2 = st.columns(2)
            with col1:
                item1 = st.selectbox("Selecione o primeiro aluno/parceiro:",
                                     available_partners, key="partner1_comp_select")
            with col2:
                item2 = st.selectbox("Selecione o segundo aluno/parceiro:", [
                                     p for p in available_partners if p != item1], key="partner2_comp_select")

        elif comparison_key == "tipos_parceria":
            available_types = sorted(
                vendas_df['TIPO_PARCERIA'].dropna().unique().tolist())
            if len(available_types) < 2:
                st.info(
                    "Dados insuficientes para comparar tipos de parceria (pelo menos 2 tipos de parceria únicos necessários).")
                return
            col1, col2 = st.columns(2)
            with col1:
                item1 = st.selectbox(
                    "Selecione o primeiro tipo:", available_types, key="type1_comp_select")
            with col2:
                item2 = st.selectbox("Selecione o segundo tipo:", [
                                     t for t in available_types if t != item1], key="type2_comp_select")

        elif comparison_key == "mesmo_mes_anos_diferentes":
            # Obter meses únicos (ex: 'Janeiro', 'Fevereiro')
            available_months = sorted(
                vendas_df['MES_NOME'].dropna().unique().tolist())
            if not available_months:
                st.info("Nenhum mês disponível para comparação de anos.")
                return

            selected_month = st.selectbox(
                "Selecione o mês para comparar:", available_months, key="month_for_year_comp_select")

            # Obter anos disponíveis para o mês selecionado
            available_years_for_month = sorted(
                vendas_df[vendas_df['MES_NOME'] == selected_month]['ANO'].dropna().unique().astype(int).tolist())

            if len(available_years_for_month) < 2:
                st.info(
                    f"Dados insuficientes para comparar anos no mês de {selected_month} (pelo menos 2 anos com dados neste mês necessários).")
                return

            col1, col2 = st.columns(2)
            with col1:
                year1 = st.selectbox(
                    f"Selecione o primeiro ano para {selected_month}:", available_years_for_month, key="year1_comp_select")
            with col2:
                # Filtrar para garantir que o segundo ano não seja o mesmo que o primeiro
                years_for_second_select = [
                    y for y in available_years_for_month if y != year1]
                if not years_for_second_select:  # Caso só haja um ano
                    st.warning("Não há outro ano para comparar neste mês.")
                    return
                year2 = st.selectbox(
                    f"Selecione o segundo ano para {selected_month}:", years_for_second_select, key="year2_comp_select")

            # Formato para passar para o visualizations
            item1 = f"{selected_month} - {year1}"
            item2 = f"{selected_month} - {year2}"

        # Renderizar gráfico se os itens forem selecionados
        if item1 and item2:
            try:
                fig = self.viz.create_detailed_sales_comparison_timeline(
                    vendas_df, comparison_key, item1, item2)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(
                    f"Erro ao gerar o gráfico de comparação detalhada: {str(e)}")
                st.exception(e)  # Para ver o stack trace completo
        else:
            st.info("Selecione os itens para realizar a comparação detalhada.")
