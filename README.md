# Trading 101

Petit projet Python pour consulter un compte Alpaca, ses positions et ses ordres
ouverts.

## Installation sous Windows PowerShell

Depuis la racine du projet, créez puis activez un environnement virtuel :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Installez les dépendances :

```powershell
python -m pip install -r requirements.txt
```

## Configuration des identifiants Alpaca

Lancez l'assistant de configuration :

```powershell
python scripts/setup_credentials.py
```

Il demande la clé API, la clé secrète et le choix entre paper trading et live.
Les valeurs sont enregistrées dans le fichier local `.env`.

## Utilisation

Les commandes suivantes utilisent le dossier source du projet :

```powershell
$env:PYTHONPATH = "src"
```

Testez la connexion et affichez le compte, les positions et les ordres ouverts :

```powershell
python scripts/check_account_state.py
```

Affichez les expositions Greeks des positions options, par contrat puis par
sous-jacent :

```powershell
python scripts/check_option_greeks.py
```

Les expositions delta, gamma, vega et theta correspondent au Greek du contrat
multiplié par la quantité signée et par le multiplicateur standard de 100.

Sauvegardez manuellement l'état courant du compte au format JSON :

```powershell
python scripts/save_account_snapshot.py
```

Chaque fichier est enregistré dans `data/account_snapshots/` avec un horodatage
UTC. Il contient les informations du compte, les positions et les ordres ouverts.
Le dossier `data/` est local et ignoré par Git.

## Execution and Risk Layer

Cette couche sépare volontairement la construction d'un ordre de son envoi :

- `TradableUniverse` définit les ETF et cryptos autorisés.
- `OrderBuilder` crée un `ProposedOrder` normalisé sans appeler Alpaca.
- `RiskChecker` approuve ou rejette la proposition selon des limites prudentes.
- `OrderManager` est le seul composant autorisé à appeler `submit_order`.

Le mode `dry_run` est actif par défaut. Les ventes potentiellement short, les
options et le trading live sont bloqués par défaut.

Téléchargez un an de données quotidiennes pour l'univers courant :

```powershell
$env:PYTHONPATH = "src"
python scripts/download_market_data.py
```

Les fichiers sont enregistrés sous `data/market_data/`, de préférence au format
Parquet avec un repli automatique vers CSV.

Testez un ordre fictif `BUY $10 SPY` sans rien envoyer :

```powershell
$env:PYTHONPATH = "src"
python scripts/place_test_order.py
```

Pour envoyer ce test sur le compte paper uniquement :

```powershell
$env:PYTHONPATH = "src"
python scripts/place_test_order.py --send
```

La saisie exacte de `SEND` est alors obligatoire avant toute soumission.

> **Attention :** n'utilisez pas encore d'identifiants live. Commencez uniquement
> en paper trading et ne validez jamais `.env` dans Git.

## Pre-trade impact preview

Le preview simule un ordre avant tout envoi. Il estime le prix d'exécution avec
le ask pour un achat et le bid pour une vente, puis affiche l'impact sur le cash,
le portefeuille, les expositions et la décision de risque.

```powershell
$env:PYTHONPATH = "src"
python scripts/preview_order_impact.py --symbol SPY --side buy --notional 1000
```

Le rapport exprime les Greeks en termes monétaires : delta, gamma, vega et theta
notionnels. Il affiche aussi les sensibilités PnL pour un mouvement de 1 % du
sous-jacent, un point de volatilité et une journée de theta.

Workflow recommandé :

```powershell
# 1. Prévisualiser uniquement
python scripts/preview_order_impact.py --symbol SPY --side buy --notional 1000

# 2. Vérifier le dry-run
python scripts/place_test_order.py

# 3. Envoyer le petit ordre de test sur le compte paper
python scripts/place_test_order.py --send
```

Les résultats sont des estimations, pas des prix d'exécution garantis. Un ordre
au marché peut être exécuté loin du quote affiché. Les conventions Greeks des
options dépendent du fournisseur de données. Le trading live reste bloqué.

## Live Quote Board

Le Live Quote Board est un écran Streamlit entièrement read-only qui diffuse le
meilleur bid et ask Alpaca. Il n'envoie aucun ordre et peut servir avant le
preview pré-trade ou une décision d'exécution paper.

Installez Streamlit avec les dépendances du projet, ou séparément :

```powershell
python -m pip install streamlit
```

Lancez ensuite le sélecteur interactif :

```powershell
$env:PYTHONPATH = "src"
python scripts/launch_live_quote_board.py
```

Le launcher permet de choisir un groupe de l'univers, tous ses symboles ou une
sélection, puis le flux equity/ETF, overnight, crypto ou options. Streamlit s'ouvre et
actualise le tableau chaque seconde jusqu'à sa fermeture. Le BID est affiché en
jaune et l'ASK en bleu.

Le groupe `Overnight / Asia proxy ETFs (24/5)` ajoute `EWJ`, `FXI`, `EWT` et
`AIA`, avec `SPY` et `QQQ` comme repères liquides. Ce sont des ETF cotés aux
États-Unis, pas les bourses asiatiques elles-mêmes. Ils utilisent le feed Alpaca
`overnight`, disponible pendant la session 20:00–04:00 ET (environ 02:00–10:00
à Paris en été). Sur l'offre gratuite, les quotes overnight sont indicatifs.
Le dashboard charge d'abord un latest quote REST puis écoute le WebSocket.

Pour un flux réellement continu 24/7, le groupe `Crypto` reste le choix le plus
simple.

La disponibilité dépend des permissions et abonnements Alpaca. Les actions,
ETF et options affichent uniquement le top-of-book, pas toute la profondeur.
Les périodes de marché fermé peuvent produire des quotes absents ou périmés.

La reconstruction complète du carnet crypto est prévue pour une version future
(`CryptoOrderBookReconstructor`, top N bid/ask, imbalance, liquidité et analyse
du spread), mais n'est pas implémentée dans cette V1.

## Sécurité

Le fichier `.env` contient des secrets. Il est ignoré par Git et ne doit jamais
être ajouté à un commit, copié dans le code ou partagé.
