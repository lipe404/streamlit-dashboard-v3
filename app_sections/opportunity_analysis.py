import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import numpy as np

# Importar o carregador de dados do IBGE
from utils.ibge_data_loader import IBGEDataLoader


class OpportunityAnalysis:
    """
    Classe para a seção de Análise de Oportunidades do Dashboard.
    Integra dados de população do IBGE, IDH/PIB fictícios e dados de polos/alunos
    para identificar potenciais de expansão.
    """

    # Use Any para Visualizations para evitar circular import se não for tipo literal
    def __init__(self, viz: Any, map_config: Dict):
        self.viz = viz  # Instância da classe Visualizations
        self.map_config = map_config

    def render(self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame, alunos_df: pd.DataFrame):
        st.markdown(
            '<h2 class="section-header">Análise de Oportunidades e Insights</h2>', unsafe_allow_html=True)

        st.info("Esta seção integra dados do IBGE (população) e dados fictícios (IDH, PIB) para identificar municípios com alto potencial de expansão, que não possuem polos ou com baixa penetração de alunos.")

        # Carregar dados externos (cacheados)
        df_ibge_pop = IBGEDataLoader.fetch_population_data()
        df_additional_data = IBGEDataLoader.get_additional_municipal_data()

        if df_ibge_pop.empty:
            st.warning(
                "Não foi possível carregar os dados de população do IBGE. Alguns gráficos podem estar incompletos.")
            return

        if municipios_df.empty:
            st.warning(
                "Dados de municípios não disponíveis para análise de oportunidades.")
            return

        # Preparar dados combinados para análise de oportunidade
        opportunity_df = self._prepare_opportunity_data(
            polos_df, municipios_df, alunos_df, df_ibge_pop, df_additional_data)

        if opportunity_df.empty:
            st.warning(
                "Nenhum dado combinado disponível para análise de oportunidades após o processamento.")
            return

        # Filtros
        st.sidebar.subheader("Filtros de Oportunidade")

        all_ufs = sorted(opportunity_df['UF'].dropna().unique())
        selected_uf = st.sidebar.selectbox(
            "Filtrar por Estado (UF):", ["Todos"] + all_ufs)

        all_regions = sorted(opportunity_df['REGIAO'].dropna().unique())
        selected_region = st.sidebar.selectbox(
            "Filtrar por Região:", ["Todos"] + all_regions)

        population_threshold = st.sidebar.slider("População Mínima (para oportunidades):", 0, int(
            opportunity_df['POPULACAO_2022'].max() if 'POPULACAO_2022' in opportunity_df.columns else 100000), 50000)

        # Aplicar filtros
        filtered_df = opportunity_df.copy()
        if selected_uf != "Todos":
            filtered_df = filtered_df[filtered_df['UF'] == selected_uf]
        if selected_region != "Todos":
            filtered_df = filtered_df[filtered_df['REGIAO'] == selected_region]

        # Garantir que a coluna 'POPULACAO_2022' seja numérica antes de filtrar
        if 'POPULACAO_2022' in filtered_df.columns:
            filtered_df['POPULACAO_2022'] = pd.to_numeric(
                filtered_df['POPULACAO_2022'], errors='coerce').fillna(0)
            filtered_df = filtered_df[filtered_df['POPULACAO_2022']
                                      >= population_threshold]
        else:
            st.warning(
                "Coluna 'POPULACAO_2022' não encontrada no DataFrame de oportunidades. O filtro de população não será aplicado.")
            filtered_df = pd.DataFrame()  # Esvazia o DF se a coluna essencial não existir

        if filtered_df.empty:
            st.info("Nenhum município encontrado com os filtros aplicados.")
            return

        # Cards de Métricas
        st.subheader("Métricas de Oportunidade")
        col1, col2, col3 = st.columns(3)

        municipios_sem_polo = filtered_df[filtered_df['TEM_POLO'] == False]
        col1.metric("Municípios sem Polo (Filtrado)", len(municipios_sem_polo))

        # Potencial Alto: Sem Polo, População > 50k, 0 Alunos
        municipios_alto_potencial = municipios_sem_polo[
            (municipios_sem_polo['POPULACAO_2022'] > 50000) &
            (municipios_sem_polo['TOTAL_ALUNOS'] == 0)
        ]
        col2.metric("Potencial Alto (Sem Polo e Alunos)",
                    len(municipios_alto_potencial))

        total_pop_sem_polo = municipios_sem_polo['POPULACAO_2022'].sum()
        col3.metric("População Total em Municípios sem Polo",
                    f"{total_pop_sem_polo:,.0f}")

        # Gráficos
        st.subheader("Gráficos de Oportunidade")

        tab1, tab2, tab3 = st.tabs(
            ["População e Alunos", "Mapas de Oportunidade", "Correlações e IDH/PIB"])

        with tab1:
            st.write("#### Top Municípios sem Polo por População")
            df_no_polo = municipios_sem_polo.nlargest(20, 'POPULACAO_2022')
            if not df_no_polo.empty:
                fig = px.bar(df_no_polo,
                             x='POPULACAO_2022',
                             y='MUNICIPIO_IBGE',
                             orientation='h',
                             title='Top Municípios sem Polo por População',
                             hover_data=['UF', 'TOTAL_ALUNOS',
                                         'IDH_2010', 'PIB_PER_CAPITA_2021'],
                             color='POPULACAO_2022', color_continuous_scale='Plasma')
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum município sem polo encontrado com os filtros.")

            st.write("#### Ranking de Potencial (População / Alunos)")
            # Potencial = População / (Total_Alunos + 1) -> +1 para evitar divisão por zero
            df_potential = filtered_df.copy()
            # Garante que 'TOTAL_ALUNOS' seja numérica para a operação
            df_potential['TOTAL_ALUNOS'] = pd.to_numeric(
                df_potential['TOTAL_ALUNOS'], errors='coerce').fillna(0)
            df_potential['Potencial_Score'] = df_potential['POPULACAO_2022'] / \
                (df_potential['TOTAL_ALUNOS'] + 1)

            # Filtra apenas municípios com população e alunos para um score mais relevante
            df_potential = df_potential[(df_potential['POPULACAO_2022'] > 0)]
            df_potential = df_potential.sort_values(
                'Potencial_Score', ascending=False).head(20)

            if not df_potential.empty:
                fig = px.bar(df_potential,
                             x='Potencial_Score',
                             y='MUNICIPIO_IBGE',
                             orientation='h',
                             title='Ranking de Potencial (População / (Alunos+1))',
                             hover_data=['UF', 'POPULACAO_2022',
                                         'TOTAL_ALUNOS', 'TEM_POLO', 'IDH_2010'],
                             color='Potencial_Score', color_continuous_scale='Viridis')
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "Nenhum município com potencial calculado encontrado com os filtros.")

        with tab2:
            st.write("#### Mapa de Oportunidade: População Sem Polo")
            if 'LAT' in filtered_df.columns and 'LNG' in filtered_df.columns and not filtered_df.dropna(subset=['LAT', 'LNG']).empty:
                m = self.viz.create_opportunity_map(
                    filtered_df, polos_df, self.map_config)
                # Usar st_folium para renderizar o mapa no Streamlit
                st_folium(m, width=700, height=500)
            else:
                st.warning(
                    "Dados de LAT/LNG para municípios não estão disponíveis ou são insuficientes para o mapa.")

        with tab3:
            st.write("#### Correlação: População vs Alunos (Dispersão)")
            if not filtered_df.empty and 'POPULACAO_2022' in filtered_df.columns and 'TOTAL_ALUNOS' in filtered_df.columns:
                fig = px.scatter(filtered_df,
                                 x='POPULACAO_2022',
                                 y='TOTAL_ALUNOS',
                                 color='TEM_POLO',  # Cor por presença de polo
                                 size='POPULACAO_2022',  # Tamanho do ponto pela população
                                 hover_data=['MUNICIPIO_IBGE', 'UF',
                                             'IDH_2010', 'PIB_PER_CAPITA_2021'],
                                 title='População vs. Número de Alunos por Município',
                                 labels={'POPULACAO_2022': 'População (2022)', 'TOTAL_ALUNOS': 'Número de Alunos'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    "Dados insuficientes para o gráfico de dispersão População vs Alunos.")

            st.write("#### População por Faixa de IDH")
            if not filtered_df.empty and 'IDH_2010' in filtered_df.columns and 'POPULACAO_2022' in filtered_df.columns:
                # Filtrar NaNs no IDH para criar faixas
                df_idh = filtered_df.dropna(subset=['IDH_2010']).copy()
                if not df_idh.empty:
                    bins = [0, 0.5, 0.6, 0.7, 0.8, 1.0]
                    labels = ['Muito Baixo', 'Baixo',
                              'Médio', 'Alto', 'Muito Alto']
                    df_idh['IDH_FAIXA'] = pd.cut(
                        df_idh['IDH_2010'], bins=bins, labels=labels, right=False)

                    idh_pop = df_idh.groupby('IDH_FAIXA')[
                        'POPULACAO_2022'].sum().reset_index()

                    fig = px.bar(idh_pop,
                                 x='IDH_FAIXA',
                                 y='POPULACAO_2022',
                                 title='População Total por Faixa de IDH',
                                 labels={'POPULACAO_2022': 'População Total',
                                         'IDH_FAIXA': 'Faixa de IDH'},
                                 color='POPULACAO_2022', color_continuous_scale='Cividis')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(
                        "Dados de IDH insuficientes após filtragem para este gráfico.")
            else:
                st.info("Dados de IDH ou população insuficientes para este gráfico.")

    def _prepare_opportunity_data(self, polos_df: pd.DataFrame, municipios_df: pd.DataFrame, alunos_df: pd.DataFrame, df_ibge_pop: pd.DataFrame, df_additional_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara o DataFrame combinado para análise de oportunidades.
        Integra dados de polos, municípios (proximidade), alunos, população IBGE e dados adicionais.
        """
        # 1. Inicia com municipios_df como base
        combined_df = municipios_df.copy()

        # 2. Adiciona flag 'TEM_POLO'
        if 'CIDADE' in polos_df.columns and 'MUNICIPIO_IBGE' in combined_df.columns:
            polos_cidades = set(
                polos_df['CIDADE'].dropna().str.upper().str.strip())
            # Garante que MUNICIPIO_IBGE também seja string para comparação
            combined_df['TEM_POLO'] = combined_df['MUNICIPIO_IBGE'].fillna(
                '').astype(str).str.upper().str.strip().isin(polos_cidades)
        else:
            # Default para False se dados ausentes
            combined_df['TEM_POLO'] = False

        # 3. Garante que 'TOTAL_ALUNOS' seja numérica e trata NaNs
        if 'TOTAL_ALUNOS' not in combined_df.columns:
            combined_df['TOTAL_ALUNOS'] = 0  # Default se coluna não existe

        combined_df['TOTAL_ALUNOS'] = pd.to_numeric(
            combined_df['TOTAL_ALUNOS'], errors='coerce').fillna(0)

        # 4. Merge com dados de População do IBGE
        if not df_ibge_pop.empty and 'MUNICIPIO_IBGE' in combined_df.columns:
            # Limpa o nome do município em combined_df para corresponder ao nome limpo do IBGE
            # Usa o MUNICIPIO_IBGE original para a operação, depois pega o valor limpo
            combined_df['MUNICIPIO_IBGE_TEMP_CLEAN'] = combined_df['MUNICIPIO_IBGE'].fillna('').astype(
                # Adicionado .str.upper()
                str).str.replace(r'\s\(.*\)', '', regex=True).str.strip().str.upper()

            combined_df = combined_df.merge(
                # Remove UF do merge do IBGE para evitar conflito se UF já está no main DF
                df_ibge_pop[['MUNICIPIO_IBGE_CLEAN', 'POPULACAO_2022']],
                left_on=['MUNICIPIO_IBGE_TEMP_CLEAN'],  # Junta pelo nome limpo
                right_on=['MUNICIPIO_IBGE_CLEAN'],
                how='left',
                suffixes=('', '_ibge')
            )
            combined_df.drop(
                columns=['MUNICIPIO_IBGE_TEMP_CLEAN', 'MUNICIPIO_IBGE_CLEAN'], inplace=True)

        # Ajustar UF se o merge do IBGE trouxe UF_ibge e for mais confiável. No nosso caso, mantemos a UF do municipio_df original.
        # Se for necessário, mesclar por UF também.
        # combined_df.drop(columns=['UF_ibge'], inplace=True, errors='ignore') # Remove se não for usar

        else:
            # Default se não houver dados de população
            combined_df['POPULACAO_2022'] = 0

        # 5. Merge com dados adicionais (IDH, PIB)
        if not df_additional_data.empty and 'MUNICIPIO_IBGE' in combined_df.columns:
            # Limpa o nome do município em combined_df para corresponder ao nome limpo dos dados adicionais
            combined_df['MUNICIPIO_IBGE_TEMP_CLEAN_ADD'] = combined_df['MUNICIPIO_IBGE'].fillna('').astype(
                # Adicionado .str.upper()
                str).str.replace(r'\s\(.*\)', '', regex=True).str.strip().str.upper()

            combined_df = combined_df.merge(
                df_additional_data[['MUNICIPIO_IBGE_CLEAN',
                                    'IDH_2010', 'PIB_PER_CAPITA_2021']],
                left_on=['MUNICIPIO_IBGE_TEMP_CLEAN_ADD'],  # Junta pelo nome limpo
                right_on=['MUNICIPIO_IBGE_CLEAN'],
                how='left',
                suffixes=('', '_add')
            )
            combined_df.drop(columns=['MUNICIPIO_IBGE_TEMP_CLEAN_ADD',
                            'MUNICIPIO_IBGE_CLEAN'], inplace=True, errors='ignore')
        else:
            # Default para NaN se não houver dados adicionais
            combined_df['IDH_2010'] = np.nan
            combined_df['PIB_PER_CAPITA_2021'] = np.nan

        # Limpa os tipos de coluna após todos os merges
        combined_df['POPULACAO_2022'] = pd.to_numeric(
            combined_df['POPULACAO_2022'], errors='coerce').fillna(0)
        combined_df['IDH_2010'] = pd.to_numeric(
            combined_df['IDH_2010'], errors='coerce')
        combined_df['PIB_PER_CAPITA_2021'] = pd.to_numeric(
            combined_df['PIB_PER_CAPITA_2021'], errors='coerce')

        # Remover duplicatas se surgirem de merges (ex: se múltiplas entradas para o mesmo município na fonte)
        combined_df.drop_duplicates(
            subset=['MUNICIPIO_IBGE', 'UF'], inplace=True)

        return combined_df
