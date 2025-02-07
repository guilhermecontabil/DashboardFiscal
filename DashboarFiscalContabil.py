import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# A chamada de configuração da página deve ser a primeira instrução do app!
st.set_page_config(page_title="Dashboard Fiscal Avançada", layout="wide")

# --------------------------------------------------
# Injeção de CSS para customização avançada
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* Importa fontes modernas do Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Roboto&display=swap');

    /* Define a fonte padrão */
    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Fundo geral da aplicação */
    .main {
        background: #f0f2f6;
    }

    /* Estilização do header customizado */
    .header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Estilo para os contêineres de gráficos e dados */
    .chart-container, .data-container {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True
)

# --------------------------------------------------
# Header customizado com HTML
# --------------------------------------------------
components.html("""
<div class="header">
    <h1>Dashboard Fiscal Avançada</h1>
    <p>Visualize e interaja com os dados financeiros da sua empresa</p>
</div>
""", height=150)

# --------------------------------------------------
# Sidebar: Upload e filtros interativos
# --------------------------------------------------
st.sidebar.markdown("## Filtros de Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo XLSX", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Leitura do arquivo XLSX
        df = pd.read_excel(uploaded_file)
        
        # Verifica a existência da coluna MÊS
        if "MÊS" not in df.columns:
            st.error("A coluna 'MÊS' não foi encontrada no arquivo.")
            st.stop()

        # Converte a coluna MÊS para um objeto datetime (assumindo o formato 'YYYY-MM')
        try:
            df["Data"] = pd.to_datetime(df["MÊS"].astype(str) + "-01", format="%Y-%m-%d")
            df.sort_values("Data", inplace=True)
            x_axis = "Data"
        except Exception as e:
            st.warning("Não foi possível converter a coluna 'MÊS' para data. Usaremos os valores originais.")
            df.sort_values("MÊS", inplace=True)
            x_axis = "MÊS"

        # Filtro de intervalo de datas, caso a conversão para Data tenha ocorrido
        if x_axis == "Data":
            min_date = df["Data"].min().date()
            max_date = df["Data"].max().date()
            date_range = st.sidebar.date_input("Selecione o intervalo de datas", [min_date, max_date])
            if isinstance(date_range, list) and len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
        
        # Permite escolher as métricas a exibir
        st.sidebar.markdown("### Métricas para exibição")
        metrics_options = [
            "COMPRAS", "VENDAS", "DAS", "FOLHA", "PRO-LABORE", "FGTS",
            "MULTA FGTS", "RESCISÃO", "FÉRIAS", "13 SALARIO", "DCTFWEB",
            "Contrib. Assistencial", "ISSQN Retido", "CARTAO E PIX"
        ]
        selected_metrics = st.sidebar.multiselect("Selecione as métricas:", metrics_options, default=metrics_options)
        
        # --------------------------------------------------
        # Exibição dos dados carregados
        # --------------------------------------------------
        st.markdown("<div class='data-container'>", unsafe_allow_html=True)
        st.subheader("Visualização dos Dados (primeiras linhas)")
        st.dataframe(df.head())
        st.markdown("</div>", unsafe_allow_html=True)
        
        # --------------------------------------------------
        # Resumo Geral com cards de métricas
        # --------------------------------------------------
        st.markdown("## Resumo Geral")
        col1, col2, col3, col4 = st.columns(4)
        total_vendas = df["VENDAS"].sum() if "VENDAS" in df.columns else 0
        total_compras = df["COMPRAS"].sum() if "COMPRAS" in df.columns else 0
        total_das = df["DAS"].sum() if "DAS" in df.columns else 0
        total_folha = df["FOLHA"].sum() if "FOLHA" in df.columns else 0
        col1.metric("Total Vendas", f"R$ {total_vendas:,.2f}")
        col2.metric("Total Compras", f"R$ {total_compras:,.2f}")
        col3.metric("Total DAS", f"R$ {total_das:,.2f}")
        col4.metric("Total Folha", f"R$ {total_folha:,.2f}")
        
        # --------------------------------------------------
        # Criação de uma coluna de Despesas Totais
        # --------------------------------------------------
        despesas_list = [
            "COMPRAS", "DAS", "FOLHA", "PRO-LABORE", "FGTS", "MULTA FGTS",
            "RESCISÃO", "FÉRIAS", "13 SALARIO", "DCTFWEB", "Contrib. Assistencial", "ISSQN Retido", "CARTAO E PIX"
        ]
        despesas_selecionadas = [col for col in despesas_list if col in selected_metrics]
        if despesas_selecionadas:
            df["Despesas Totais"] = df[despesas_selecionadas].sum(axis=1)
        
        # --------------------------------------------------
        # Gráficos Interativos com Plotly Express
        # --------------------------------------------------

        # Gráfico 1: Evolução das Vendas
        if "VENDAS" in selected_metrics:
            fig_vendas = px.line(
                df, x=x_axis, y="VENDAS", 
                title="Evolução das Vendas",
                markers=True, template="plotly_white"
            )
            fig_vendas.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vendas, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 2: Vendas vs DAS
        if all(m in selected_metrics for m in ["VENDAS", "DAS"]):
            fig_vdas = px.line(
                df, x=x_axis, y=["VENDAS", "DAS"],
                title="Vendas vs DAS",
                markers=True, template="plotly_white"
            )
            fig_vdas.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vdas, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 3: Vendas vs Compras
        if all(m in selected_metrics for m in ["VENDAS", "COMPRAS"]):
            fig_vcompras = px.line(
                df, x=x_axis, y=["VENDAS", "COMPRAS"],
                title="Vendas vs Compras",
                markers=True, template="plotly_white"
            )
            fig_vcompras.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vcompras, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 4: Resumo Fiscal - Vendas vs Despesas Totais
        if "Despesas Totais" in df.columns and "VENDAS" in selected_metrics:
            fig_resumo = px.bar(
                df, x=x_axis, y=["VENDAS", "Despesas Totais"],
                title="Resumo Fiscal: Vendas vs Despesas Totais",
                barmode="group", template="plotly_white"
            )
            fig_resumo.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_resumo, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico Adicional: Comparativo de Outras Métricas (opcional)
        selected_other_metrics = [m for m in selected_metrics if m not in ["VENDAS", "COMPRAS", "DAS"]]
        if selected_other_metrics:
            fig_other = px.line(
                df, x=x_axis, y=selected_other_metrics,
                title="Comparativo de Outras Métricas",
                markers=True, template="plotly_white"
            )
            fig_other.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_other, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.sidebar.info("Aguardando o upload de um arquivo XLSX.")
    st.info("Utilize a barra lateral para carregar o arquivo e configurar os filtros.")
