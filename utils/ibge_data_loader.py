import requests
import pandas as pd
import streamlit as st
import re  # Necessário para expressões regulares


class IBGEDataLoader:
    """Classe para carregar dados de APIs externas como IBGE."""

    # URL para população residente (Estimativas) - Agregado 6579, Variavel 9340 (População total)
    # Período 2022, Localidades N6 (Municípios)
    BASE_URL_POPULATION_V3 = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2022/variaveis/9340?localidades=N6[all]"
    # URL alternativa
    BASE_URL_POPULATION_V2 = "https://servicodados.ibge.gov.br/api/v2/agregados/6579/periodos/2022/variaveis/9340?localidades=N6[all]"

    @staticmethod
    @st.cache_data(ttl=3600*24*7)  # Cache por 1 semana
    def fetch_population_data() -> pd.DataFrame:
        """
        Busca dados de população dos municípios brasileiros no IBGE.
        Tenta a API v3 e, em caso de erro 500, tenta a v2.
        Retorna um DataFrame com 'codigo_ibge_completo', 'nome_municipio', 'uf', 'populacao'.
        """
        urls_to_try = [
            (IBGEDataLoader.BASE_URL_POPULATION_V3, "v3"),
            (IBGEDataLoader.BASE_URL_POPULATION_V2, "v2")
        ]

        for url, version in urls_to_try:
            try:
                st.info(
                    f"Tentando carregar dados de população do IBGE (versão {version})...")
                # Adiciona timeout de 10 segundos
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Lança exceção para erros HTTP (incluindo 5xx)
                data = response.json()

                if not data or not data[0].get('resultados'):
                    st.warning(
                        f"Nenhum dado válido encontrado na API do IBGE (versão {version}).")
                    continue  # Tenta a próxima URL

                population_list = []
                for item in data[0]['resultados'][0]['series']:
                    localidade_id = item['localidade']['id']
                    # Nome original da API
                    nome_municipio_api = item['localidade']['nome']

                    # Tenta pegar o valor de 2022; se não houver, tenta o último ano disponível
                    populacao_str = item['serie'].get('2022')
                    if populacao_str is None:
                        # Pega a última chave do dicionário 'serie'
                        last_year = list(item['serie'].keys())[-1]
                        populacao_str = item['serie'].get(last_year)
                        st.warning(
                            f"Dados de 2022 não encontrados para {nome_municipio_api}. Usando dados de {last_year}.")

                    populacao = int(populacao_str) if populacao_str else 0

                    # Extrair UF do nome_municipio (ex: "São Paulo (SP)")
                    uf_match = re.search(r'\((.*?)\)', nome_municipio_api)
                    uf = uf_match.group(1) if uf_match else 'N/A'

                    # Limpar nome_municipio para remover (UF)
                    nome_municipio_clean = re.sub(
                        r'\s\(.*\)', '', nome_municipio_api).strip()

                    population_list.append({
                        'codigo_ibge_completo': str(localidade_id),
                        # Nome limpo para merge, em maiúsculas
                        'MUNICIPIO_IBGE_CLEAN': nome_municipio_clean.upper(),
                        'UF': uf,
                        # Manter o nome da coluna como 2022 para consistência, mesmo que venha de outro ano
                        'POPULACAO_2022': populacao
                    })

                df_pop = pd.DataFrame(population_list)
                st.success(
                    f"Dados de população do IBGE (versão {version}) carregados com sucesso!")
                return df_pop  # Retorna o DataFrame se o carregamento for bem-sucedido

            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 500:
                    st.error(
                        f"Erro no servidor do IBGE (500 Internal Server Error) na versão {version}. Tentando alternativa...")
                else:
                    st.error(
                        f"Erro HTTP ao carregar dados do IBGE (versão {version}): {http_err}. Status: {response.status_code}")
                # Continua para a próxima URL em caso de erro HTTP
            except requests.exceptions.ConnectionError as conn_err:
                st.error(
                    f"Erro de conexão ao carregar dados do IBGE (versão {version}): {conn_err}. Verifique sua internet ou o status da API.")
                # Continua para a próxima URL
            except requests.exceptions.Timeout as timeout_err:
                st.error(
                    f"Tempo limite excedido ao carregar dados do IBGE (versão {version}): {timeout_err}. A conexão pode estar lenta.")
                # Continua para a próxima URL
            except requests.exceptions.RequestException as req_err:
                st.error(
                    f"Erro inesperado na requisição ao IBGE (versão {version}): {req_err}")
                # Continua para a próxima URL
            except Exception as e:
                st.error(
                    f"Erro ao processar dados da API do IBGE (versão {version}): {e}")
                # Continua para a próxima URL

        st.error(
            "Não foi possível carregar dados de população do IBGE após múltiplas tentativas. "
            "Por favor, verifique o status da API do IBGE e tente novamente mais tarde. "
            "[Link para a documentação da API do IBGE](https://servicodados.ibge.gov.br/api/docs/)"
        )
        return pd.DataFrame()  # Retorna DataFrame vazio se todas as tentativas falharem

    @staticmethod
    @st.cache_data(ttl=3600*24*7)  # Cache por 1 semana
    def get_additional_municipal_data() -> pd.DataFrame:
        """
        Simula a busca de dados adicionais (IDH, PIB) ou carrega de um CSV/API externa.
        Estes dados são fictícios para a demonstração e precisam ser substituídos por fontes reais.
        """
        # Dados fictícios para IDH e PIB para alguns municípios.
        # Estes dados são case-sensitive para o merge, por isso estão em MAIÚSCULAS para bater com MUNICIPIO_IBGE_CLEAN.
        data = [
            {'MUNICIPIO_IBGE_CLEAN': 'SÃO PAULO', 'UF': 'SP',
                'IDH_2010': 0.805, 'PIB_PER_CAPITA_2021': 60000},
            {'MUNICIPIO_IBGE_CLEAN': 'RIO DE JANEIRO', 'UF': 'RJ',
                'IDH_2010': 0.799, 'PIB_PER_CAPITA_2021': 55000},
            {'MUNICIPIO_IBGE_CLEAN': 'BELO HORIZONTE', 'UF': 'MG',
                'IDH_2010': 0.810, 'PIB_PER_CAPITA_2021': 50000},
            {'MUNICIPIO_IBGE_CLEAN': 'BRASÍLIA', 'UF': 'DF',
                'IDH_2010': 0.824, 'PIB_PER_CAPITA_2021': 90000},
            {'MUNICIPIO_IBGE_CLEAN': 'SALVADOR', 'UF': 'BA',
                'IDH_2010': 0.759, 'PIB_PER_CAPITA_2021': 25000},
            {'MUNICIPIO_IBGE_CLEAN': 'FORTALEZA', 'UF': 'CE',
                'IDH_2010': 0.732, 'PIB_PER_CAPITA_2021': 20000},
            {'MUNICIPIO_IBGE_CLEAN': 'PORTO ALEGRE', 'UF': 'RS',
                'IDH_2010': 0.805, 'PIB_PER_CAPITA_2021': 48000},
            {'MUNICIPIO_IBGE_CLEAN': 'CURITIBA', 'UF': 'PR',
                'IDH_2010': 0.810, 'PIB_PER_CAPITA_2021': 45000},
            {'MUNICIPIO_IBGE_CLEAN': 'RECIFE', 'UF': 'PE',
                'IDH_2010': 0.772, 'PIB_PER_CAPITA_2021': 28000},
            {'MUNICIPIO_IBGE_CLEAN': 'MANAUS', 'UF': 'AM',
                'IDH_2010': 0.737, 'PIB_PER_CAPITA_2021': 35000},
            {'MUNICIPIO_IBGE_CLEAN': 'CAMPINAS', 'UF': 'SP',
                'IDH_2010': 0.795, 'PIB_PER_CAPITA_2021': 65000},
            {'MUNICIPIO_IBGE_CLEAN': 'GOIÂNIA', 'UF': 'GO',
                'IDH_2010': 0.799, 'PIB_PER_CAPITA_2021': 40000},
            {'MUNICIPIO_IBGE_CLEAN': 'BELÉM', 'UF': 'PA',
                'IDH_2010': 0.746, 'PIB_PER_CAPITA_2021': 18000},
            {'MUNICIPIO_IBGE_CLEAN': 'SÃO LUÍS', 'UF': 'MA',
                'IDH_2010': 0.768, 'PIB_PER_CAPITA_2021': 22000},
            {'MUNICIPIO_IBGE_CLEAN': 'NATAL', 'UF': 'RN',
                'IDH_2010': 0.763, 'PIB_PER_CAPITA_2021': 20000},
            {'MUNICIPIO_IBGE_CLEAN': 'CAMPO GRANDE', 'UF': 'MS',
                'IDH_2010': 0.784, 'PIB_PER_CAPITA_2021': 38000},
            {'MUNICIPIO_IBGE_CLEAN': 'JOÃO PESSOA', 'UF': 'PB',
                'IDH_2010': 0.763, 'PIB_PER_CAPITA_2021': 19000},
            {'MUNICIPIO_IBGE_CLEAN': 'MACEIÓ', 'UF': 'AL',
                'IDH_2010': 0.721, 'PIB_PER_CAPITA_2021': 17000},
            {'MUNICIPIO_IBGE_CLEAN': 'TERESINA', 'UF': 'PI',
                'IDH_2010': 0.751, 'PIB_PER_CAPITA_2021': 15000},
            {'MUNICIPIO_IBGE_CLEAN': 'ARACAJU', 'UF': 'SE',
                'IDH_2010': 0.770, 'PIB_PER_CAPITA_2021': 16000},
        ]
        df_additional = pd.DataFrame(data)
        return df_additional
