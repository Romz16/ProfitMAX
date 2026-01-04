import json
import os
from typing import Dict, Any
from src.models import AppState

DB_FILE = "store_data.json"

DEFAULT_STATE: AppState = {"budget": 5000.0, "risk_factor": 0.5, "products": []}


def sanitize_product(prod: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função de Migração: Garante que produtos criados em versões
    antigas recebam os novos campos com valores padrão.
    """
    defaults = {
        "operational_cost": 0.0,
        "stock_on_hand": 0,
        "lead_time_days": 0,
        "target_sell_price": 0.0,
        "manual_sales_estimate": 0,
        "min_order_qty": 1,
        "supplier_cost": 0.0,
    }

    # Para cada campo novo, se não existir no produto, cria com valor padrão
    for key, default_value in defaults.items():
        if key not in prod:
            prod[key] = default_value

    return prod


def load_state() -> AppState:
    if not os.path.exists(DB_FILE):
        return DEFAULT_STATE

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

            # Garante que a chave 'products' exista
            if "products" not in state:
                state["products"] = []

            # Aplica a correção (sanitização) em cada produto carregado
            state["products"] = [sanitize_product(p) for p in state["products"]]

            # Garante chaves globais
            if "budget" not in state:
                state["budget"] = 5000.0
            if "risk_factor" not in state:
                state["risk_factor"] = 0.5

            return state

    except (json.JSONDecodeError, IOError):
        return DEFAULT_STATE


def save_state(state: AppState) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
