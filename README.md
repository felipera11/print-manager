# Print Manager 3D

Sistema web para gestão de um serviço de impressão 3D. Permite cadastrar impressoras e spools de filamento, registrar ordens de impressão com controle automático de estoque e fila, e gerar orçamentos em PDF — tudo com cálculo de custo de produção automático.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | Flask + Jinja2 (Python) |
| Banco de dados | PostgreSQL |
| Testes | Pytest |
| Orquestração | Docker Compose |
| CI | GitHub Actions |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Executando o projeto

```bash
git clone https://github.com/felipera11/print-manager.git
cd print-manager
docker-compose up --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:5000 |
| Backend (API) | http://localhost:8000 |
| Documentação Swagger | http://localhost:8000/docs |

```bash
docker-compose down          # encerrar
docker-compose down -v       # encerrar e apagar banco
```

## Executando os testes

```bash
docker-compose run backend pytest
```

Os testes cobrem todos os recursos do backend (printers, filament types, spool models, spools, clients, prints, quotes e dashboard) usando um banco em memória isolado via `TestClient` do FastAPI. Os mesmos testes rodam automaticamente no GitHub Actions a cada push.

## Banco de dados

`spool_models` representa o modelo físico do rolo (peso vazio). `spools` são as unidades reais de filamento em estoque, referenciando um modelo e um tipo de filamento.

### Relações

- **N:M** — `prints` ↔ `spools` (via `print_spools`): uma impressão pode usar várias spools, e uma spool pode participar de várias impressões
- **N:1** — `spools` → `filament_types`, `spools` → `spool_models`, `prints` → `printers`, `prints` → `clients`, `quotes` → `clients` (destinatário e emitente), `quote_items` → `quotes`, `quote_items` → `printers`, `quote_items` → `filament_types`

### Esquema

```
printers       (id, name, brand, hourly_cost, active)
filament_types (id, type, brand, cost_per_kg)
spool_models   (id, name, weight_g)
spools         (id, number, type_id→filament_types, color, spool_model_id→spool_models,
                total_weight_g, remaining_weight_g, reserved_weight_g)
clients        (id, name, email, cnpj, address, mobile, phone)
prints         (id, part_name, printer_id→printers, client_id→clients,
                weight_g, time_h, cost, price, date, notes, status, queue_position)
print_spools   (print_id→prints, spool_id→spools)     -- tabela N:M
quotes         (id, client_id→clients, issuer_client_id→clients, discount, total, date, status)
quote_items    (id, quote_id→quotes, part_name, quantity, weight_g, time_h, margin,
                printer_id→printers, filament_type_id→filament_types, unit_price, total)
```

## Telas do frontend

| Tela | URL | Descrição |
|---|---|---|
| Dashboard | `/` | Métricas do mês: gasto de produção, receita, impressões e spools com estoque crítico |
| Calculadora | `/calculator` | Estimativa de custo por filamento e tempo sem criar uma ordem |
| Impressoras | `/printers` | CRUD de impressoras |
| Filamentos | `/filaments` | CRUD de tipos de filamento, modelos de spool e spools |
| Clientes | `/clients` | CRUD de clientes |
| Impressões | `/prints` | CRUD de ordens de impressão com filtros por status, cliente e impressora |
| Fila | `/queue` | Visualização e reordenação drag-and-drop da fila de impressão |
| Orçamentos | `/quotes` | CRUD de orçamentos com itens e exportação em PDF |

## API

Todos os endpoints seguem o padrão `/api/v1/{recurso}/`. A documentação completa com schemas e exemplos está disponível no Swagger em `/docs`.

### Printers — `/api/v1/printers/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar impressoras |
| GET | `/{id}` | Buscar impressora |
| POST | `/` | Criar impressora |
| PUT | `/{id}` | Editar impressora |
| DELETE | `/{id}` | Remover impressora |

### Filament Types — `/api/v1/filament-types/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar tipos de filamento |
| GET | `/{id}` | Buscar tipo |
| POST | `/` | Criar tipo |
| PUT | `/{id}` | Editar tipo |
| DELETE | `/{id}` | Remover tipo |

### Spool Models — `/api/v1/spool-models/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar modelos de spool |
| GET | `/{id}` | Buscar modelo |
| POST | `/` | Criar modelo |
| PUT | `/{id}` | Editar modelo |
| DELETE | `/{id}` | Remover modelo |

### Spools — `/api/v1/spools/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar spools |
| GET | `/suggest?weight_g=X&type_id=Y` | Sugerir spools com filamento disponível suficiente para o peso pedido |
| GET | `/{id}` | Buscar spool |
| POST | `/` | Criar spool |
| PUT | `/{id}` | Editar spool |
| DELETE | `/{id}` | Remover spool |

### Clients — `/api/v1/clients/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar clientes |
| GET | `/{id}` | Buscar cliente |
| POST | `/` | Criar cliente |
| PUT | `/{id}` | Editar cliente |
| DELETE | `/{id}` | Remover cliente |

### Prints — `/api/v1/prints/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar impressões (filtros: `client_id`, `printer_id`, `status`) |
| GET | `/{id}` | Buscar impressão |
| POST | `/` | Criar impressão |
| PUT | `/{id}` | Editar impressão |
| PATCH | `/reorder` | Reordenar fila — body: `{"print_ids": [...]}` |
| PATCH | `/{id}/status` | Atualizar status — body: `{"status": "queued"\|"printing"\|"completed"\|"failed"}` |
| DELETE | `/{id}` | Remover impressão |

### Quotes — `/api/v1/quotes/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Listar orçamentos |
| GET | `/{id}` | Buscar orçamento |
| GET | `/{id}/pdf` | Gerar PDF do orçamento |
| POST | `/` | Criar orçamento com itens |
| PUT | `/{id}` | Editar orçamento |
| DELETE | `/{id}` | Remover orçamento |

### Dashboard — `/api/v1/dashboard/`

| Método | Rota | Ação |
|---|---|---|
| GET | `/` | Resumo do mês atual (gasto de produção, receita, contagem de impressões, spools com estoque crítico) |

## Regras de negócio

### Custo de impressão

O custo de produção é calculado automaticamente ao criar ou editar uma impressão. O peso é distribuído igualmente entre as spools selecionadas:

```
filament_cost  = Σ (weight_g / n_spools / 1000) × cost_per_kg    (por spool, somado)
printing_cost  = time_h × hourly_cost
cost           = filament_cost + printing_cost
```

O campo `price` (valor cobrado do cliente) é inserido manualmente e independe do custo.

### Fluxo de status e estoque

Uma impressão passa pelo seguinte ciclo de vida, e cada transição afeta o estoque das spools:

```
queued → printing → completed
                 ↘ failed
```

| Status | Efeito no estoque |
|---|---|
| `queued` | Reserva `weight_g` em `reserved_weight_g` das spools |
| `printing` | Mantém a reserva; apenas uma impressão `printing` por impressora simultaneamente |
| `completed` | Desconta o peso de `total_weight_g` e `remaining_weight_g`, libera reserva |
| `failed` | Libera a reserva sem descontar peso |

### Precificação de orçamentos

```
unit_price  = (filament_cost + printing_cost) × (1 + margin / 100)
item_total  = unit_price × quantity
quote_total = Σ item_total × (1 - discount / 100)
```

## Logs

Cada serviço emite uma linha de log por requisição no stdout:

```bash
docker-compose logs backend     # logs do backend
docker-compose logs frontend    # logs do frontend
docker-compose logs -f          # todos os serviços em tempo real
```
