# First Proposal – Algorithmic Trading

## Goals

1. Improving programming skills: Generate the skeleton of a code that can automatically perform:
   - a) data collection,
   - b) execution of orders,
   - c) Continuous Deployment & Integration (cf. GitHub Actions).

2. Initiate to proper algorithmic trading: Create a simple and highly understandable algorithm on financial assets that are not too technical (no exotic assets, no commodities related to geopolitics, …) in order to generate steady low returns with low risks.

## APIs propositions

As there are no capital gains tax in Singapore, the APIs / broker platform used to pass orders must be compatible with Singapore’s regulations.

| API | + | - | Deposit |
|------|---|---|---------|
| **Alpaca Trading (2015)** | Real time, great community activity, 0 fees on US stocks, better investor protection | Shorter historical data (less than 10 years), API rate limit = 200 (but 10k with Algo Trader Plus) | Bank transfer, Airwallex, Checkout, Currency Cloud, I2C, Nium, Sila Money, Wise |
| **Oanda (1996)** | Real time, prices since 2005, API rate limit = 7200, 0 fees on US stocks | Mid-range community activity, fees can be slightly more expensive, inactivity fee | Bank transfer, Credit/debit cards, PayPal, Skrill, Neteller |
| **Interactive Broker (1977)** | API rate limit = 3000, great community activity, regulated by MAS (Singapore) | Trading fees for US stock = 1US$, a bit more fees generally | Bank transfer |

**Source:** https://brokerchooser.com/best-brokers/best-brokers-for-algo-trading-in-singapore

## Asset classes to be considered (open question)

- Maybe stocks first.

## First algorithms to be considered (very open question)

- Simple maths
- Why not trying including possibility theory for a better accounting of ignorance (cf. Léo & Gabriel)?

## Future extensions

- More complex algorithms: Reinforcement Learning, LLMs automation (Grok), …
- Multidimensional selection of assets.
- More complex products…

## Roles to be filled

(One role can be done by multiple people.)

- Strategist
- Continuous Development & Integration
- Architect: how to test algorithms before launching them, emergency stop, …

# Rules

Rules can be amended later if needed.

1. No obligation / participation quotas.
2. Everyone agrees here to share his algorithm, no secret.
3. Gains or losses distributions will always follow the proportions of money invested. For example, if my money represents 20% of whole the money invested, I should get 20% of the gains/losses. This follows from Rule n°2, everything is shared.
4. Every 1st of the month, people can ask to withdraw their own share of money but this must be accepted by at least a majority of the members as this can impact trading strategies.
5. Exceptions to Rule n°4 include exceptional expenses encountered by any member (health, housing…).


# Example of project structure

```text
algorithmic-trading/
│
├── documentations/                         
│   ├── architecture.md
│   ├── api.md
│   ├── algorithms.md
│   └── deployment.md
│                 
├── src/
│   ├── config/
│   ├── data/
│   ├── strategies/
│   ├── backtesting/
│   ├── execution/
│   └── main.py
│
├── tests/
│   ├── test_data.py
│   ├── test_strategy.py
│   ├── test_backtesting.py
│   └── test_execution.py
│
└── .github/
    └── workflows/ # for CD / CI
```

