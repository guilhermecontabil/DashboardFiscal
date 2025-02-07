import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# A chamada de configuração da página deve ser a primeira instrução!
st.set_page_config(page_title="Dashboard Fiscal Avançada", layout="wide")

# ------------------------------------------------------------------------------
# Função para converter a coluna MÊS tentando diferentes formatos
# ------------------------------------------------------------------------------
def converter_mes(valor):
    formatos = ["%Y-%m", "%m/%Y", "%B %Y", "%b %Y"]  # Ex: "2023-05", "05/2023", "Maio 2023", "May 2023"
    for fmt in formatos:
        try:
            return pd.to_datetime(valor, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT  # Retorna Not a Time se nenhum formato funcionar

# ------------------------------------------------------------------------------
# Função para formatar números no padrão de moeda brasileira (Real)
# ------------------------------------------------------------------------------
def format_brl(x):
    try:
        # Formata o número com vírgula como separador decimal e ponto para milhares.
        # Exemplo: 1234.56 -> R$ 1.234,56
        return "R$ " + format(x, ",.2f").replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return x

# ------------------------------------------------------------------------------
# Injeção de CSS para customização visual avançada
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Roboto&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
    }
    .main {
        background: #f0f2f6;
    }
    .header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #6a11cb, #2575fc);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
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

# ------------------------------------------------------------------------------
# Header customizado com HTML
# ------------------------------------------------------------------------------
components.html(
    """
    <div class="header">
        <h1>Dashboard Fiscal Avançada</h1>
        <p>Visualize e interaja com os dados financeiros da sua empresa</p>
    </div>
    """, 
    height=150
)

