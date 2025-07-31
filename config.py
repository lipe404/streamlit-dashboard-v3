import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Certifique-se de que load_dotenv() seja chamado antes de tentar acessar as variáveis
load_dotenv()

# Função auxiliar para pegar a variável de ambiente ou retornar um erro claro


def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(
            f"Variável de ambiente '{name}' não configurada. Por favor, verifique seu arquivo .env ou as configurações de segredos do deploy.")
    return value


# Configurações das APIs e planilhas
GOOGLE_SHEETS_CONFIG = {
    'planilha_polos': {
        'API_KEY': get_env_var('GOOGLE_SHEETS_POLOS_API_KEY'),
        'SHEET_ID': get_env_var('GOOGLE_SHEETS_POLOS_SHEET_ID'),
        'abas': {
            'polos_ativos': 'POLOS ATIVOS',
            'municipios': 'Sheet3'
        }
    },
    'planilha_vendas': {
        'API_KEY': get_env_var('GOOGLE_SHEETS_VENDAS_API_KEY'),
        'SHEET_ID': get_env_var('GOOGLE_SHEETS_VENDAS_SHEET_ID'),
        'abas': {
            'base_vendas': 'Base de Vendas'
        }
    },
    'planilha_alunos': {
        'API_KEY': get_env_var('GOOGLE_SHEETS_ALUNOS_API_KEY'),
        'SHEET_ID': get_env_var('GOOGLE_SHEETS_ALUNOS_SHEET_ID'),
        'abas': {
            'alunos_dados': 'lista_alunos'
        }
    }
}

# Configurações de visualização
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff7f0e',
    'info': '#17a2b8',
    'purple': '#9467bd'
}

# Configurações do mapa
MAP_CONFIG = {
    'center_lat': -14.235,
    'center_lon': -51.925,
    'zoom': 4,
    'mapbox_style': 'open-street-map'
}
