from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, LpStatus
from typing import List, Dict, Any
from src.models import Product
from src.analytics import calculate_optimal_price_and_demand


def optimize_purchasing_plan(
    products: List[Product], budget: float, risk_appetite: float
) -> Dict[str, Any]:

    prob = LpProblem("ProfitMax_Engine", LpMaximize)

    variables = {}
    meta_data = {}
    skipped_products = []

    for p in products:
        cost = p["supplier_cost"]
        op_cost = p["operational_cost"]
        stock = p["stock_on_hand"]
        committed_orders = p["min_order_qty"]

        # --- 1. DEFINIÇÃO DA DEMANDA TOTAL---

        opt_price, opt_demand = calculate_optimal_price_and_demand(p["history"], cost)

        total_demand_ceiling = 0
        final_price = 0.0
        source = ""
        analyzable = False

        if opt_price is not None and opt_demand > 0:
            final_price = opt_price
            total_demand_ceiling = int(opt_demand * 1.2)
            source = "IA (Histórico)"
            analyzable = True
        elif p["manual_sales_estimate"] > 0:
            final_price = p["target_sell_price"]
            total_demand_ceiling = int(p["manual_sales_estimate"])
            source = "Manual (Estimativa)"
            analyzable = True
        else:
            # Se não tem estimativa, mas TEM compromisso agendado, o teto é o próprio compromisso
            if committed_orders > 0:
                final_price = p["target_sell_price"]
                total_demand_ceiling = committed_orders
                source = "Apenas Agendados"
                analyzable = True
            else:
                skipped_products.append(f"{p['name']} (Sem dados)")
                analyzable = False

        if not analyzable:
            continue
        total_demand_ceiling = max(total_demand_ceiling, committed_orders)

        # --- 2. APLICAÇÃO DO RISCO ---

        upside = total_demand_ceiling - committed_orders
        allowed_demand = committed_orders + (upside * risk_appetite)
        allowed_demand = int(allowed_demand)

        # --- 3. DEFINIÇÃO DE NECESSIDADE DE COMPRA ---
        must_buy = max(0, committed_orders - stock)
        can_buy = max(0, allowed_demand - stock)
        if can_buy == 0:
            var_min = 0
            var_max = 0
        else:
            var_min = must_buy
            var_max = can_buy

        # Variável de Decisão
        var_name = f"qty_{p['id']}"
        x = LpVariable(var_name, lowBound=var_min, upBound=var_max, cat="Integer")

        variables[p["id"]] = x

        # Função Objetivo (Lucro Líquido)
        unit_profit = final_price - (cost + op_cost)
        prob += x * unit_profit

        meta_data[p["id"]] = {
            "name": p["name"],
            "cost": cost,
            "op_cost": op_cost,
            "final_price": final_price,
            "real_profit": unit_profit,
            "source": source,
        }

    # Restrição Orçamentária
    if variables:
        prob += (
            lpSum([variables[pid] * meta_data[pid]["cost"] for pid in variables])
            <= budget
        )

        prob.solve(PULP_CBC_CMD(msg=0))
    else:
        return {"status": "Error", "message": "Nenhum produto analisável.", "data": []}

    results = []

    # Tratamento se não houver dinheiro para os pedidos agendados
    status = LpStatus[prob.status]
    if status != "Optimal":
        return {
            "status": status,
            "data": [],
            "skipped": skipped_products,
            "message": "Orçamento insuficiente para cobrir as vendas já agendadas!",
        }

    for pid in variables:
        qty = int(variables[pid].varValue)
        if qty > 0:
            d = meta_data[pid]
            results.append(
                {
                    "Produto": d["name"],
                    "Qtd Compra": qty,
                    "Custo Unit": d["cost"],
                    "Custo Operacional": d["op_cost"],
                    "Preço Venda": d["final_price"],
                    "Investimento Total": qty * d["cost"],
                    "Lucro Previsto": qty * d["real_profit"],
                    "Base Decisão": d["source"],
                }
            )

    return {"status": status, "data": results, "skipped": skipped_products}
