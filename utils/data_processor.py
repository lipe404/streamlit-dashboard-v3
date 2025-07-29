import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Tuple, List
import re


class DataProcessor:
    """Classe para processamento e limpeza dos dados"""

    # Adicione este método à classe DataProcessor

    @staticmethod
    def enhance_municipal_data_for_coverage(municipios_df: pd.DataFrame, polos_df: pd.DataFrame) -> pd.DataFrame:
        """Aprimora dados municipais para análise de cobertura"""

        if municipios_df.empty or polos_df.empty:
            return municipios_df

        try:
            # Criar cópia para não modificar o original
            enhanced_df = municipios_df.copy()

            # Identificar municípios com polos
            if 'CIDADE' in polos_df.columns and 'MUNICIPIO_IBGE' in enhanced_df.columns:
                polos_cidades = set(
                    polos_df['CIDADE'].dropna().str.upper().str.strip())
                enhanced_df['TEM_POLO'] = enhanced_df[
                    'MUNICIPIO_IBGE'].str.upper(
                ).str.strip().isin(polos_cidades)
            else:
                enhanced_df['TEM_POLO'] = False

            # Categorizar tipo de cobertura
            enhanced_df['TIPO_COBERTURA'] = enhanced_df.apply(
                lambda row: DataProcessor._categorize_coverage_type(
                    row), axis=1
            )

            # Calcular estatísticas de cobertura por UF
            coverage_stats = enhanced_df.groupby('UF').agg({
                'TEM_POLO': 'sum',
                'DISTANCIA_KM': 'mean',
                'TOTAL_ALUNOS': 'sum',
                'MUNICIPIO_IBGE': 'count'
            }).reset_index()

            coverage_stats.columns = ['UF', 'Municipios_Com_Polo',
                                      'Distancia_Media', 'Total_Alunos',
                                      'Total_Municipios']

            # Merge das estatísticas de volta
            enhanced_df = enhanced_df.merge(
                coverage_stats, on='UF', how='left', suffixes=('', '_UF'))

            return enhanced_df

        except Exception as e:
            st.warning(f"Erro ao aprimorar dados municipais: {str(e)}")
            return municipios_df

    @staticmethod
    def _categorize_coverage_type(row):
        """Categoriza o tipo de cobertura do município"""
        try:
            if row.get('TEM_POLO', False):
                return 'Com Polo'

            distancia = row.get('DISTANCIA_KM', 999)
            if pd.notna(distancia):
                dist_float = float(distancia)
                if dist_float <= 50:
                    return 'Cobertura Próxima'
                elif dist_float <= 100:
                    return 'Cobertura Estendida'
                else:
                    return 'Fora da Cobertura'
            else:
                return 'Sem Dados'
        except:
            return 'Sem Dados'

    @staticmethod
    def clean_polos_data(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e processa dados dos polos ativos"""
        if df.empty:
            return df

        # Baseado no debug
        columns_map = {
            0: 'UNIDADE',      # UNIDADE
            1: 'RAZAO',        # RAZÃO
            3: 'ENDERECO',     # ENDEREÇO
            4: 'CIDADE',       # CIDADE
            5: 'UF',           # UF
            6: 'CEP',          # CEP
            12: 'lat',         # lat
            13: 'long'         # long
        }

        # Criar DataFrame limpo
        df_clean = df.copy()

        # Renomear colunas baseado no índice, verificando se existem
        for idx, new_name in columns_map.items():
            if idx < len(df.columns):
                old_name = df.columns[idx]
                df_clean.rename(columns={old_name: new_name}, inplace=True)
            else:
                df_clean[new_name] = ''

        # Manter apenas colunas necessárias
        required_cols = list(columns_map.values())
        df_clean = df_clean[required_cols]

        # Limpeza de dados
        df_clean = DataProcessor._clean_coordinates(df_clean)
        df_clean = DataProcessor._clean_text_columns(df_clean)
        df_clean = DataProcessor._add_region_column(df_clean)

        return df_clean

    @staticmethod
    def clean_municipios_data(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e processa dados dos municípios"""
        if df.empty:
            return df

        # Com headers únicos
        columns_map = {
            0: 'MUNICIPIO_IBGE',    # MUNICÍPIO - IBGE
            1: 'UF',                # UF
            3: 'LAT',               # LAT (primeira ocorrência)
            4: 'LNG',               # LNG (primeira ocorrência)
            5: 'POLO_ENDERECO',     # POLO MAIS PRÓXIMO - ENDEREÇO COMPLETO
            9: 'UNIDADE_POLO',      # UNIDADE/POLO
            10: 'DISTANCIA_KM',     # DISTÂNCIA KM
            14: 'TOTAL_ALUNOS'      # TOTAL DE ALUNOS
        }

        # Criar DataFrame limpo
        df_clean = df.copy()

        # Renomear colunas baseado no índice, verificando se existem
        for idx, new_name in columns_map.items():
            if idx < len(df.columns):
                old_name = df.columns[idx]
                df_clean.rename(columns={old_name: new_name}, inplace=True)
            else:
                df_clean[new_name] = '' if new_name not in [
                    'LAT', 'LNG', 'DISTANCIA_KM', 'TOTAL_ALUNOS'] else 0

        # Manter apenas colunas necessárias
        required_cols = list(columns_map.values())
        df_clean = df_clean[required_cols]

        # Limpeza de dados
        df_clean = DataProcessor._clean_coordinates(
            df_clean, lat_col='LAT', lng_col='LNG')
        df_clean = DataProcessor._clean_numeric_columns(df_clean)
        df_clean = DataProcessor._add_region_column(df_clean)

        return df_clean

    @staticmethod
    def clean_alunos_data(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e processa dados dos alunos"""
        if df.empty:
            return df

        # Baseado no debug
        columns_map = {
            2: 'CPF',                # CPF
            3: 'CEP',                # CEP
            4: 'CIDADE',             # Cidade
            5: 'UF',                 # UF
            10: 'CURSO',             # Curso
            11: 'POLO',              # Polo
            12: 'POLO_MAIS_PROXIMO'  # POLO MAIS PRÓXIMO
        }

        # Criar DataFrame limpo
        df_clean = df.copy()

        # Renomear colunas baseado no índice, verificando se existem
        for idx, new_name in columns_map.items():
            if idx < len(df.columns):
                old_name = df.columns[idx]
                df_clean.rename(columns={old_name: new_name}, inplace=True)
            else:
                df_clean[new_name] = ''

        # Manter apenas colunas necessárias
        required_cols = list(columns_map.values())
        df_clean = df_clean[required_cols]

        # Limpeza de dados
        df_clean = DataProcessor._clean_text_columns(df_clean)
        df_clean = DataProcessor._add_region_column(df_clean)

        return df_clean

    @staticmethod
    def clean_vendas_data(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e processa dados de vendas"""
        if df.empty:
            return df

        try:
            # Mapeamento das colunas baseado nas posições especificadas
            columns_map = {
                2: 'CPF',                    # Coluna C (índice 2)
                3: 'ALUNO',                  # Coluna D (índice 3)
                4: 'NIVEL',                  # Coluna E (índice 4)
                5: 'CURSO',                  # Coluna F (índice 5)
                9: 'DT_PAGTO',               # Coluna J (índice 9)
                13: 'TIPO_PARCERIA'          # Coluna N (índice 13)
            }

            # Criar DataFrame limpo
            df_clean = df.copy()

            # Renomear colunas baseado no índice, verificando se existem
            for idx, new_name in columns_map.items():
                if idx < len(df.columns):
                    old_name = df.columns[idx]
                    df_clean.rename(columns={old_name: new_name}, inplace=True)
                else:
                    df_clean[new_name] = ''

            # Manter apenas colunas necessárias
            required_cols = list(columns_map.values())
            df_clean = df_clean[required_cols]

            # Filtrar modalidades válidas
            modalidades_validas = [
                'Aperfeiçoamento', 'Curso Técnico', 'Disciplina Isolada',
                'Disciplinas Eletivas', 'Ensino fundamental (EJA)',
                'Ensino Médio (EJA)', 'Extensão', 'Graduação',
                'Pós-Graduação', 'Segunda Graduação', 'Tecnólogo'
            ]

            df_clean = df_clean[df_clean['NIVEL'].isin(modalidades_validas)]

            # Filtrar tipos de parceria válidos
            parcerias_validas = ['Parceiro Comercial',
                                 'Parceiro Polo', 'Comercial Interno']
            df_clean = df_clean[df_clean['TIPO_PARCERIA'].isin(
                parcerias_validas)]

            # Processar data de pagamento
            df_clean = DataProcessor._process_payment_date(df_clean)

            # Limpeza de dados
            df_clean = DataProcessor._clean_text_columns(df_clean)

            # Remover linhas com dados essenciais vazios
            df_clean = df_clean.dropna(
                subset=['CPF', 'DT_PAGTO', 'NIVEL', 'TIPO_PARCERIA'])

            return df_clean

        except Exception as e:
            st.error(f"Erro ao processar dados de vendas: {str(e)}")
            return pd.DataFrame()

    # Dentro da classe DataProcessor, no método _process_payment_date
    @staticmethod
    def _process_payment_date(df: pd.DataFrame) -> pd.DataFrame:
        """Processa e converte datas de pagamento"""
        if 'DT_PAGTO' not in df.columns:
            return df

        try:
            # Converter para datetime, tratando erros
            df['DT_PAGTO'] = pd.to_datetime(
                df['DT_PAGTO'], format='%d/%m/%Y', errors='coerce')

            # Remover linhas onde a conversão falhou (Dt Pagto é NaN)
            df = df.dropna(subset=['DT_PAGTO'])

            if df.empty:
                return df

            # Extrair informações de data
            df['ANO'] = df['DT_PAGTO'].dt.year
            df['MES'] = df['DT_PAGTO'].dt.month
            df['MES_ANO'] = df['DT_PAGTO'].dt.to_period('M').astype(str)
            df['TRIMESTRE'] = df['DT_PAGTO'].dt.quarter
            df['SEMESTRE'] = df['DT_PAGTO'].dt.month.apply(
                lambda x: 1 if x <= 6 else 2)
            df['DIA_DO_MES'] = df['DT_PAGTO'].dt.day

            # Nomes dos meses em português
            meses_pt = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }

            df['MES_NOME'] = df['MES'].map(meses_pt)

            # Filtrar apenas dados válidos (remover datas futuras ou muito antigas)
            # Pega o ano atual dinamicamente
            current_year = pd.to_datetime('today').year
            df = df[(df['ANO'] >= 2020) & (df['ANO'] <= current_year)]

            return df

        except Exception as e:
            st.warning(f"Erro ao processar datas de pagamento: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def _clean_coordinates(
            df: pd.DataFrame, lat_col: str = 'lat',
            lng_col: str = 'long') -> pd.DataFrame:
        """Limpa e converte coordenadas para float"""
        try:
            if lat_col in df.columns and len(df) > 0:
                # Trabalhar com a Series específica, não o DataFrame
                lat_series = df[lat_col].fillna('').astype(str)
                lat_series = lat_series.str.replace(',', '.')
                lat_series = lat_series.str.replace(r'[^\d.-]', '', regex=True)
                df[lat_col] = pd.to_numeric(lat_series, errors='coerce')

            if lng_col in df.columns and len(df) > 0:
                # Trabalhar com a Series específica, não o DataFrame
                lng_series = df[lng_col].fillna('').astype(str)
                lng_series = lng_series.str.replace(',', '.')
                lng_series = lng_series.str.replace(r'[^\d.-]', '', regex=True)
                df[lng_col] = pd.to_numeric(lng_series, errors='coerce')

        except Exception as e:
            # Em caso de erro, criar colunas com valores NaN
            if lat_col in df.columns:
                df[lat_col] = np.nan
            if lng_col in df.columns:
                df[lng_col] = np.nan

        return df

    @staticmethod
    def _clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa colunas numéricas"""
        numeric_cols = ['DISTANCIA_KM', 'TOTAL_ALUNOS']

        for col in numeric_cols:
            if col in df.columns and len(df) > 0:
                try:
                    # Trabalhar com a Series específica
                    series = df[col].fillna('').astype(str)
                    # Remover caracteres não numéricos,
                    # manter apenas dígitos, pontos e vírgulas
                    series = series.str.replace(r'[^\d.,]', '', regex=True)
                    series = series.str.replace(',', '.')
                    # Remover strings vazias
                    series = series.replace('', '0')
                    df[col] = pd.to_numeric(series, errors='coerce')
                    df[col] = df[col].fillna(0)
                except Exception as e:
                    df[col] = 0

        return df

    @staticmethod
    def _clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Limpa colunas de texto"""
        try:
            if len(df) > 0:
                # Selecionar apenas colunas de texto que existem
                text_cols = df.select_dtypes(include=['object']).columns

                for col in text_cols:
                    if col in df.columns:
                        # Trabalhar com a Series específica
                        series = df[col].fillna('').astype(str)
                        series = series.str.strip()
                        series = series.replace('nan', '')
                        series = series.replace('', np.nan)
                        df[col] = series

        except Exception as e:
            pass

        return df

    @staticmethod
    def _add_region_column(df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona coluna de região baseada no UF"""
        if 'UF' not in df.columns or len(df) == 0:
            return df

        regions = {
            'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
            'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
            'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
            'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
            'Sul': ['PR', 'RS', 'SC']
        }

        def get_region(uf):
            try:
                if pd.isna(uf) or uf == '' or str(uf).lower() == 'nan':
                    return 'Não identificado'
                uf_clean = str(uf).upper().strip()
                for region, states in regions.items():
                    if uf_clean in states:
                        return region
                return 'Não identificado'
            except:
                return 'Não identificado'

        try:
            df['REGIAO'] = df['UF'].apply(get_region)
        except Exception as e:
            df['REGIAO'] = 'Não identificado'

        return df

    @staticmethod
    def merge_alunos_municipios(
            alunos_df: pd.DataFrame,
            municipios_df: pd.DataFrame) -> pd.DataFrame:
        """Faz merge dos dados de alunos
        com municípios para obter coordenadas"""
        if alunos_df.empty or municipios_df.empty:
            return alunos_df

        try:
            # Verificar se as colunas necessárias existem
            alunos_cols = ['CIDADE', 'UF']
            municipios_cols = ['MUNICIPIO_IBGE', 'UF', 'LAT', 'LNG']

            # Verificar se todas as colunas existem
            if all(col in alunos_df.columns for col in alunos_cols) and \
               all(col in municipios_df.columns for col in municipios_cols):

                # Merge baseado na cidade e UF
                merged_df = alunos_df.merge(
                    municipios_df[municipios_cols],
                    left_on=['CIDADE', 'UF'],
                    right_on=['MUNICIPIO_IBGE', 'UF'],
                    how='left',
                    suffixes=('', '_municipio')
                )
                return merged_df
            else:
                return alunos_df

        except Exception as e:
            return alunos_df

    @staticmethod
    def calculate_coverage_metrics(
            polos_df: pd.DataFrame, municipios_df: pd.DataFrame) -> Dict:
        """Calcula métricas de cobertura dos polos"""
        metrics = {
            'total_municipios': 0,
            'municipios_cobertos': 0,
            'percentual_cobertura': 0,
            'distancia_media': 0,
            'alunos_cobertos': 0,
            'total_alunos': 0
        }

        try:
            if not polos_df.empty and not municipios_df.empty:
                # Raio de cobertura de 100km
                coverage_radius = 100

                # Verificar se a coluna DISTANCIA_KM existe e tem dados válidos
                if 'DISTANCIA_KM' in municipios_df.columns:
                    # Filtrar municípios com dados válidos
                    municipios_validos = municipios_df[
                        (municipios_df['DISTANCIA_KM'].notna()) &
                        (municipios_df['DISTANCIA_KM'] > 0)
                    ]

                    if not municipios_validos.empty:
                        # Municípios dentro da cobertura
                        municipios_cobertura = municipios_validos[
                            municipios_validos[
                                'DISTANCIA_KM'] <= coverage_radius
                        ]

                        metrics['total_municipios'] = len(municipios_validos)
                        metrics['municipios_cobertos'] = len(
                            municipios_cobertura)
                        metrics['percentual_cobertura'] = (
                            len(municipios_cobertura) / len(
                                municipios_validos)) * 100
                        metrics['distancia_media'] = municipios_validos[
                            'DISTANCIA_KM'].mean(
                        )

                        if 'TOTAL_ALUNOS' in municipios_df.columns:
                            metrics['alunos_cobertos'] = municipios_cobertura[
                                'TOTAL_ALUNOS'].sum(
                            )
                            metrics['total_alunos'] = municipios_validos[
                                'TOTAL_ALUNOS'].sum(
                            )

        except Exception as e:
            pass

        return metrics
