import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io
# Adicionado para gráficos profissionais

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
st.set_page_config(page_title="Financeiro Ultimate", layout="wide", page_icon="💎")

def conectar():
    return sqlite3.connect('financas_ultimate.db', check_same_thread=False)

def inicializar_db():
    conn = conectar()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, descricao TEXT, 
                  categoria TEXT, tipo TEXT, valor REAL)''')
    conn.commit()
    conn.close()

# --- LOGICA ---
def salvar_transacao(d, desc, cat, t, v):
    conn = conectar()
    conn.execute('INSERT INTO transacoes (data, descricao, categoria, tipo, valor) VALUES (?,?,?,?,?)', (d, desc, cat, t, v))
    conn.commit()
    conn.close()

def excluir_transacao(id_transacao):
    conn = conectar()
    conn.execute('DELETE FROM transacoes WHERE id = ?', (id_transacao,))
    conn.commit()
    conn.close()

def carregar_dados():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM transacoes", conn)
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['AnoMes'] = df['data'].dt.strftime('%Y-%m')
    return df

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso Restrito")
    with st.container():
        senha = st.text_input("Senha do Sistema:", type="password")
        if st.button("Acessar Painel"):
            if senha == "admin123":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha inválida.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
inicializar_db()
st.title("💎 Gestão Financeira Ultimate")

# SIDEBAR
with st.sidebar:
    st.header("👤 Perfil: Administrador")
    if st.button("Deslogar"):
        st.session_state.autenticado = False
        st.rerun()
    
    st.divider()
    st.subheader("📝 Novo Lançamento")
    with st.form("form_add", clear_on_submit=True):
        d = st.date_input("Data", date.today())
        desc = st.text_input("Descrição")
        cat = st.selectbox("Categoria", ["Salário", "Lazer", "Contas Fixas", "Alimentação", "Transporte", "Saúde", "Educação", "Outros"])
        tipo = st.radio("Tipo", ["Entrada", "Saída"])
        val = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Confirmar Lançamento"):
            if desc and val > 0:
                salvar_transacao(str(d), desc, cat, tipo, val)
                st.rerun()

# PROCESSAMENTO DE DADOS
df_completo = carregar_dados()

if not df_completo.empty:
    meses = ["Todos"] + sorted(df_completo['AnoMes'].unique().tolist(), reverse=True)
    mes_sel = st.sidebar.selectbox("Filtrar Período", meses)
    df = df_completo[df_completo['AnoMes'] == mes_sel] if mes_sel != "Todos" else df_completo

    # DASHBOARD DE MÉTRICAS
    rec = df[df['tipo'] == 'Entrada']['valor'].sum()
    desp = df[df['tipo'] == 'Saída']['valor'].sum()
    saldo = rec - desp
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ganhos Totais", f"R$ {rec:,.2f}")
    m2.metric("Gastos Totais", f"R$ {desp:,.2f}", f"-{desp:,.2f}", delta_color="inverse")
    m3.metric("Saldo do Período", f"R$ {saldo:,.2f}")

    st.divider()

    # ABAS
    tab_visão, tab_analise, tab_gestao = st.tabs(["📊 Visão Geral", "🎯 Análise por Categoria", "⚙️ Gerenciar Dados"])

    with tab_visão:
        st.subheader("Evolução Diária do Saldo")
        df_ev = df.sort_values('data')
        df_ev['v_adj'] = df_ev.apply(lambda x: x['valor'] if x['tipo'] == 'Entrada' else -x['valor'], axis=1)
        df_ev['Acumulado'] = df_ev['v_adj'].cumsum()
        fig_evolucao = px.line(df_ev, x='data', y='Acumulado', title='Linha de Patrimônio')
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with tab_analise:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write("**Distribuição de Gastos (Saídas)**")
            df_saidas = df[df['tipo'] == 'Saída']
            if not df_saidas.empty:
                fig_pizza = px.pie(df_saidas, values='valor', names='categoria', hole=0.4)
                st.plotly_chart(fig_pizza, use_container_width=True)
            else: st.info("Sem gastos registrados.")
            
        with col_p2:
            st.write("**Metas de Orçamento**")
            limite = 2000.0 # Exemplo de meta global
            st.write(f"Limite Mensal Sugerido: R$ {limite:,.2f}")
            st.progress(min(desp/limite, 1.0))

    with tab_gestao:
        st.subheader("Histórico Detalhado (Clique em excluir para remover)")
        for i, row in df.sort_values('data', ascending=False).iterrows():
            c_d, c_desc, c_v, c_b = st.columns([1, 2, 1, 1])
            c_d.write(row['data'].strftime('%d/%m/%Y'))
            c_desc.write(row['descricao'])
            cor = "green" if row['tipo'] == "Entrada" else "red"
            c_v.write(f":{cor}[R$ {row['valor']:,.2f}]")
            if c_b.button("🗑️", key=f"btn_{row['id']}"):
                excluir_transacao(row['id'])
                st.rerun()

else:
    st.info("👋 Bem-vindo! Comece lançando sua primeira receita ou despesa na barra lateral.")