import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.persistence import load_state, save_state
from src.solver import optimize_purchasing_plan
from src.analytics import analyze_price_elasticity

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="ProfitMax Pro", layout="wide", page_icon="📈")

# CSS para métricas e tabelas bonitas
st.markdown(
    """
<style>
    .metric-card { 
        background-color: #f8f9fa; 
        border: 1px solid #dee2e6; 
        border-radius: 8px; 
        padding: 20px; 
        text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }
    .metric-title { color: #6c757d; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .metric-value { color: #212529; font-size: 2rem; font-weight: 700; }
    .metric-delta { font-size: 1rem; font-weight: 600; margin-top: 5px; }
    
    /* Cores para badges */
    .badge-a { background-color: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-b { background-color: #fff3e0; color: #ef6c00; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-c { background-color: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNÇÕES AUXILIARES ---
def calculate_abc_class(products):
    """Classifica produtos em A (80%), B (15%) e C (5%) do faturamento potencial"""
    if not products:
        return {}
    data = []
    for p in products:
        rev = p["target_sell_price"] * p["manual_sales_estimate"]
        data.append({"id": p["id"], "rev": rev})

    data.sort(key=lambda x: x["rev"], reverse=True)
    total = sum(d["rev"] for d in data)
    accumulated = 0
    mapping = {}

    for item in data:
        accumulated += item["rev"]
        perc = accumulated / total if total > 0 else 0
        if perc <= 0.80:
            mapping[item["id"]] = "A"
        elif perc <= 0.95:
            mapping[item["id"]] = "B"
        else:
            mapping[item["id"]] = "C"
    return mapping


if "app_state" not in st.session_state:
    st.session_state.app_state = load_state()
state = st.session_state.app_state

if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None
if "editing_product_id" not in st.session_state:
    st.session_state.editing_product_id = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Ajustes Globais")

    # Orçamento
    state["budget"] = st.number_input(
        "💰 Orçamento (R$)", value=state["budget"], step=500.0
    )

    # Apetite ao Risco (Slider atualizado)
    st.markdown("### 🎚️ Apetite ao Risco")
    state["risk_factor"] = st.slider(
        "Nível de Agressividade",
        0.0,
        1.0,
        state["risk_factor"],
        help="0% = Compra só o mínimo garantido. 100% = Compra até o teto máximo de vendas estimado.",
    )

    # Legenda Dinâmica
    if state["risk_factor"] == 0.0:
        st.caption("🛡️ Modo: Conservador (Mínimos)")
    elif state["risk_factor"] == 1.0:
        st.caption("🚀 Modo: Agressivo (Máximo Potencial)")
    else:
        st.caption("⚖️ Modo: Moderado (Equilibrado)")

    st.markdown("---")
    if st.button("💾 Salvar Dados"):
        save_state(state)
        st.toast("Dados salvos com sucesso!", icon="✅")

tab_dashboard, tab_produtos, tab_pricing = st.tabs(
    ["📊 Painel Estratégico", "📦 Gestão de Produtos", "🧠 Laboratório de Preço"]
)

# ================= TAB 1: DASHBOARD (ATUALIZADO) =================
with tab_dashboard:
    st.title("Painel de Decisão & Lucratividade")
    st.markdown(
        "**Regra de Ouro:** A IA tem prioridade absoluta. Se não houver histórico, usamos sua estimativa manual. Se a estimativa for 0 e não houver histórico, o produto é ignorado."
    )

    if st.button(
        "🚀 CALCULAR PLANO DE COMPRA", type="primary", use_container_width=True
    ):
        if not state["products"]:
            st.error("Cadastre produtos primeiro.")
        else:
            with st.spinner("Analisando dados e restrições..."):
                res = optimize_purchasing_plan(
                    state["products"], state["budget"], state["risk_factor"]
                )
                st.session_state.optimization_result = res

    result = st.session_state.optimization_result

    # --- EXIBIÇÃO DE ERROS/AVISOS ---
    if result and "skipped" in result and result["skipped"]:
        st.warning(
            f"⚠️ Atenção: {len(result['skipped'])} produtos foram ignorados pois não possuem histórico nem estimativa manual de venda (>0)."
        )
        with st.expander("Ver produtos ignorados"):
            for skip in result["skipped"]:
                st.write(f"- {skip}")

    if result and result["status"] == "Optimal" and result["data"]:
        df = pd.DataFrame(result["data"])

        # --- LÓGICA COMPARATIVA ---
        total_lucro_manual = 0
        total_lucro_ia = 0
        comparativo = []

        for _, row in df.iterrows():
            prod_original = next(
                p for p in state["products"] if p["name"] == row["Produto"]
            )

            qtd_otima = row["Qtd Compra"]
            custo_full = row["Custo Unit"] + row["Custo Operacional"]

            # Cenário 1: Preço Manual (Seu Alvo)
            preco_manual = prod_original["target_sell_price"]
            lucro_manual_item = (preco_manual - custo_full) * qtd_otima

            # Cenário 2: Preço IA (Ou Manual se a IA não atuou)
            preco_ia = row["Preço Venda"]
            lucro_ia_item = row["Lucro Previsto"]

            total_lucro_manual += lucro_manual_item
            total_lucro_ia += lucro_ia_item

            source_label = row["Base Decisão"]

            comparativo.append(
                {
                    "Produto": row["Produto"],
                    "Volume": qtd_otima,
                    "Decisão Baseada em": source_label,
                    "Seu Preço": preco_manual,
                    "Preço Otimizado": preco_ia,
                    "Lucro (Seu Preço)": lucro_manual_item,
                    "Lucro (Otimizado)": lucro_ia_item,
                    "Ganho Extra": lucro_ia_item - lucro_manual_item,
                }
            )

        df_comp = pd.DataFrame(comparativo)
        delta = total_lucro_ia - total_lucro_manual

        # --- CARDS KPI ---
        c1, c2, c3 = st.columns(3)

        c1.markdown(
            f"""
        <div class="metric-card" style="border-left: 5px solid #607d8b;">
            <div class="metric-title">Lucro c/ Seu Preço</div>
            <div class="metric-value">R$ {total_lucro_manual:,.2f}</div>
            <div class="metric-delta">Volume Sugerido</div>
        </div>""",
            unsafe_allow_html=True,
        )

        color_delta = "#2e7d32" if delta >= 0 else "#c62828"
        symbol = "+" if delta >= 0 else ""
        c2.markdown(
            f"""
        <div class="metric-card" style="border-left: 5px solid {color_delta};">
            <div class="metric-title">Lucro Otimizado</div>
            <div class="metric-value">R$ {total_lucro_ia:,.2f}</div>
            <div class="metric-delta" style="color:{color_delta}">{symbol} R$ {delta:,.2f} vs Manual</div>
        </div>""",
            unsafe_allow_html=True,
        )

        inv_total = df["Investimento Total"].sum()
        roi = (total_lucro_ia / inv_total * 100) if inv_total > 0 else 0
        c3.markdown(
            f"""
        <div class="metric-card" style="border-left: 5px solid #1565c0;">
            <div class="metric-title">Investimento Total</div>
            <div class="metric-value">R$ {inv_total:,.2f}</div>
            <div class="metric-delta">ROI Projetado: {roi:.1f}%</div>
        </div>""",
            unsafe_allow_html=True,
        )

        st.divider()

        # --- TABELA PRINCIPAL DE COMPARAÇÃO ---
        st.subheader("📋 Detalhe da Decisão (Preço Manual vs IA)")
        st.dataframe(
            df_comp[
                [
                    "Produto",
                    "Volume",
                    "Decisão Baseada em",
                    "Seu Preço",
                    "Preço Otimizado",
                    "Lucro (Seu Preço)",
                    "Lucro (Otimizado)",
                    "Ganho Extra",
                ]
            ]
            .style.format(
                {
                    "Seu Preço": "R$ {:.2f}",
                    "Preço Otimizado": "R$ {:.2f}",
                    "Lucro (Seu Preço)": "R$ {:.2f}",
                    "Lucro (Otimizado)": "R$ {:.2f}",
                    "Ganho Extra": "+ R$ {:.2f}",
                }
            )
            .background_gradient(subset=["Ganho Extra"], cmap="Greens"),
            use_container_width=True,
        )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("⚡ Giro Rápido (Volume)")
            st.dataframe(
                df_comp.sort_values("Volume", ascending=False).head(3)[
                    ["Produto", "Volume", "Preço Otimizado"]
                ],
                use_container_width=True,
            )

        with col_t2:
            st.subheader("💎 Top Margem (Por Unidade)")
            df_comp["Margem Unit"] = df_comp["Lucro (Otimizado)"] / df_comp["Volume"]
            st.dataframe(
                df_comp.sort_values("Margem Unit", ascending=False)
                .head(3)[["Produto", "Margem Unit"]]
                .style.format({"Margem Unit": "R$ {:.2f}"}),
                use_container_width=True,
            )

    elif result and "message" in result:
        st.error(result["message"])
    elif result:
        st.warning("O orçamento é insuficiente para cobrir as compras mínimas.")
# =========================================================
# TAB 2: GESTÃO DE PRODUTOS (CRUD)
# =========================================================
with tab_produtos:
    # --- FORMULÁRIO DE EDIÇÃO/CRIAÇÃO ---
    edit_idx = None
    edit_data = {}

    if st.session_state.editing_product_id:
        for idx, p in enumerate(state["products"]):
            if p["id"] == st.session_state.editing_product_id:
                edit_idx = idx
                edit_data = p
                break

    def_name = edit_data.get("name", "")
    def_cost = edit_data.get("supplier_cost", 0.0)
    def_op_cost = edit_data.get("operational_cost", 0.0)
    def_min = edit_data.get("min_order_qty", 1)
    def_lead = edit_data.get("lead_time_days", 7)
    def_stock = edit_data.get("stock_on_hand", 0)
    def_target = edit_data.get("target_sell_price", 0.0)
    def_est = edit_data.get("manual_sales_estimate", 0)

    form_label = (
        f"✏️ Editando: {def_name}"
        if st.session_state.editing_product_id
        else "➕ Adicionar Novo Produto"
    )

    with st.expander(form_label, expanded=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome do Produto", value=def_name)

        st.markdown("**Custos & Logística**")
        r1 = st.columns(4)
        cost = r1[0].number_input(
            "Custo Forn. (R$)", 0.0, value=float(def_cost), format="%.2f"
        )
        op_cost = r1[1].number_input(
            "Custo Op. (R$)", 0.0, value=float(def_op_cost), format="%.2f"
        )

        # MUDANÇA AQUI:
        min_qty = r1[2].number_input(
            "Vendas Agendadas (Un)",
            0,
            value=int(def_min),
            help="Quantidade que você JÁ vendeu/comprometeu e PRECISA comprar para entregar.",
        )

        lead_time = r1[3].number_input("Prazo (Dias)", 1, value=int(def_lead))

        st.markdown("**Vendas & Estratégia**")
        r2 = st.columns(3)
        stock = r2[0].number_input("Estoque Atual", 0, value=int(def_stock))
        target_price = r2[1].number_input(
            "Preço Alvo (R$)", 0.0, value=float(def_target), format="%.2f"
        )
        manual_est = r2[2].number_input("Est. Venda (Un)", 0, value=int(def_est))

        # Ações do Formulário
        col_act = st.columns([1, 5])
        if st.session_state.editing_product_id:
            if col_act[0].button("💾 Atualizar", type="primary"):
                state["products"][edit_idx].update(
                    {
                        "name": name,
                        "supplier_cost": cost,
                        "operational_cost": op_cost,
                        "min_order_qty": min_qty,
                        "lead_time_days": lead_time,
                        "stock_on_hand": stock,
                        "target_sell_price": target_price,
                        "manual_sales_estimate": manual_est,
                    }
                )
                st.session_state.editing_product_id = None
                st.rerun()
            if col_act[1].button("Cancelar"):
                st.session_state.editing_product_id = None
                st.rerun()
        else:
            if col_act[0].button("Cadastrar", type="primary"):
                if name and cost > 0:
                    state["products"].append(
                        {
                            "id": str(pd.Timestamp.now().timestamp()),
                            "name": name,
                            "supplier_cost": cost,
                            "operational_cost": op_cost,
                            "min_order_qty": min_qty,
                            "lead_time_days": lead_time,
                            "stock_on_hand": stock,
                            "target_sell_price": target_price,
                            "manual_sales_estimate": manual_est,
                            "history": [],
                        }
                    )
                    st.toast("Produto cadastrado!")
                    st.rerun()
                else:
                    st.error("Preencha Nome e Custo corretamente.")

    # --- LISTAGEM ---
    st.divider()
    st.markdown("### Catálogo de Produtos")
    abc_map = calculate_abc_class(state["products"])

    for i, p in enumerate(state["products"]):
        with st.container(border=True):
            cls = abc_map.get(p["id"], "C")
            css_class = f"badge-{cls.lower()}"

            cols = st.columns([3, 2, 1, 1])

            # Coluna 1: Info Principal
            cols[0].markdown(
                f"**{p['name']}** <span class='{css_class}'>Classe {cls}</span>",
                unsafe_allow_html=True,
            )
            cols[0].caption(
                f"Estoque: {p['stock_on_hand']} | Prazo: {p['lead_time_days']} dias"
            )

            # Coluna 2: Dados Financeiros & Upload
            margem = p["target_sell_price"] - p["supplier_cost"] - p["operational_cost"]
            cor_m = "green" if margem > 0 else "red"
            cols[1].markdown(f"Margem Manual: :{cor_m}[R$ {margem:.2f}]")

            up = cols[1].file_uploader(
                "Histórico CSV",
                type="csv",
                key=f"up_{p['id']}",
                label_visibility="collapsed",
            )
            if up:
                try:
                    df = pd.read_csv(up)
                    hist = [
                        {
                            "period": str(r.get("mes", "")),
                            "quantity": int(r["quantidade"]),
                            "unit_price": float(r["valor"]),
                        }
                        for _, r in df.iterrows()
                    ]
                    state["products"][i]["history"] = hist
                    st.toast("Histórico importado!")
                except:
                    pass

            # Coluna 3 e 4: Ações
            if cols[2].button("✏️", key=f"ed_{p['id']}"):
                st.session_state.editing_product_id = p["id"]
                st.rerun()

            if cols[3].button("🗑️", key=f"dl_{p['id']}"):
                state["products"].pop(i)
                st.rerun()

# =========================================================
# TAB 3: LABORATÓRIO DE PREÇO (IA)
# =========================================================
with tab_pricing:
    st.title("🧠 Simulador de Elasticidade de Preço")
    st.markdown("Veja como a IA enxerga a sensibilidade de preço dos seus clientes.")

    prods_with_hist = [p for p in state["products"] if len(p["history"]) >= 3]

    if not prods_with_hist:
        st.info(
            "Para habilitar este módulo, cadastre produtos e faça upload de CSV com histórico (mín. 3 meses)."
        )
    else:
        sel_name = st.selectbox(
            "Selecione o Produto", [p["name"] for p in prods_with_hist]
        )
        sel_prod = next(p for p in prods_with_hist if p["name"] == sel_name)

        # Análise de IA
        res = analyze_price_elasticity(sel_prod["history"], sel_prod["supplier_cost"])

        if res["valid"]:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(
                "Preço Alvo (Manual)", f"R$ {sel_prod['target_sell_price']:.2f}"
            )
            col_b.metric(
                "Preço Ótimo (IA)",
                f"R$ {res['optimal_price']:.2f}",
                delta=f"{res['optimal_price'] - sel_prod['target_sell_price']:.2f}",
            )
            col_c.metric(
                "Elasticidade",
                f"{res['elasticity']:.2f}",
                help="Se < -1, o cliente é muito sensível a preço.",
            )

            # Gráfico Plotly
            chart = res["chart_data"]
            fig = go.Figure()

            # Linha de Lucro
            fig.add_trace(
                go.Scatter(
                    x=chart["prices"],
                    y=chart["profits"],
                    mode="lines",
                    name="Curva de Lucro Estimado",
                    line=dict(color="#2e7d32", width=3),
                )
            )

            # Marcador do Ponto Ótimo
            lucro_otimo = (res["optimal_price"] - sel_prod["supplier_cost"]) * res[
                "optimal_qty"
            ]
            fig.add_trace(
                go.Scatter(
                    x=[res["optimal_price"]],
                    y=[lucro_otimo],
                    mode="markers",
                    name="Ponto Ótimo",
                    marker=dict(color="red", size=15, symbol="star"),
                )
            )

            fig.update_layout(
                title="Projeção: Lucro Total vs Preço de Venda",
                xaxis_title="Preço de Venda (R$)",
                yaxis_title="Lucro do Lote (R$)",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(
                f"A IA não conseguiu traçar uma curva confiável: {res['reason']}"
            )
