import pandas as pd
import requests
import streamlit as st
from typing import Dict, Any
import numpy as np


class GoogleSheetsLoader:
    """Classe para carregar dados do Google Sheets"""

    @staticmethod
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def load_sheet_data(
            api_key: str, sheet_id: str, sheet_name: str) -> pd.DataFrame:
        """Carrega dados de uma planilha específica do Google Sheets"""
        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{
                sheet_id}/values/{
                    sheet_name}?key={
                        api_key}"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            values = data.get('values', [])

            if not values:
                return pd.DataFrame()

            # Primeira linha como cabeçalho
            headers = values[0]
            rows = values[1:]

            # Verificar se há dados
            if not rows:
                return pd.DataFrame()

            # Encontrar o número máximo de colunas
            max_cols = max(len(headers), max(len(row)
                           for row in rows) if rows else 0)

            # Ajustar headers para ter o mesmo número de colunas
            while len(headers) < max_cols:
                headers.append(f'Col_{len(headers)}')

            # Resolver nomes de colunas duplicados
            seen_headers = {}
            unique_headers = []

            for header in headers[:max_cols]:
                if header in seen_headers:
                    seen_headers[header] += 1
                    unique_headers.append(f"{header}_{seen_headers[header]}")
                else:
                    seen_headers[header] = 0
                    unique_headers.append(header)

            # Ajustar todas as linhas para ter o mesmo número de colunas
            normalized_rows = []
            for row in rows:
                # Preencher com strings vazias se a linha for menor
                while len(row) < max_cols:
                    row.append('')
                # Truncar se a linha for maior
                normalized_rows.append(row[:max_cols])

            # Criar DataFrame com headers únicos
            df = pd.DataFrame(normalized_rows, columns=unique_headers)

            # Remover linhas completamente vazias
            df = df.dropna(how='all')

            return df

        except Exception as e:
            st.error(
                f"Erro ao carregar dados da planilha {sheet_name}: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def load_all_data(config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Carrega todos os dados das planilhas configuradas"""
        data = {}

        with st.spinner("Carregando dados das planilhas..."):
            # Carregar dados dos polos ativos
            polos_config = config['planilha_polos']
            data['polos_ativos'] = GoogleSheetsLoader.load_sheet_data(
                polos_config['API_KEY'],
                polos_config['SHEET_ID'],
                polos_config['abas']['polos_ativos']
            )

            # Carregar dados dos municípios
            data['municipios'] = GoogleSheetsLoader.load_sheet_data(
                polos_config['API_KEY'],
                polos_config['SHEET_ID'],
                polos_config['abas']['municipios']
            )

            # Carregar dados dos alunos
            alunos_config = config['planilha_alunos']
            data['alunos'] = GoogleSheetsLoader.load_sheet_data(
                alunos_config['API_KEY'],
                alunos_config['SHEET_ID'],
                alunos_config['abas']['alunos_dados']
            )

        return data
