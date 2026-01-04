from typing import List, TypedDict, Optional


class SaleRecord(TypedDict):
    period: str
    quantity: int
    unit_price: float


class Product(TypedDict):
    id: str
    name: str
    supplier_cost: float  # Preço de Compra
    min_order_qty: int
    operational_cost: float  # Custo Logístico/Armazenagem (R$)
    stock_on_hand: int  # Quanto já tenho no estoque físico

    target_sell_price: float
    manual_sales_estimate: int

    history: List[SaleRecord]


class AppState(TypedDict):
    budget: float
    risk_factor: float
    products: List[Product]
