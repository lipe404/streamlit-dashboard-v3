# 🌍 Dashboard de Análise Macro

Um dashboard interativo desenvolvido em **Python** com **Streamlit**, integrado à **Google Sheets API**, para análise macro de polos, municípios, alunos e vendas.  
O projeto consolida dados geográficos, acadêmicos e comerciais, oferecendo **visualizações dinâmicas e relatórios estratégicos**.

🔗 Repositório: [streamlit-dashboard-v3](https://github.com/lipe404/streamlit-dashboard-v3)

---

## 🚀 Funcionalidades
- 📍 **Análise geográfica dos polos** com mapas interativos (Folium + Streamlit-Folium).  
- 📊 **Análise de municípios e alunos**, incluindo cobertura e distribuição.  
- 🎯 **Indicadores de cobertura e eficiência** para tomada de decisão.  
- 👥 **Análise detalhada de alunos e cursos.**  
- 🔄 **Alinhamento de polos e desempenho de vendas.**  
- 💰 **KPIs de vendas** em tempo real.  
- 🌟 **Relatórios de oportunidades** exportáveis.  
- ⚡ Cache inteligente de dados (`st.cache_data`) para performance.  

---

## 🛠️ Tecnologias utilizadas
- **Python 3.11+**  
- [Streamlit](https://streamlit.io/) — UI interativa  
- **Pandas, NumPy, GeoPandas, Shapely, PyProj** — análise de dados e geoprocessamento  
- **Plotly & Altair** — visualizações gráficas  
- **Folium & Streamlit-Folium** — mapas interativos  
- **Google Sheets API** — integração com bases de polos, alunos e vendas  
- **dotenv** — gerenciamento seguro de variáveis de ambiente  
- **OpenPyXL / PyArrow / Xlrd** — suporte a planilhas  

---

## 📂 Estrutura principal
📁 streamlit-dashboard-v3/
├── app.py # Ponto de entrada
├── config.py # Configurações e variáveis de ambiente
├── utils/ # Módulos auxiliares (data_loader, processor, visualizations)
├── app_sections/ # Seções de análise (geográfica, vendas, alunos, etc.)
├── requirements.txt # Dependências
└── .env.example # Exemplo de variáveis de ambiente


---

## ⚙️ Instalação e execução local
```bash
# Clonar repositório
git clone https://github.com/lipe404/streamlit-dashboard-v3.git
cd streamlit-dashboard-v3

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env a partir do exemplo
cp .env.example .env
# Adicionar suas chaves da Google Sheets API

# Executar
streamlit run app.py

🔑 Variáveis de ambiente (.env)
GOOGLE_SHEETS_POLOS_API_KEY=xxxx
GOOGLE_SHEETS_POLOS_SHEET_ID=xxxx
GOOGLE_SHEETS_VENDAS_API_KEY=xxxx
GOOGLE_SHEETS_VENDAS_SHEET_ID=xxxx
GOOGLE_SHEETS_ALUNOS_API_KEY=xxxx
GOOGLE_SHEETS_ALUNOS_SHEET_ID=xxxx

