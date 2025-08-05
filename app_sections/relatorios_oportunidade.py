import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from typing import Dict, List, Tuple
import time
import os


# Função global para cache (fora da classe)
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_population_data_from_local_file() -> pd.DataFrame:
    """Carrega dados de população da planilha local"""
    try:
        # Caminho para o arquivo local
        file_path = os.path.join("data", "listagem_municipios.xls")

        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            st.error(f"❌ Arquivo não encontrado: {file_path}")
            return pd.DataFrame()

        # Carregar dados da planilha da aba "Municípios"
        # st.info("📊 Carregando dados de municípios da planilha local...")

        # Ler da aba "Municípios" com as colunas específicas
        df_municipios = pd.read_excel(
            file_path,
            sheet_name='Municípios',  # Especificar a aba
            usecols=[0, 3, 4],  # Colunas A (0), D (3), E (4)
            names=['uf', 'nome', 'populacao'],  # Renomear colunas
            skiprows=1  # Pular a primeira linha (cabeçalho)
        )

        # Limpar e processar dados
        df_municipios = clean_municipal_data(df_municipios)

        return df_municipios

    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha local: {str(e)}")
        return pd.DataFrame()


def clean_municipal_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e processa dados dos municípios"""
    try:
        # Remover linhas vazias
        initial_count = len(df)
        df = df.dropna(subset=['nome', 'uf'])

        # Limpar dados de texto
        df['nome'] = df['nome'].astype(str).str.strip().str.upper()
        df['uf'] = df['uf'].astype(str).str.strip().str.upper()

        # Limpar e converter população
        df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce')

        # Remover linhas sem população válida
        df = df.dropna(subset=['populacao'])
        df['populacao'] = df['populacao'].astype(int)

        # Filtrar apenas dados válidos (população > 0)
        df = df[df['populacao'] > 0]

        # Adicionar código IBGE simulado (para compatibilidade)
        df['codigo_ibge'] = range(1, len(df) + 1)

        # Mapear regiões baseado no UF
        regions_map = {
            # Norte
            'AC': 'Norte', 'AP': 'Norte', 'AM': 'Norte', 'PA': 'Norte',
            'RO': 'Norte', 'RR': 'Norte', 'TO': 'Norte',
            # Nordeste
            'AL': 'Nordeste', 'BA': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste',
            'PB': 'Nordeste', 'PE': 'Nordeste', 'PI': 'Nordeste', 'RN': 'Nordeste', 'SE': 'Nordeste',
            # Centro-Oeste
            'DF': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste',
            # Sudeste
            'ES': 'Sudeste', 'MG': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
            # Sul
            'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul'
        }

        df['REGIAO'] = df['uf'].map(regions_map)
        df['regiao'] = df['REGIAO']  # Para compatibilidade

        # Filtrar apenas UFs válidos
        df = df.dropna(subset=['REGIAO'])

        # Ordenar por população (maiores primeiro)
        df = df.sort_values('populacao', ascending=False)

        # Reset index
        df = df.reset_index(drop=True)

        # st.success(f"✅ Carregados {len(df):,} municípios da planilha local")

        return df

    except Exception as e:
        st.error(f"Erro ao processar dados dos municípios: {str(e)}")
        return pd.DataFrame()


class RelatoriosOportunidade:
    """Análise de oportunidades baseada em cidades com alta população sem polos"""

    def __init__(self, viz, map_config):
        self.viz = viz
        self.map_config = map_config

    def render(self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame = None, alunos_df: pd.DataFrame = None):
        """Renderiza a análise de oportunidades"""

        st.markdown("## 🌟 Relatórios de Oportunidade")
        st.markdown("---")

        # Verificar se há dados de polos
        if polos_df.empty:
            st.error("❌ Dados de polos não disponíveis para análise")
            return

        # Obter cidades com polos
        cidades_com_polos = self._get_cities_with_polos(polos_df)

        # Carregar dados de população da planilha local
        with st.spinner("🔄 Carregando dados de população das cidades brasileiras..."):
            dados_populacao = load_population_data_from_local_file()

        if dados_populacao.empty:
            st.error(
                "❌ Não foi possível carregar dados de população da planilha local")
            return

        # Identificar oportunidades
        oportunidades = self._identify_opportunities(
            dados_populacao, cidades_com_polos)

        if oportunidades.empty:
            st.warning("⚠️ Nenhuma oportunidade identificada")
            return

        # Exibir métricas principais
        self._display_opportunity_metrics(
            oportunidades, dados_populacao, cidades_com_polos)

        # Filtros - Agora em 4 colunas para incluir Estados
        st.markdown("### 🔧 Filtros de Análise")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_pop = int(oportunidades['populacao'].min())
            max_pop = int(oportunidades['populacao'].max())
            min_population = st.slider(
                "População mínima",
                min_value=min_pop,
                max_value=max_pop,
                value=min(50000, max_pop),
                step=10000,
                help="Filtrar cidades com população mínima"
            )

        with col2:
            available_regions = sorted(
                oportunidades['REGIAO'].unique().tolist())
            selected_regions = st.multiselect(
                "Regiões",
                options=available_regions,
                default=available_regions,
                help="Selecionar regiões para análise"
            )

        with col3:
            # Novo filtro de Estados
            available_states = sorted(oportunidades['uf'].unique().tolist())
            selected_states = st.multiselect(
                "Estados (UF)",
                options=available_states,
                default=available_states,
                help="Selecionar estados específicos para análise"
            )

        with col4:
            top_n = st.selectbox(
                "Top N cidades",
                options=[10, 20, 30, 50, 100],
                index=2,
                help="Número de cidades a exibir nos rankings"
            )

        # Filtrar dados com o novo filtro de estados
        oportunidades_filtradas = self._filter_opportunities(
            oportunidades, min_population, selected_regions, selected_states
        )

        if oportunidades_filtradas.empty:
            st.warning("⚠️ Nenhuma cidade encontrada com os filtros aplicados")
            return

        # Exibir informações dos filtros aplicados
        self._display_filter_info(oportunidades_filtradas, oportunidades)

        # Abas de análise
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Visão Geral",
            "🏙️ Por Cidade",
            "🗺️ Por Estado",
            "📈 Análise Detalhada"
        ])

        with tab1:
            self._render_general_overview(oportunidades_filtradas, top_n)

        with tab2:
            self._render_city_analysis(oportunidades_filtradas, top_n)

        with tab3:
            self._render_state_analysis(oportunidades_filtradas)

        with tab4:
            self._render_detailed_analysis(
                oportunidades_filtradas, dados_populacao, cidades_com_polos)

    def _display_filter_info(self, oportunidades_filtradas: pd.DataFrame, oportunidades_total: pd.DataFrame):
        """Exibe informações sobre os filtros aplicados"""

        if len(oportunidades_filtradas) < len(oportunidades_total):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.info(
                    f"🔍 **Filtrado:** {len(oportunidades_filtradas):,} de {len(oportunidades_total):,} cidades")

            with col2:
                pop_filtrada = oportunidades_filtradas['populacao'].sum()
                pop_total = oportunidades_total['populacao'].sum()
                pct_pop = (pop_filtrada / pop_total *
                           100) if pop_total > 0 else 0
                st.info(f"👥 **População:** {pct_pop:.1f}% do total")

            with col3:
                estados_filtrados = oportunidades_filtradas['uf'].nunique()
                regioes_filtradas = oportunidades_filtradas['REGIAO'].nunique()
                st.info(
                    f"🗺️ **Abrangência:** {estados_filtrados} estados, {regioes_filtradas} regiões")

    def _get_cities_with_polos(self, polos_df: pd.DataFrame) -> set:
        """Extrai conjunto de cidades que já possuem polos"""
        if 'CIDADE' not in polos_df.columns:
            return set()

        cidades_com_polos = set()
        for cidade in polos_df['CIDADE'].dropna():
            # Normalizar nome da cidade
            cidade_normalizada = str(cidade).upper().strip()
            cidades_com_polos.add(cidade_normalizada)

        return cidades_com_polos

    def _identify_opportunities(self, dados_populacao: pd.DataFrame, cidades_com_polos: set) -> pd.DataFrame:
        """Identifica cidades com oportunidades (alta população sem polo)"""
        if dados_populacao.empty:
            return pd.DataFrame()

        # Normalizar nomes das cidades para comparação
        dados_populacao['nome_normalizado'] = dados_populacao['nome'].str.upper(
        ).str.strip()

        # Filtrar cidades que NÃO têm polos
        oportunidades = dados_populacao[
            ~dados_populacao['nome_normalizado'].isin(cidades_com_polos)
        ].copy()

        # Ordenar por população (maiores primeiro)
        oportunidades = oportunidades.sort_values('populacao', ascending=False)

        # Adicionar ranking
        oportunidades['ranking_nacional'] = range(1, len(oportunidades) + 1)

        # Adicionar ranking por estado
        oportunidades['ranking_estadual'] = oportunidades.groupby('uf')['populacao'].rank(
            method='dense', ascending=False
        ).astype(int)

        return oportunidades

    def _filter_opportunities(self, oportunidades: pd.DataFrame, min_population: int,
                              selected_regions: List[str], selected_states: List[str]) -> pd.DataFrame:
        """Aplica filtros às oportunidades - ATUALIZADO para incluir filtro de estados"""
        if oportunidades.empty:
            return oportunidades

        # Filtrar por população mínima
        filtered = oportunidades[oportunidades['populacao']
                                 >= min_population].copy()

        # Filtrar por regiões selecionadas
        if selected_regions:
            filtered = filtered[filtered['REGIAO'].isin(selected_regions)]

        # NOVO: Filtrar por estados selecionados
        if selected_states:
            filtered = filtered[filtered['uf'].isin(selected_states)]

        return filtered

    def _display_opportunity_metrics(self, oportunidades: pd.DataFrame, dados_populacao: pd.DataFrame, cidades_com_polos: set):
        """Exibe métricas principais das oportunidades"""

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_cidades_sem_polo = len(oportunidades)
            st.metric(
                "🏙️ Cidades sem Polo",
                f"{total_cidades_sem_polo:,}",
                help="Total de cidades que não possuem polos"
            )

        with col2:
            total_cidades_com_polo = len(cidades_com_polos)
            st.metric(
                "🎓 Cidades com Polo",
                f"{total_cidades_com_polo:,}",
                help="Total de cidades que já possuem polos"
            )

        with col3:
            populacao_sem_polo = oportunidades['populacao'].sum()
            st.metric(
                "👥 População sem Polo",
                f"{populacao_sem_polo:,}",
                help="População total das cidades sem polos"
            )

        with col4:
            if not oportunidades.empty:
                media_pop_sem_polo = oportunidades['populacao'].mean()
                st.metric(
                    "📊 Média Pop. sem Polo",
                    f"{media_pop_sem_polo:,.0f}",
                    help="População média das cidades sem polos"
                )

    def _render_general_overview(self, oportunidades: pd.DataFrame, top_n: int):
        """Renderiza visão geral das oportunidades"""

        st.markdown("### 📊 Visão Geral das Oportunidades")

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de pizza por região
            fig_regiao = self._create_opportunities_by_region_pie(
                oportunidades)
            st.plotly_chart(fig_regiao, use_container_width=True)

        with col2:
            # Top cidades por população
            fig_top_cidades = self._create_top_cities_chart(
                oportunidades, top_n)
            st.plotly_chart(fig_top_cidades, use_container_width=True)

        # Distribuição de população
        st.markdown("#### 📈 Distribuição de População")
        fig_dist = self._create_population_distribution_chart(oportunidades)
        st.plotly_chart(fig_dist, use_container_width=True)

    def _render_city_analysis(self, oportunidades: pd.DataFrame, top_n: int):
        """Renderiza análise por cidade"""

        st.markdown("### 🏙️ Análise por Cidade")

        # Tabela das top oportunidades
        st.markdown(f"#### 🔝 Top {top_n} Cidades com Maior Oportunidade")

        top_cities = oportunidades.head(top_n)[
            ['ranking_nacional', 'nome', 'uf', 'REGIAO', 'populacao']
        ].copy()

        top_cities.columns = ['Ranking', 'Cidade', 'UF', 'Região', 'População']
        top_cities['População'] = top_cities['População'].apply(
            lambda x: f"{x:,}")

        st.dataframe(
            top_cities,
            use_container_width=True,
            hide_index=True
        )

        # Gráfico de barras horizontal
        fig_horizontal = self._create_horizontal_cities_chart(
            oportunidades, top_n)
        st.plotly_chart(fig_horizontal, use_container_width=True)

    def _render_state_analysis(self, oportunidades: pd.DataFrame):
        """Renderiza análise por estado"""

        st.markdown("### 🗺️ Análise por Estado")

        # Calcular métricas por estado
        stats_por_estado = oportunidades.groupby('uf').agg({
            'populacao': ['sum', 'mean', 'count'],
            'nome': 'count'
        }).round(0)

        stats_por_estado.columns = ['Pop_Total',
                                    'Pop_Media', 'Pop_Count', 'Num_Cidades']
        stats_por_estado = stats_por_estado.reset_index()
        stats_por_estado = stats_por_estado.sort_values(
            'Pop_Total', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de barras por estado - população total
            fig_estado_pop = self._create_states_population_chart(
                stats_por_estado)
            st.plotly_chart(fig_estado_pop, use_container_width=True)

        with col2:
            # Gráfico de barras por estado - número de cidades
            fig_estado_cidades = self._create_states_cities_chart(
                stats_por_estado)
            st.plotly_chart(fig_estado_cidades, use_container_width=True)

        # Tabela resumo por estado
        st.markdown("#### 📋 Resumo por Estado")

        display_stats = stats_por_estado.copy()
        display_stats.columns = [
            'UF', 'População Total', 'População Média', 'Pop_Count_Hidden', 'Número de Cidades']
        display_stats = display_stats.drop('Pop_Count_Hidden', axis=1)
        display_stats['População Total'] = display_stats['População Total'].apply(
            lambda x: f"{x:,.0f}")
        display_stats['População Média'] = display_stats['População Média'].apply(
            lambda x: f"{x:,.0f}")

        st.dataframe(
            display_stats,
            use_container_width=True,
            hide_index=True
        )

    def _render_detailed_analysis(self, oportunidades: pd.DataFrame, dados_populacao: pd.DataFrame, cidades_com_polos: set):
        """Renderiza análise detalhada"""

        st.markdown("### 📈 Análise Detalhada")

        col1, col2 = st.columns(2)

        with col1:
            # Análise de cobertura atual
            st.markdown("#### 🎯 Cobertura Atual")

            total_cidades = len(dados_populacao)
            cidades_com_polo = len(cidades_com_polos)
            cidades_sem_polo = len(oportunidades)

            cobertura_pct = (cidades_com_polo / total_cidades) * \
                100 if total_cidades > 0 else 0

            st.metric("Cobertura de Cidades", f"{cobertura_pct:.1f}%")
            st.metric("Cidades Cobertas", f"{cidades_com_polo:,}")
            st.metric("Cidades Descobertas", f"{cidades_sem_polo:,}")

        with col2:
            # Análise de população
            st.markdown("#### 👥 Análise Populacional")

            pop_total = dados_populacao['populacao'].sum()
            pop_sem_polo = oportunidades['populacao'].sum()
            pop_com_polo = pop_total - pop_sem_polo

            cobertura_pop_pct = (pop_com_polo / pop_total) * \
                100 if pop_total > 0 else 0

            st.metric("Cobertura Populacional", f"{cobertura_pop_pct:.1f}%")
            st.metric("População Coberta", f"{pop_com_polo:,}")
            st.metric("População Descoberta", f"{pop_sem_polo:,}")

        # Gráfico de análise de gaps
        st.markdown("#### 🔍 Análise de Gaps por Região")
        fig_gaps = self._create_coverage_gaps_chart(
            oportunidades, dados_populacao, cidades_com_polos)
        st.plotly_chart(fig_gaps, use_container_width=True)

    # Métodos para criação de gráficos específicos
    def _create_opportunities_by_region_pie(self, oportunidades: pd.DataFrame) -> go.Figure:
        """Cria gráfico de pizza das oportunidades por região"""

        if oportunidades.empty:
            return go.Figure()

        try:
            regiao_counts = oportunidades['REGIAO'].value_counts()

            fig = go.Figure(data=[go.Pie(
                labels=regiao_counts.index,
                values=regiao_counts.values,
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{percent}<br>(%{value} cidades)',
                hovertemplate='<b>%{label}</b><br>Cidades: %{value}<br>Percentual: %{percent}<extra></extra>'
            )])

            fig.update_layout(
                title="Distribuição de Oportunidades por Região",
                height=400
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_top_cities_chart(self, oportunidades: pd.DataFrame, top_n: int) -> go.Figure:
        """Cria gráfico das top cidades"""

        if oportunidades.empty:
            return go.Figure()

        try:
            top_cities = oportunidades.head(top_n)

            fig = px.bar(
                top_cities,
                x='populacao',
                y='nome',
                orientation='h',
                title=f'Top {top_n} Cidades por População',
                color='populacao',
                color_continuous_scale='Viridis',
                text='populacao'
            )

            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='População',
                yaxis_title='Cidade',
                height=400
            )

            fig.update_traces(texttemplate='%{text:,}', textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_population_distribution_chart(self, oportunidades: pd.DataFrame) -> go.Figure:
        """Cria gráfico de distribuição de população"""

        if oportunidades.empty:
            return go.Figure()

        try:
            fig = px.histogram(
                oportunidades,
                x='populacao',
                nbins=30,
                title='Distribuição de População das Cidades sem Polo',
                color_discrete_sequence=['#1f77b4']
            )

            fig.update_layout(
                xaxis_title='População',
                yaxis_title='Número de Cidades',
                height=400
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_horizontal_cities_chart(self, oportunidades: pd.DataFrame, top_n: int) -> go.Figure:
        """Cria gráfico horizontal das cidades"""

        if oportunidades.empty:
            return go.Figure()

        try:
            top_cities = oportunidades.head(top_n)

            fig = go.Figure(data=[
                go.Bar(
                    y=top_cities['nome'],
                    x=top_cities['populacao'],
                    orientation='h',
                    text=top_cities['populacao'],
                    texttemplate='%{text:,}',
                    textposition='outside',
                    marker_color='rgba(55, 128, 191, 0.7)',
                    hovertemplate='<b>%{y}</b><br>População: %{x:,}<extra></extra>'
                )
            ])

            fig.update_layout(
                title=f'Top {top_n} Cidades - Maiores Oportunidades',
                xaxis_title='População',
                yaxis_title='Cidade',
                yaxis={'categoryorder': 'total ascending'},
                height=max(400, top_n * 25)
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_states_population_chart(self, stats_por_estado: pd.DataFrame) -> go.Figure:
        """Cria gráfico de população por estado"""

        try:
            fig = px.bar(
                stats_por_estado.head(15),
                x='uf',
                y='Pop_Total',
                title='População Total sem Polo por Estado (Top 15)',
                color='Pop_Total',
                color_continuous_scale='Blues',
                text='Pop_Total'
            )

            fig.update_layout(
                xaxis_title='Estado',
                yaxis_title='População Total',
                height=400
            )

            fig.update_traces(
                texttemplate='%{text:,.0f}', textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_states_cities_chart(self, stats_por_estado: pd.DataFrame) -> go.Figure:
        """Cria gráfico de número de cidades por estado"""

        try:
            fig = px.bar(
                stats_por_estado.head(15),
                x='uf',
                y='Num_Cidades',
                title='Número de Cidades sem Polo por Estado (Top 15)',
                color='Num_Cidades',
                color_continuous_scale='Oranges',
                text='Num_Cidades'
            )

            fig.update_layout(
                xaxis_title='Estado',
                yaxis_title='Número de Cidades',
                height=400
            )

            fig.update_traces(texttemplate='%{text}', textposition='outside')

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )

    def _create_coverage_gaps_chart(self, oportunidades: pd.DataFrame, dados_populacao: pd.DataFrame, cidades_com_polos: set) -> go.Figure:
        """Cria gráfico de análise de gaps de cobertura"""

        try:
            # Calcular métricas por região
            gaps_por_regiao = []

            for regiao in dados_populacao['REGIAO'].unique():
                if pd.isna(regiao):
                    continue

                # Dados da região
                regiao_data = dados_populacao[dados_populacao['REGIAO'] == regiao]
                oportunidades_regiao = oportunidades[oportunidades['REGIAO'] == regiao]

                # Calcular métricas
                total_cidades = len(regiao_data)
                cidades_sem_polo = len(oportunidades_regiao)
                cidades_com_polo = total_cidades - cidades_sem_polo

                pop_total = regiao_data['populacao'].sum()
                pop_sem_polo = oportunidades_regiao['populacao'].sum()
                pop_com_polo = pop_total - pop_sem_polo

                gaps_por_regiao.append({
                    'Regiao': regiao,
                    'Cidades_Total': total_cidades,
                    'Cidades_Com_Polo': cidades_com_polo,
                    'Cidades_Sem_Polo': cidades_sem_polo,
                    'Pop_Total': pop_total,
                    'Pop_Com_Polo': pop_com_polo,
                    'Pop_Sem_Polo': pop_sem_polo,
                    'Cobertura_Cidades_Pct': (cidades_com_polo / total_cidades * 100) if total_cidades > 0 else 0,
                    'Cobertura_Pop_Pct': (pop_com_polo / pop_total * 100) if pop_total > 0 else 0
                })

            df_gaps = pd.DataFrame(gaps_por_regiao)

            # Criar gráfico de barras agrupadas
            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Cobertura de Cidades (%)',
                x=df_gaps['Regiao'],
                y=df_gaps['Cobertura_Cidades_Pct'],
                marker_color='rgba(55, 128, 191, 0.7)',
                text=df_gaps['Cobertura_Cidades_Pct'].round(1),
                texttemplate='%{text}%',
                textposition='outside'
            ))

            fig.add_trace(go.Bar(
                name='Cobertura Populacional (%)',
                x=df_gaps['Regiao'],
                y=df_gaps['Cobertura_Pop_Pct'],
                marker_color='rgba(255, 127, 14, 0.7)',
                text=df_gaps['Cobertura_Pop_Pct'].round(1),
                texttemplate='%{text}%',
                textposition='outside'
            ))

            fig.update_layout(
                title='Análise de Cobertura por Região',
                xaxis_title='Região',
                yaxis_title='Percentual de Cobertura (%)',
                barmode='group',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )

            return fig

        except Exception as e:
            return go.Figure().add_annotation(
                text=f"Erro: {str(e)}", x=0.5, y=0.5, showarrow=False
            )
