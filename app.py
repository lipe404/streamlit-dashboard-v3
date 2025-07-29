from utils.visualizations import Visualizations
from utils.data_processor import DataProcessor
from utils.data_loader import GoogleSheetsLoader
from config import GOOGLE_SHEETS_CONFIG, COLORS, MAP_CONFIG
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore')

# Importar configurações e utilitários

# Configuração da página
st.set_page_config(
    page_title="Dashboard Análise de Polos e Alunos",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def load_and_process_data():
    """Carrega e processa todos os dados"""
    # Carregar dados
    data = GoogleSheetsLoader.load_all_data(GOOGLE_SHEETS_CONFIG)

    # Processar dados
    processed_data = {}

    if not data['polos_ativos'].empty:
        processed_data['polos'] = DataProcessor.clean_polos_data(
            data['polos_ativos'])
    else:
        processed_data['polos'] = pd.DataFrame()

    if not data['municipios'].empty:
        processed_data['municipios'] = DataProcessor.clean_municipios_data(
            data['municipios'])
    else:
        processed_data['municipios'] = pd.DataFrame()

    if not data['alunos'].empty:
        processed_data['alunos'] = DataProcessor.clean_alunos_data(
            data['alunos'])
        # Fazer merge com municípios para obter coordenadas
        processed_data['alunos'] = DataProcessor.merge_alunos_municipios(
            processed_data['alunos'],
            processed_data['municipios']
        )
    else:
        processed_data['alunos'] = pd.DataFrame()

    return processed_data


def display_metrics(polos_df, municipios_df, alunos_df):
    """Exibe métricas principais"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_polos = len(polos_df) if not polos_df.empty else 0
        st.metric("Total de Polos", total_polos)

    with col2:
        estados_atendidos = polos_df['UF'].nunique(
        ) if not polos_df.empty else 0
        st.metric("Estados Atendidos", estados_atendidos)

    with col3:
        total_municipios = len(municipios_df) if not municipios_df.empty else 0
        st.metric("Municípios Mapeados", total_municipios)

    with col4:
        total_alunos = alunos_df['CPF'].nunique(
        ) if not alunos_df.empty and 'CPF' in alunos_df.columns else 0
        st.metric("Total de Alunos", total_alunos)


def main():
    # Header principal
    st.markdown('<h1 class="main-header">🎓 Dashboard Análise de Polos e Alunos</h1>',
                unsafe_allow_html=True)

    # Sidebar para navegação
    st.sidebar.title("Navegação")

    # Carregar dados
    with st.spinner("Carregando e processando dados..."):
        data = load_and_process_data()

    polos_df = data['polos']
    municipios_df = data['municipios']
    alunos_df = data['alunos']

    # Verificar se os dados foram carregados
    if polos_df.empty and municipios_df.empty and alunos_df.empty:
        st.error(
            "Não foi possível carregar os dados. Verifique as configurações das APIs.")
        return

    # Exibir métricas principais
    display_metrics(polos_df, municipios_df, alunos_df)

    # Criar instância de visualizações
    viz = Visualizations(COLORS)

    # Seções do dashboard
    sections = [
        "📍 Análise Geográfica dos Polos",
        "📊 Análise de Municípios e Alunos",
        "🎯 Análise de Cobertura e Eficiência",
        "👥 Análise de Alunos e Cursos",
        "🔄 Análise de Alinhamento de Polos"
    ]

    selected_section = st.sidebar.selectbox("Selecione a seção:", sections)

    # Seção 1: Análise Geográfica dos Polos
    if selected_section == "📍 Análise Geográfica dos Polos":
        st.markdown(
            '<h2 class="section-header">📍 Análise Geográfica dos Polos</h2>', unsafe_allow_html=True)

        if not polos_df.empty:
            # Subseções
            geo_option = st.selectbox(
                "Escolha o tipo de visualização:",
                ["Mapa de Polos", "Mapa de Calor", "Gráficos de Distribuição"]
            )

            if geo_option == "Mapa de Polos":
                st.subheader("🗺️ Localização dos Polos")
                mapa_polos = viz.create_polos_map(polos_df, MAP_CONFIG)
                st_folium(mapa_polos, width=700, height=500)

            elif geo_option == "Mapa de Calor":
                st.subheader("🔥 Densidade de Polos")
                mapa_calor = viz.create_heatmap(polos_df, MAP_CONFIG)
                st_folium(mapa_calor, width=700, height=500)

            elif geo_option == "Gráficos de Distribuição":
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Polos por Estado")
                    fig_estados = viz.create_polos_by_state_chart(polos_df)
                    st.plotly_chart(fig_estados, use_container_width=True)

                with col2:
                    st.subheader("🥧 Distribuição por Região")
                    fig_regioes = viz.create_polos_by_region_pie(polos_df)
                    st.plotly_chart(fig_regioes, use_container_width=True)
        else:
            st.warning("Dados dos polos não disponíveis.")

        # Seção 2: Análise de Municípios e Alunos
    elif selected_section == "📊 Análise de Municípios e Alunos":
        st.markdown(
            '<h2 class="section-header">📊 Análise de Municípios e Alunos</h2>', unsafe_allow_html=True)

        if not municipios_df.empty:
            # Debug temporário - remover depois
            st.write("Debug - Colunas disponíveis:",
                     list(municipios_df.columns))
            st.write("Debug - Shape:", municipios_df.shape)
            if 'TOTAL_ALUNOS' in municipios_df.columns:
                st.write("Debug - TOTAL_ALUNOS stats:",
                         municipios_df['TOTAL_ALUNOS'].describe())

            # Seletor para top N
            top_n = st.selectbox("Selecione o número de municípios:", [
                                 10, 20, 50], index=0)

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

            # Análises de correlação
            st.subheader("🔍 Análises de Correlação")

            col3, col4 = st.columns(2)

            with col3:
                st.subheader("📏 Distância vs Alunos")
                try:
                    required_cols = [
                        'DISTANCIA_KM', 'TOTAL_ALUNOS', 'REGIAO', 'MUNICIPIO_IBGE', 'UF']
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

                            st.plotly_chart(
                                fig_scatter, use_container_width=True)
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

                            st.plotly_chart(
                                fig_boxplot, use_container_width=True)
                        else:
                            st.info("Dados insuficientes para gerar o gráfico.")
                    else:
                        st.info("Colunas necessárias não encontradas.")
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico: {str(e)}")

            # Heatmap de correlação
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
                            "Dados insuficientes para gerar a matriz de correlação.")
                else:
                    st.info("Colunas numéricas insuficientes para correlação.")
            except Exception as e:
                st.error(f"Erro ao gerar matriz de correlação: {str(e)}")

        else:
            st.warning("Dados dos municípios não disponíveis.")

    # Seção 3: Análise de Cobertura e Eficiência
    elif selected_section == "🎯 Análise de Cobertura e Eficiência":
        st.markdown(
            '<h2 class="section-header">🎯 Análise de Cobertura e Eficiência</h2>', unsafe_allow_html=True)

        if not polos_df.empty and not municipios_df.empty:
            # Métricas de cobertura
            metrics = DataProcessor.calculate_coverage_metrics(
                polos_df, municipios_df)

            # Exibir métricas de cobertura
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Municípios Cobertos",
                          f"{metrics.get('municipios_cobertos', 0)}/{metrics.get('total_municipios', 0)}")

            with col2:
                st.metric("% Cobertura",
                          f"{metrics.get('percentual_cobertura', 0):.1f}%")

            with col3:
                st.metric("Distância Média",
                          f"{metrics.get('distancia_media', 0):.1f} km")

            with col4:
                eficiencia = metrics.get(
                    'alunos_cobertos', 0) / len(polos_df) if len(polos_df) > 0 else 0
                st.metric("Alunos por Polo", f"{eficiencia:.0f}")

            # Mapa de cobertura
            st.subheader("🗺️ Mapa de Cobertura (Raio 100km)")
            mapa_cobertura = viz.create_coverage_map(
                polos_df, municipios_df, MAP_CONFIG)
            st_folium(mapa_cobertura, width=700, height=500)

            # Análise por região
            st.subheader("📊 Eficiência por Região")

            if 'REGIAO' in municipios_df.columns:
                eficiencia_regiao = municipios_df.groupby('REGIAO').agg({
                    'TOTAL_ALUNOS': 'sum',
                    'DISTANCIA_KM': 'mean',
                    'MUNICIPIO_IBGE': 'count'
                }).reset_index()

                eficiencia_regiao.columns = [
                    'Região', 'Total Alunos', 'Distância Média', 'Municípios']

                # Calcular eficiência (alunos por município)
                eficiencia_regiao['Eficiência'] = eficiencia_regiao['Total Alunos'] / \
                    eficiencia_regiao['Municípios']

                col1, col2 = st.columns(2)

                with col1:
                    fig_regiao_alunos = px.bar(eficiencia_regiao, x='Região', y='Total Alunos',
                                               title='Total de Alunos por Região')
                    st.plotly_chart(fig_regiao_alunos,
                                    use_container_width=True)

                with col2:
                    fig_regiao_dist = px.bar(eficiencia_regiao, x='Região', y='Distância Média',
                                             title='Distância Média por Região')
                    st.plotly_chart(fig_regiao_dist, use_container_width=True)

                # Tabela de eficiência
                st.subheader("📋 Resumo de Eficiência por Região")
                st.dataframe(eficiencia_regiao.round(2),
                             use_container_width=True)

        else:
            st.warning("Dados insuficientes para análise de cobertura.")

    # Seção 4: Análise de Alunos e Cursos
    elif selected_section == "👥 Análise de Alunos e Cursos":
        st.markdown(
            '<h2 class="section-header">👥 Análise de Alunos e Cursos</h2>', unsafe_allow_html=True)

        if not alunos_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📚 Cursos Mais Demandados")
                fig_cursos = viz.create_students_by_course_chart(alunos_df)
                st.plotly_chart(fig_cursos, use_container_width=True)

            with col2:
                if 'REGIAO' in alunos_df.columns:
                    st.subheader("🌎 Alunos por Região")
                    alunos_regiao = alunos_df['REGIAO'].value_counts()
                    fig_regiao = px.pie(values=alunos_regiao.values, names=alunos_regiao.index,
                                        title='Distribuição de Alunos por Região')
                    st.plotly_chart(fig_regiao, use_container_width=True)

            # Análise de cursos por UF
            if 'CURSO' in alunos_df.columns and 'UF' in alunos_df.columns:
                st.subheader("📊 Cursos Mais Demandados por UF")

                # Seletor de UF
                ufs_disponiveis = sorted(alunos_df['UF'].dropna().unique())
                uf_selecionada = st.selectbox(
                    "Selecione um estado:", ufs_disponiveis)

                if uf_selecionada:
                    alunos_uf = alunos_df[alunos_df['UF'] == uf_selecionada]
                    cursos_uf = alunos_uf['CURSO'].value_counts().head(10)

                    fig_cursos_uf = px.bar(
                        x=cursos_uf.values,
                        y=cursos_uf.index,
                        orientation='h',
                        title=f'Top 10 Cursos em {uf_selecionada}'
                    )
                    fig_cursos_uf.update_layout(
                        yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_cursos_uf, use_container_width=True)

            # Mapa de densidade de alunos
            if 'LAT' in alunos_df.columns and 'LNG' in alunos_df.columns:
                st.subheader("🗺️ Densidade de Alunos por Localização")

                # Filtrar alunos com coordenadas válidas
                alunos_com_coord = alunos_df.dropna(subset=['LAT', 'LNG'])

                if not alunos_com_coord.empty:
                    # Criar mapa de densidade
                    m = folium.Map(
                        location=[MAP_CONFIG['center_lat'],
                                  MAP_CONFIG['center_lon']],
                        zoom_start=MAP_CONFIG['zoom']
                    )

                    # Dados para heatmap
                    heat_data = [[row['LAT'], row['LNG']]
                                 for _, row in alunos_com_coord.iterrows()]

                    if heat_data:
                        from folium import plugins
                        plugins.HeatMap(heat_data, radius=15).add_to(m)

                        # Adicionar polos ao mapa
                        if not polos_df.empty:
                            for _, polo in polos_df.iterrows():
                                if pd.notna(polo['lat']) and pd.notna(polo['long']):
                                    folium.Marker(
                                        location=[polo['lat'], polo['long']],
                                        popup=f"<b>{polo['UNIDADE']}</b>",
                                        icon=folium.Icon(
                                            color='red', icon='graduation-cap', prefix='fa')
                                    ).add_to(m)

                        st_folium(m, width=700, height=500)

        else:
            st.warning("Dados dos alunos não disponíveis.")

    # Seção 5: Análise de Alinhamento de Polos
    elif selected_section == "🔄 Análise de Alinhamento de Polos":
        st.markdown(
            '<h2 class="section-header">🔄 Análise de Alinhamento de Polos</h2>', unsafe_allow_html=True)

        if not alunos_df.empty and 'POLO' in alunos_df.columns and 'POLO_MAIS_PROXIMO' in alunos_df.columns:

            # Análise de alinhamento
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⚖️ Alinhamento Polo Atual vs Ideal")
                fig_alignment = viz.create_alignment_analysis(alunos_df)
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

            # Diagrama Sankey
            st.subheader("🌊 Fluxo de Realocação (Sankey)")
            fig_sankey = viz.create_sankey_diagram(alunos_df)
            if fig_sankey.data:
                st.plotly_chart(fig_sankey, use_container_width=True)
            else:
                st.info("Não há dados suficientes para criar o diagrama de fluxo.")

            # Matriz de migração
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

            # Análise por UF
            st.subheader("📍 Desalinhamento por Estado")

            if 'UF' in alunos_df.columns:
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
                st.dataframe(desalinhamento_uf.round(2),
                             use_container_width=True)

                # Mapa de conexões
            st.subheader("🗺️ Mapa de Conexões Aluno-Polo")

            if 'LAT' in alunos_df.columns and 'LNG' in alunos_df.columns and not polos_df.empty:
                # Criar mapa de conexões
                m = folium.Map(
                    location=[MAP_CONFIG['center_lat'],
                              MAP_CONFIG['center_lon']],
                    zoom_start=MAP_CONFIG['zoom']
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

    # Rodapé com informações adicionais
    st.markdown("---")
    st.markdown("""
    ### 📊 Informações do Dashboard

    **Dados atualizados automaticamente das planilhas Google Sheets**

    **Funcionalidades:**
    - ✅ Análise geográfica interativa dos polos
    - ✅ Métricas de cobertura e eficiência
    - ✅ Análise de alinhamento de alunos
    - ✅ Visualizações de correlação e tendências
    - ✅ Mapas interativos com diferentes camadas
    - ✅ Cache de dados para otimização de performance

    **Tecnologias utilizadas:** Streamlit, Plotly, Folium, Pandas
    """)


if __name__ == "__main__":
    main()
