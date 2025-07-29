import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from . import BasePage


class AlignmentAnalysis(BasePage):
    """Página de análise de alinhamento de polos"""

    def render(self, polos_df, municipios_df, alunos_df):
        st.markdown('<h2 class="section-header">🔄 Análise de Alinhamento de Polos</h2>',
                    unsafe_allow_html=True)

        if not (self.check_data_availability(alunos_df, "alunos") and
                'POLO' in alunos_df.columns and 'POLO_MAIS_PROXIMO' in alunos_df.columns):
            st.warning("Dados de alinhamento não disponíveis.")
            return

        # Análise de alinhamento
        self._render_alignment_analysis(alunos_df)

        # Diagrama Sankey
        self._render_sankey_diagram(alunos_df)

        # Matriz de migração
        self._render_migration_matrix(alunos_df)

        # Análise por UF
        self._render_uf_alignment_analysis(alunos_df)

        # Mapa de conexões
        self._render_connections_map(alunos_df, polos_df)

    def _render_alignment_analysis(self, alunos_df):
        """Renderiza análise básica de alinhamento"""
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚖️ Alinhamento Polo Atual vs Ideal")
            fig_alignment = self.viz.create_alignment_analysis(alunos_df)
            st.plotly_chart(fig_alignment, use_container_width=True)

        with col2:
            # Métricas de alinhamento
            alunos_df['ALINHADO'] = alunos_df['POLO'] == alunos_df['POLO_MAIS_PROXIMO']
            total_alunos = len(alunos_df)
            alinhados = alunos_df['ALINHADO'].sum()
            desalinhados = total_alunos - alinhados
            taxa_alinhamento = (alinhados / total_alunos) * \
                100 if total_alunos > 0 else 0

            st.metric("Total de Alunos", total_alunos)
            st.metric("Alunos Alinhados", alinhados)
            st.metric("Alunos Desalinhados", desalinhados)
            st.metric("Taxa de Alinhamento", f"{taxa_alinhamento:.1f}%")

    def _render_sankey_diagram(self, alunos_df):
        """Renderiza diagrama Sankey"""
        st.subheader("🌊 Fluxo de Realocação (Sankey)")
        fig_sankey = self.viz.create_sankey_diagram(alunos_df)
        if fig_sankey.data:
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("Não há dados suficientes para criar o diagrama de fluxo.")

    def _render_migration_matrix(self, alunos_df):
        """Renderiza matriz de migração"""
        st.subheader("📊 Matriz de Migração de Alunos")

        # Filtrar apenas desalinhados
        desalinhados_df = alunos_df[alunos_df['POLO']
                                    != alunos_df['POLO_MAIS_PROXIMO']]

        if not desalinhados_df.empty:
            # Criar matriz de migração
            matriz_migracao = pd.crosstab(
                desalinhados_df['POLO'],
                desalinhados_df['POLO_MAIS_PROXIMO'],
                margins=True
            )

            # Mostrar apenas os top polos para melhor visualização
            top_polos_origem = desalinhados_df['POLO'].value_counts().head(
                10).index
            top_polos_destino = desalinhados_df['POLO_MAIS_PROXIMO'].value_counts().head(
                10).index

            # Filtrar matriz
            polos_relevantes = list(
                set(top_polos_origem) | set(top_polos_destino))
            matriz_filtrada = matriz_migracao.loc[
                matriz_migracao.index.isin(polos_relevantes),
                matriz_migracao.columns.isin(polos_relevantes)
            ]

            if not matriz_filtrada.empty:
                fig_matriz = px.imshow(
                    matriz_filtrada.values,
                    x=matriz_filtrada.columns,
                    y=matriz_filtrada.index,
                    title='Matriz de Migração - Top Polos',
                    color_continuous_scale='Blues',
                    text_auto=True
                )
                fig_matriz.update_layout(
                    xaxis_title='Polo Ideal (Destino)',
                    yaxis_title='Polo Atual (Origem)'
                )
                st.plotly_chart(fig_matriz, use_container_width=True)

    def _render_uf_alignment_analysis(self, alunos_df):
        """Renderiza análise de alinhamento por UF"""
        st.subheader("📍 Desalinhamento por Estado")

        if 'UF' in alunos_df.columns:
            alunos_df['ALINHADO'] = alunos_df['POLO'] == alunos_df['POLO_MAIS_PROXIMO']

            desalinhamento_uf = alunos_df.groupby('UF').agg({
                'ALINHADO': ['count', 'sum']
            }).round(2)

            desalinhamento_uf.columns = ['Total_Alunos', 'Alinhados']
            desalinhamento_uf['Desalinhados'] = desalinhamento_uf['Total_Alunos'] - \
                desalinhamento_uf['Alinhados']
            desalinhamento_uf['Taxa_Alinhamento'] = (
                desalinhamento_uf['Alinhados'] / desalinhamento_uf['Total_Alunos']) * 100
            desalinhamento_uf = desalinhamento_uf.reset_index()

            col1, col2 = st.columns(2)

            with col1:
                fig_desalinhamento_uf = px.bar(
                    desalinhamento_uf,
                    x='UF',
                    y='Taxa_Alinhamento',
                    title='Taxa de Alinhamento por Estado',
                    color='Taxa_Alinhamento',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_desalinhamento_uf,
                                use_container_width=True)

            with col2:
                # Ranking de estados com maior potencial de otimização
                potencial_otimizacao = desalinhamento_uf.nlargest(
                    10, 'Desalinhados')

                fig_potencial = px.bar(
                    potencial_otimizacao,
                    x='Desalinhados',
                    y='UF',
                    orientation='h',
                    title='Estados com Maior Potencial de Otimização',
                    color='Desalinhados',
                    color_continuous_scale='Reds'
                )
                fig_potencial.update_layout(
                    yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_potencial, use_container_width=True)

            # Tabela detalhada
            st.subheader("📋 Resumo Detalhado por Estado")
            st.dataframe(desalinhamento_uf.round(2), use_container_width=True)

    def _render_connections_map(self, alunos_df, polos_df):
        """Renderiza mapa de conexões"""
        st.subheader("🗺️ Mapa de Conexões Aluno-Polo")

        if ('LAT' in alunos_df.columns and 'LNG' in alunos_df.columns and
                not polos_df.empty):

            # Criar mapa de conexões
            m = folium.Map(
                location=[self.map_config['center_lat'],
                          self.map_config['center_lon']],
                zoom_start=self.map_config['zoom']
            )

            # Adicionar polos
            for _, polo in polos_df.iterrows():
                try:
                    lat_val = polo.get('lat', None)
                    lng_val = polo.get('long', None)
                    if pd.notna(lat_val) and pd.notna(lng_val):
                        folium.Marker(
                            location=[float(lat_val), float(lng_val)],
                            popup=f"<b>{polo.get('UNIDADE', 'N/A')}</b>",
                            icon=folium.Icon(
                                color='blue', icon='graduation-cap', prefix='fa')
                        ).add_to(m)
                except:
                    continue

            # Adicionar conexões para uma amostra de alunos desalinhados
            desalinhados_df = alunos_df[alunos_df['POLO']
                                        != alunos_df['POLO_MAIS_PROXIMO']]

            if not desalinhados_df.empty and 'LAT' in desalinhados_df.columns and 'LNG' in desalinhados_df.columns:
                alunos_com_coord = desalinhados_df.dropna(
                    subset=['LAT', 'LNG'])
                if len(alunos_com_coord) > 0:
                    sample_size = min(100, len(alunos_com_coord))
                    alunos_desalinhados_sample = alunos_com_coord.sample(
                        sample_size, random_state=42)

                    for _, aluno in alunos_desalinhados_sample.iterrows():
                        try:
                            # Coordenadas do aluno
                            aluno_lat = float(aluno.get('LAT', 0))
                            aluno_lng = float(aluno.get('LNG', 0))

                            if aluno_lat != 0 and aluno_lng != 0:
                                # Encontrar coordenadas do polo atual e ideal
                                polo_atual_coords = polos_df[polos_df['UNIDADE'] == aluno.get(
                                    'POLO', '')]
                                polo_ideal_coords = polos_df[polos_df['UNIDADE'] == aluno.get(
                                    'POLO_MAIS_PROXIMO', '')]

                                if not polo_atual_coords.empty and not polo_ideal_coords.empty:
                                    try:
                                        polo_atual_lat = float(
                                            polo_atual_coords.iloc[0]['lat'])
                                        polo_atual_lng = float(
                                            polo_atual_coords.iloc[0]['long'])
                                        polo_ideal_lat = float(
                                            polo_ideal_coords.iloc[0]['lat'])
                                        polo_ideal_lng = float(
                                            polo_ideal_coords.iloc[0]['long'])

                                        # Linha vermelha: aluno -> polo atual
                                        folium.PolyLine(
                                            locations=[[aluno_lat, aluno_lng], [
                                                polo_atual_lat, polo_atual_lng]],
                                            color='red',
                                            weight=2,
                                            opacity=0.6
                                        ).add_to(m)

                                        # Linha verde: aluno -> polo ideal
                                        folium.PolyLine(
                                            locations=[[aluno_lat, aluno_lng], [
                                                polo_ideal_lat, polo_ideal_lng]],
                                            color='green',
                                            weight=2,
                                            opacity=0.6,
                                            dash_array='5, 5'
                                        ).add_to(m)
                                    except:
                                        continue
                        except:
                            continue

            # Adicionar legenda
            legend_html = '''
            <div style="position: fixed;
                       bottom: 50px; left: 50px; width: 200px; height: 80px;
                       background-color: white; border:2px solid grey; z-index:9999;
                       font-size:14px; padding: 10px">
            <p><b>Legenda:</b></p>
            <p><span style="color:red;">━━━</span> Polo Atual</p>
            <p><span style="color:green;">┅┅┅</span> Polo Ideal</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))

            st_folium(m, width=700, height=500)
        else:
            st.info(
                "Dados de coordenadas não disponíveis para criar o mapa de conexões.")