# ------------------------------------------------------------------------------
# Sidebar: Upload, filtros e seleção de métricas
# ------------------------------------------------------------------------------
st.sidebar.markdown("## Filtros de Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo XLSX", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Leitura do arquivo XLSX
        df = pd.read_excel(uploaded_file)
        
        # Verifica se a coluna MÊS existe
        if "MÊS" not in df.columns:
            st.error("A coluna 'MÊS' não foi encontrada no arquivo.")
            st.stop()
        
        # Converte a coluna MÊS para datetime utilizando a função personalizada
        df["Data"] = df["MÊS"].apply(converter_mes)
        if df["Data"].isnull().all():
            st.warning("Não foi possível converter a coluna 'MÊS' para data. Usaremos os valores originais.")
            x_axis = "MÊS"
            df.sort_values("MÊS", inplace=True)
        else:
            # Remove registros com Data inválida e ordena pela coluna Data
            df = df[df["Data"].notnull()]
            df.sort_values("Data", inplace=True)
            x_axis = "Data"
        
        # Filtro de intervalo de datas, caso a conversão tenha sido realizada
        if x_axis == "Data":
            min_date = df["Data"].min().date()
            max_date = df["Data"].max().date()
            date_range = st.sidebar.date_input("Selecione o intervalo de datas", [min_date, max_date])
            if isinstance(date_range, list) and len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
        
        # Lista de métricas disponíveis
        metrics_options = [
            "COMPRAS", "VENDAS", "DAS", "FOLHA", "PRO-LABORE", "FGTS",
            "MULTA FGTS", "RESCISÃO", "FÉRIAS", "13 SALARIO", "DCTFWEB",
            "Contrib. Assistencial", "ISSQN Retido", "CARTAO E PIX"
        ]
        # Checkbox para incluir todas as métricas
        include_all = st.sidebar.checkbox("Incluir todas as métricas", value=True)
        if include_all:
            selected_metrics = metrics_options
        else:
            selected_metrics = st.sidebar.multiselect("Selecione as métricas:", metrics_options, default=metrics_options)
        
        # ------------------------------------------------------------------------------
        # Visualização dos Dados: Tabela com a coluna MÊS e linha de total (formatação BRL)
        # ------------------------------------------------------------------------------
        st.markdown("<div class='data-container'>", unsafe_allow_html=True)
        st.subheader("Visualização dos Dados")
        # Cria uma cópia para exibição; remove a coluna 'Data' (utilizada apenas para filtros/gráficos)
        display_df = df.copy()
        if "Data" in display_df.columns:
            display_df.drop("Data", axis=1, inplace=True)
        
        # Adiciona uma linha de total para as colunas numéricas
        total_values = {}
        for col in display_df.columns:
            if pd.api.types.is_numeric_dtype(display_df[col]):
                total_values[col] = display_df[col].sum()
            else:
                # Exibe a palavra "Total" na coluna que contém o mês
                total_values[col] = "Total" if col == "MÊS" else ""
        total_df = pd.DataFrame(total_values, index=["Total"])
        display_df = pd.concat([display_df, total_df])
        
        # Aplica formatação BRL às células numéricas
        display_df = display_df.applymap(lambda x: format_brl(x) if isinstance(x, (int, float)) else x)
        st.dataframe(display_df)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # ------------------------------------------------------------------------------
        # Resumo Geral com cards de métricas
        # ------------------------------------------------------------------------------
        st.markdown("## Resumo Geral")
        col1, col2, col3, col4 = st.columns(4)
        total_vendas  = df["VENDAS"].sum()  if "VENDAS"  in df.columns else 0
        total_compras = df["COMPRAS"].sum() if "COMPRAS" in df.columns else 0
        total_das     = df["DAS"].sum()     if "DAS"     in df.columns else 0
        total_folha   = df["FOLHA"].sum()   if "FOLHA"   in df.columns else 0
        col1.metric("Total Vendas", format_brl(total_vendas))
        col2.metric("Total Compras", format_brl(total_compras))
        col3.metric("Total DAS", format_brl(total_das))
        col4.metric("Total Folha", format_brl(total_folha))
        
        # ------------------------------------------------------------------------------
        # Criação de uma coluna para Despesas Totais (soma das despesas selecionadas)
        # ------------------------------------------------------------------------------
        despesas_list = [
            "COMPRAS", "DAS", "FOLHA", "PRO-LABORE", "FGTS", "MULTA FGTS",
            "RESCISÃO", "FÉRIAS", "13 SALARIO", "DCTFWEB", "Contrib. Assistencial",
            "ISSQN Retido", "CARTAO E PIX"
        ]
        despesas_selecionadas = [col for col in despesas_list if col in selected_metrics]
        if despesas_selecionadas:
            df["Despesas Totais"] = df[despesas_selecionadas].sum(axis=1)
        
        # ------------------------------------------------------------------------------
        # Gráficos Interativos (com formatação BRL nos eixos)
        # ------------------------------------------------------------------------------
        
        # Gráfico 1: Evolução das Vendas
        if "VENDAS" in selected_metrics:
            fig_vendas = px.line(
                df, x=x_axis, y="VENDAS",
                title="Evolução das Vendas",
                markers=True,
                template="plotly_white"
            )
            fig_vendas.update_yaxes(tickprefix="R$ ")
            fig_vendas.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vendas, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 2: Vendas vs DAS
        if all(m in selected_metrics for m in ["VENDAS", "DAS"]):
            fig_vdas = px.line(
                df, x=x_axis, y=["VENDAS", "DAS"],
                title="Vendas vs DAS",
                markers=True,
                template="plotly_white"
            )
            fig_vdas.update_yaxes(tickprefix="R$ ")
            fig_vdas.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vdas, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 3: Vendas vs Compras
        if all(m in selected_metrics for m in ["VENDAS", "COMPRAS"]):
            fig_vcompras = px.line(
                df, x=x_axis, y=["VENDAS", "COMPRAS"],
                title="Vendas vs Compras",
                markers=True,
                template="plotly_white"
            )
            fig_vcompras.update_yaxes(tickprefix="R$ ")
            fig_vcompras.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_vcompras, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico 4: Resumo Fiscal - Vendas vs Despesas Totais
        if "Despesas Totais" in df.columns and "VENDAS" in selected_metrics:
            fig_resumo = px.bar(
                df, x=x_axis, y=["VENDAS", "Despesas Totais"],
                title="Resumo Fiscal: Vendas vs Despesas Totais",
                barmode="group",
                template="plotly_white"
            )
            fig_resumo.update_yaxes(tickprefix="R$ ")
            fig_resumo.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_resumo, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráfico adicional: Comparativo de Outras Métricas
        selected_other_metrics = [m for m in selected_metrics if m not in ["VENDAS", "COMPRAS", "DAS"]]
        if selected_other_metrics:
            fig_other = px.line(
                df, x=x_axis, y=selected_other_metrics,
                title="Comparativo de Outras Métricas",
                markers=True,
                template="plotly_white"
            )
            fig_other.update_yaxes(tickprefix="R$ ")
            fig_other.update_layout(transition_duration=500)
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.plotly_chart(fig_other, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.sidebar.info("Aguardando o upload de um arquivo XLSX.")
    st.info("Utilize a barra lateral para carregar o arquivo e configurar os filtros.")
