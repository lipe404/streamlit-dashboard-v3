import streamlit as st
import pandas as pd
import plotly.express as px
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

        # Análise por Região (Nova seção)
        self._render_regional_analysis(alunos_df)

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
                    title='Distribuição de Alunos por Região',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
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

                if not cursos_uf.empty:
                    fig_cursos_uf = px.bar(
                        x=cursos_uf.values,
                        y=cursos_uf.index,
                        orientation='h',
                        title=f'Top 10 Cursos em {uf_selecionada}',
                        color=cursos_uf.values,
                        color_continuous_scale='Plasma'
                    )
                    fig_cursos_uf.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        xaxis_title='Número de Alunos',
                        yaxis_title='Curso'
                    )
                    st.plotly_chart(fig_cursos_uf, use_container_width=True)
                else:
                    st.info(f"Nenhum curso encontrado para {uf_selecionada}")

    def _render_regional_analysis(self, alunos_df):
        """Renderiza análise por região (substitui o mapa de densidade)"""
        st.subheader("🌍 Cursos Mais Demandados por Região do Brasil")

        if 'REGIAO' not in alunos_df.columns or 'CURSO' not in alunos_df.columns:
            st.warning(
                "Dados de região ou curso não disponíveis para esta análise.")
            return

        # Controles para a análise regional
        col_control1, col_control2 = st.columns(2)

        with col_control1:
            top_cursos = st.selectbox(
                "Número de cursos por região:",
                [5, 10, 15, 20],
                index=1,
                help="Selecione quantos cursos mostrar por região"
            )

        with col_control2:
            visualization_type = st.selectbox(
                "Tipo de visualização:",
                ["Gráfico de Barras", "Heatmap", "Tabela Resumo"],
                help="Escolha como visualizar os dados"
            )

        # Renderizar visualização baseada na seleção
        if visualization_type == "Gráfico de Barras":
            try:
                fig_cursos_regiao = self.viz.create_courses_by_region_chart(
                    alunos_df, top_cursos)
                st.plotly_chart(fig_cursos_regiao, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de barras: {str(e)}")

        elif visualization_type == "Heatmap":
            try:
                fig_heatmap = self.viz.create_courses_by_region_heatmap(
                    alunos_df, top_cursos)
                st.plotly_chart(fig_heatmap, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar heatmap: {str(e)}")

        elif visualization_type == "Tabela Resumo":
            try:
                resumo_regional = self.viz.create_regional_course_summary(
                    alunos_df)

                if not resumo_regional.empty:
                    st.subheader("📋 Resumo por Região")

                    # Renomear colunas para exibição
                    resumo_display = resumo_regional.copy()
                    resumo_display.columns = [
                        'Região', 'Total Matrículas', 'Cursos Distintos',
                        'Alunos Únicos', 'Curso Mais Popular',
                        'Alunos no Curso Popular', 'Média Alunos/Curso'
                    ]

                    st.dataframe(
                        resumo_display,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Métricas de destaque
                    if len(resumo_regional) > 0:
                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                        with col_m1:
                            total_matriculas = resumo_regional['Total_Matriculas'].sum(
                            )
                            st.metric("Total de Matrículas",
                                      f"{total_matriculas:,.0f}")

                        with col_m2:
                            total_cursos = resumo_regional['Cursos_Distintos'].sum(
                            )
                            st.metric("Total de Cursos", f"{total_cursos:.0f}")

                        with col_m3:
                            regiao_mais_ativa = resumo_regional.iloc[0]['REGIAO']
                            st.metric("Região Mais Ativa", regiao_mais_ativa)

                        with col_m4:
                            media_geral = resumo_regional['Media_Alunos_por_Curso'].mean(
                            )
                            st.metric("Média Geral Alunos/Curso",
                                      f"{media_geral:.1f}")

                else:
                    st.info("Nenhum dado disponível para o resumo regional.")

            except Exception as e:
                st.error(f"Erro ao gerar tabela resumo: {str(e)}")

        # Análise adicional: Curso mais popular geral
        self._render_popular_courses_analysis(alunos_df)

    def _render_popular_courses_analysis(self, alunos_df):
        """Renderiza análise dos cursos mais populares"""
        st.subheader("🏆 Análise dos Cursos Mais Populares")

        try:
            if 'CURSO' in alunos_df.columns and 'REGIAO' in alunos_df.columns:
                # Top 5 cursos gerais
                top_cursos_gerais = alunos_df['CURSO'].value_counts().head(5)

                col_pop1, col_pop2 = st.columns(2)

                with col_pop1:
                    # Gráfico dos top 5 cursos
                    fig_top5 = px.bar(
                        x=top_cursos_gerais.values,
                        y=top_cursos_gerais.index,
                        orientation='h',
                        title='Top 5 Cursos Mais Populares (Geral)',
                        color=top_cursos_gerais.values,
                        color_continuous_scale='Viridis'
                    )
                    fig_top5.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        xaxis_title='Número de Alunos',
                        yaxis_title='Curso'
                    )
                    st.plotly_chart(fig_top5, use_container_width=True)

                with col_pop2:
                    # Análise regional do curso mais popular
                    curso_mais_popular = top_cursos_gerais.index[0]
                    alunos_curso_popular = alunos_df[alunos_df['CURSO']
                                                     == curso_mais_popular]

                    if not alunos_curso_popular.empty:
                        distribuicao_regional = alunos_curso_popular['REGIAO'].value_counts(
                        )

                        fig_regional_popular = px.pie(
                            values=distribuicao_regional.values,
                            names=distribuicao_regional.index,
                            title=f'Distribuição Regional: {curso_mais_popular}',
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_regional_popular,
                                        use_container_width=True)

        except Exception as e:
            st.error(f"Erro na análise de cursos populares: {str(e)}")
