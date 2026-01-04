import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import List, Tuple, Optional, Dict, Any
from src.models import SaleRecord


def analyze_price_elasticity(
    history: List[SaleRecord], current_cost: float
) -> Dict[str, Any]:
    # 1. Validações de Segurança
    if len(history) < 3:
        return {
            "valid": False,
            "reason": "Dados insuficientes (mínimo 3 meses de histórico).",
        }

    df = pd.DataFrame(history)

    if df["unit_price"].nunique() < 2:
        return {
            "valid": False,
            "reason": "Variação de preço insuficiente no histórico para análise.",
        }

    # 2. Treinamento do Modelo (Machine Learning)
    X = df[["unit_price"]].values
    y = df["quantity"].values

    model = LinearRegression()
    model.fit(X, y)

    elasticity = model.coef_[
        0
    ]  # Inclinação (a): Quanto a venda cai se o preço sobe R$ 1
    intercept = (
        model.intercept_
    )  # Intercepto (b): Venda base teórica se preço fosse R$ 0

    # 3. Detecção de Anomalias
    # Elasticidade >= 0 significa que aumentar o preço aumentou a venda (raro no varejo, indica ruído nos dados)
    if elasticity >= 0:
        return {
            "valid": False,
            "reason": "Comportamento anômalo detectado (Elasticidade Positiva). O modelo sugere usar a média simples.",
        }

    # 4. Otimização Matemática (Cálculo Numérico)
    # Fórmula do Preço Ótimo derivada de: d(Lucro)/dP = 0
    # P_otimo = (Custo - b/a) / 2
    optimal_price = (current_cost - (intercept / elasticity)) / 2

    # Trava de Segurança: O preço sugerido nunca pode ser menor que o custo + 10%
    optimal_price = max(optimal_price, current_cost * 1.1)

    # Previsão de demanda para esse preço ótimo
    optimal_qty = int(model.predict([[optimal_price]])[0])
    optimal_qty = max(0, optimal_qty)  # Não existe venda negativa

    # 5. Geração de Dados para o Gráfico (Simulação de Cenários)
    min_p = df["unit_price"].min() * 0.8
    max_p = df["unit_price"].max() * 1.5

    # Vetor de preços simulados
    price_range = np.linspace(min_p, max_p, 50).reshape(-1, 1)

    # Vetor de quantidades previstas para esses preços
    predicted_qty_range = model.predict(price_range)

    # Vetor de lucro previsto para esses preços
    # Lucro = (Preço Venda - Custo) * Quantidade
    projected_profit_range = (
        price_range.flatten() - current_cost
    ) * predicted_qty_range

    return {
        "valid": True,
        "model": model,
        "optimal_price": float(optimal_price),
        "optimal_qty": optimal_qty,
        "elasticity": elasticity,
        "chart_data": {
            "prices": price_range.flatten(),
            "quantities": predicted_qty_range,
            "profits": projected_profit_range,
        },
    }


def calculate_optimal_price_and_demand(
    history: List[SaleRecord], cost_price: float
) -> Tuple[Optional[float], int]:
    result = analyze_price_elasticity(history, cost_price)

    if result["valid"]:
        return result["optimal_price"], result["optimal_qty"]

    # Fallback: Se a IA falhar, retorna a média histórica
    if not history:
        return None, 0
    df = pd.DataFrame(history)
    return float(df["unit_price"].mean()), int(df["quantity"].mean())
