# Imports internos
from utils.visualizations import Visualizations
from utils.data_processor import DataProcessor
from utils.data_loader import GoogleSheetsLoader
from config import GOOGLE_SHEETS_CONFIG, COLORS, MAP_CONFIG

# Imports das páginas
from pages.geographic_analysis import GeographicAnalysis
from pages.municipalities_analysis import MunicipalitiesAnalysis
from pages.coverage_analysis import CoverageAnalysis
from pages.students_analysis import StudentsAnalysis
from pages.alignment_analysis import AlignmentAnalysis

# Imports externos
import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Análise Macro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
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


@st.cache_data(ttl=300)  # Cache por 5 minutos
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
    st.markdown(
        '<h1 class="main-header">🎓 Dashboard de Análise Macro</h1>',
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
            "Erro. Verifique as configurações das APIs.")
        return

    # Exibir métricas principais
    display_metrics(polos_df, municipios_df, alunos_df)

    # Criar instância de visualizações
    viz = Visualizations(COLORS)

    # Seções do dashboard
    sections = {
        "📍 Análise Geográfica dos Polos": GeographicAnalysis,
        "📊 Análise de Municípios e Alunos": MunicipalitiesAnalysis,
        "🎯 Análise de Cobertura e Eficiência": CoverageAnalysis,
        "👥 Análise de Alunos e Cursos": StudentsAnalysis,
        "🔄 Análise de Alinhamento de Polos": AlignmentAnalysis
    }

    selected_section = st.sidebar.selectbox(
        "Selecione a seção:", list(sections.keys()))

    # Executar a seção selecionada
    section_class = sections[selected_section]
    section_instance = section_class(viz, MAP_CONFIG)
    section_instance.render(polos_df, municipios_df, alunos_df)

    # Rodapé
    st.markdown("---")
    st.markdown("""
    ### 📊 Informações do Dashboard
    **Dados atualizados automaticamente das planilhas Google Sheets**
    **Tecnologias utilizadas:** Streamlit, Plotly, Folium, Pandas
    """)


if __name__ == "__main__":
    main()
