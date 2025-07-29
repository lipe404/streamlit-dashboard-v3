"""
Módulo de páginas do dashboard
"""


class BasePage:
    """Classe base para todas as páginas do dashboard"""

    def __init__(self, viz, map_config):
        self.viz = viz
        self.map_config = map_config

    def render(self, polos_df, municipios_df, alunos_df):
        """Método que deve ser implementado por cada página"""
        raise NotImplementedError(
            "Cada página deve implementar o método render")

    def check_data_availability(self, df, data_name):
        """Verifica se os dados estão disponíveis"""
        if df.empty:
            import streamlit as st
            st.warning(f"Dados de {data_name} não disponíveis.")
            return False
        return True
