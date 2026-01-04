# ProfitMax Pro - Sistema de Otimização de Compras e Estoque

Sistema de suporte à decisão que combina Inteligência Artificial (Previsão de Demanda) com Pesquisa Operacional (Alocação de Recursos) para maximizar o lucro líquido de operações de varejo.

## Instalação e Execução

### Pré-requisitos
* Python 3.8 ou superior instalado.

### Passo a Passo
1. Instale as dependências do projeto:
   ```bash
   pip install -r requirements.txt
2. Execute a aplicação via Streamlit:
    python -m streamlit run app.py
3. O sistema abrirá automaticamente no navegador padrão (endereço local, geralmente porta 8501).

Guia de Funcionalidades
1. Gestão de Produtos (Entrada de Dados)
Módulo responsável pelo cadastro de SKUs e parâmetros logísticos.

Campos Financeiros e Logísticos:

Custo Fornecedor: Preço de custo unitário pago ao fornecedor.

Custo Operacional: Custos variáveis por unidade (Ex: embalagem, frete unitário, taxas de cartão, impostos sobre venda). Não inclua custos fixos (aluguel, salários).

Vendas Agendadas (Backlog): Quantidade de produtos que já foram vendidos ou comprometidos com clientes e precisam obrigatoriamente ser adquiridos para entrega. O sistema trata este valor como prioridade absoluta na alocação de verba.

Prazo (Dias): Lead Time (tempo de entrega do fornecedor), utilizado para controle de ruptura de estoque.

Campos de Estratégia Comercial:

Preço Alvo: O preço de venda definido manualmente pelo gestor.

Est. Venda (Manual): Estimativa do gestor sobre o volume de vendas mensal total (incluindo as agendadas). Utilizado como base de cálculo quando não há histórico suficiente para a IA.

Nota: Se a estimativa for 0, não houver vendas agendadas e não houver histórico, o produto será ignorado pelo otimizador.

Upload de Histórico (CSV): Para habilitar o módulo de IA, faça upload de um arquivo .csv individual para cada produto. O arquivo deve conter cabeçalho e seguir este formato:

mes,quantidade,valor
jan,50,100.00
fev,45,110.00
mar,60,95.00

# Painel Estratégico
## Dashboard de Otimização de Compras

Este projeto implementa um sistema de apoio à decisão para definição de preços e planejamento de compras, combinando Machine Learning (preditivo) e Pesquisa Operacional (prescritivo).

O objetivo é maximizar o lucro respeitando restrições reais como orçamento, vendas já contratadas e apetite ao risco.

---

## Funcionalidades Principais

- Sugestão automática de plano ótimo de compras
- Otimização de preço de venda baseada em histórico
- Simulação de cenários de risco (conservador, moderado e agressivo)
- Visualização interativa de demanda e lucro
- Garantia matemática de solução ótima

---

## Painel Estratégico (Dashboard)

Módulo responsável por processar os dados e gerar recomendações de compra com base nos modelos preditivo e prescritivo.

---

## Configurações Globais

### Orçamento
Capital total disponível para o ciclo de compras.

### Nível de Agressividade (Apetite ao Risco)
Define o teto de compra permitido além do volume já garantido pelas vendas agendadas (backlog).

- 0% — Conservador  
  Compra apenas o necessário para cobrir as vendas agendadas.

- 50% — Moderado  
  Estabelece um teto intermediário entre o backlog garantido e a projeção máxima de demanda.

- 100% — Agressivo  
  Permite compras até o limite máximo da estimativa de demanda (IA ou manual).

---

## Interpretação dos Resultados

- Volume  
  Quantidade sugerida para compra de cada SKU.

- Decisão Baseada em  
  Indica se a recomendação foi calculada a partir de:
  - Projeção da IA (histórico)
  - Estimativa manual de demanda

- Ganho Extra  
  Diferença financeira projetada entre utilizar o preço otimizado pela IA e o preço-alvo manual, mantendo o mesmo volume de vendas.

---

## Laboratório de Preço

Simulador que exibe as curvas de demanda e de lucro em função do preço.

### Regras
- Disponível apenas para produtos com no mínimo 3 meses de histórico.
- Permite identificar:
  - Elasticidade-preço da demanda
  - Ponto ótimo de maximização de lucro

---

## Metodologia Técnica

O sistema utiliza uma arquitetura híbrida, combinando:

- Machine Learning (Preditivo) para estimativa de demanda
- Pesquisa Operacional (Prescritivo) para alocação ótima de recursos

---

## Modelo Preditivo — Análise de Demanda

Responsável por estimar o comportamento do consumidor e a elasticidade-preço da demanda.

- Algoritmo: Regressão Linear Simples
- Biblioteca: Scikit-Learn

### Funcionamento

O modelo analisa a correlação histórica entre:

- Preço unitário
- Quantidade vendida

A partir da reta de melhor ajuste:

y = ax + b

o sistema estima a sensibilidade do volume de vendas em relação à variação do preço.

### Maximização de Lucro

- A função de demanda estimada é usada para construir a função de lucro.
- Aplica-se cálculo diferencial (derivada igual a zero) para encontrar o preço que maximiza o lucro, respeitando o custo do produto.

---

## Modelo de Otimização — Alocação de Recursos

Responsável por determinar o plano de compras ideal considerando restrições reais.

- Algoritmo: Programação Linear Inteira Mista (MILP)
- Biblioteca: PuLP (solver CBC)

### Formulação do Problema

Função Objetivo  
Maximizar a soma do Lucro Líquido Previsto de todos os produtos escolhidos.

Variáveis de Decisão  
Quantidade inteira a ser comprada de cada SKU.

Restrições
1. O custo total não pode exceder o orçamento disponível.
2. A compra deve cobrir obrigatoriamente as vendas agendadas (backlog).
3. A compra não pode exceder o teto de demanda ajustado pelo fator de risco.

### Resultado

O solver garante matematicamente a solução global ótima, assegurando a combinação de produtos mais lucrativa possível dentro das restrições impostas.

---

## Tecnologias Utilizadas

- Streamlit — Interface web interativa
- Pandas — Manipulação e estruturação de dados
- PuLP — Modelagem de otimização linear
- Scikit-Learn — Algoritmos de Machine Learning
- Plotly — Visualização de dados e gráficos interativos
