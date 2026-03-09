---
name: azure-architecture-diagram
description: >
  Generate professional Azure architecture diagrams matching the Microsoft Azure Architecture Center
  style (learn.microsoft.com/en-us/azure/architecture/browse/). Use this skill whenever the user asks
  for an Azure architecture diagram, cloud infrastructure diagram, physical architecture diagram with
  Azure services, or any visual showing Azure services and data flows. Also trigger when the user says
  "draw an architecture diagram", "make it look like Azure Architecture Center", "create a diagram with
  Azure icons", or references Azure reference architectures. Even for non-Azure diagrams where the user
  wants a professional cloud architecture visual, this skill produces high-quality results. Always use
  this skill instead of hand-drawing Pillow diagrams for Azure architectures — it handles icons,
  zones, arrows, step numbers, and the full Azure visual language automatically.
---

# Azure Architecture Diagram Skill

Generates PNG architecture diagrams that match the visual style published in the
Microsoft Azure Architecture Center.

## Before Starting — READ THESE FILES

1. Read `references/azure-style-guide.md` — full visual spec, colour palette, layout rules
2. Run `scripts/setup_icons.py` — downloads and caches official Azure SVG icons as PNGs (one-time)
3. Use `scripts/render_azure_diagram.py` — the rendering API

## Quick Start

```python
# 1. Setup icons (once per session)
exec(open("/path/to/scripts/setup_icons.py").read())

# 2. Define diagram
from render_azure_diagram import AzureDiagram

d = AzureDiagram("My Architecture", width=2800, height=1600)

# Add zones (grouping boxes)
d.add_zone("fabric", "Microsoft Fabric", x=350, y=80, w=1400, h=700,
           style="green")  # green = scope boundary

# Add services (with official icons)
d.add_service("df", "Data Factory", x=400, y=200, icon="data-factory")
d.add_service("lh", "Lakehouse", x=700, y=200, icon="synapse")

# Add connectors
d.add_connector("df", "lh", label="ELT", step=1)

# Add platform bar
d.add_platform_bar(["entra-id", "key-vault", "monitor", "defender", "devops"])

# Render
d.render("/mnt/user-data/outputs/architecture.png")
```

## Workflow

### Step 1: Understand the architecture
Parse the user's request. Identify: services, data flows, zone groupings, user types.

### Step 2: Choose a layout pattern
See `references/azure-style-guide.md` § Layout Patterns:
- **Pipeline** (left→right): Ingest → Store → Process → Enrich → Serve
- **Hub-and-spoke**: Central service with radiating connections
- **Layered** (top→bottom): Presentation → Application → Data
- **Zone-based**: Independent functional groups with cross-connections

### Step 3: Write the rendering code
Use `render_azure_diagram.py` API. Position services in a grid aligned to zones.
Use `add_connector()` with step numbers for ordered data flows.

### Step 4: Render, review, adjust
Generate the PNG. Check for overlapping labels, arrow routing issues, and zone sizing.
Adjust coordinates and re-render. Deliver to user.

## Key Design Rules (from Azure Architecture Center)

1. **Official Azure icons** — use `icon="service-name"` from the icon catalogue
2. **Left-to-right primary flow** — data reads left → right or top → bottom
3. **Zone grouping** — related services in rounded rectangles with light fills
4. **Step numbers** — circled numbers on arrows to show operation sequence
5. **Two zone styles** — grey (#F2F2F2) for general groups, green (#F1FFF4) for scope boundaries
6. **Platform bar at bottom** — cross-cutting services (identity, security, monitoring)
7. **Max 15-20 services per diagram** — split complex architectures into multiple diagrams
8. **Segoe UI / DejaVu Sans** — clean sans-serif typography
9. **White canvas** — no outer border, no coloured title bars
10. **Flow annotations** — italic text like "Hot path" / "Cold path" near arrows

## Icon Catalogue

The setup script downloads 683 official Azure SVG icons from Microsoft's CDN. Common icon keys:

| Key                  | Azure Service               | Category           |
|----------------------|-----------------------------|--------------------|
| `data-factory`       | Azure Data Factory          | Analytics          |
| `sql-database`       | Azure SQL Database          | Databases          |
| `cosmos-db`          | Azure Cosmos DB             | Databases          |
| `storage-account`    | Azure Storage Accounts      | Storage            |
| `event-hubs`         | Azure Event Hubs            | Analytics/IoT      |
| `iot-hub`            | Azure IoT Hub               | IoT                |
| `app-service`        | Azure App Service           | Compute/Web        |
| `kubernetes`         | Azure Kubernetes Service    | Containers         |
| `function-app`       | Azure Functions             | Compute            |
| `api-management`     | API Management              | Integration        |
| `key-vault`          | Azure Key Vault             | Security           |
| `monitor`            | Azure Monitor               | Management         |
| `app-insights`       | Application Insights        | DevOps/Monitor     |
| `entra-id`           | Microsoft Entra ID          | Identity           |
| `b2c`                | Azure AD B2C                | Identity           |
| `cognitive-search`   | Azure AI Search             | AI + ML            |
| `openai`             | Azure OpenAI                | AI + ML            |
| `machine-learning`   | Azure Machine Learning      | AI + ML            |
| `speech`             | Azure AI Speech             | AI + ML            |
| `language`           | Azure AI Language           | AI + ML            |
| `cognitive-services` | Azure AI Services           | AI + ML            |
| `power-bi`           | Power BI Embedded           | Analytics          |
| `synapse`            | Azure Synapse Analytics     | Analytics          |
| `databricks`         | Azure Databricks            | Analytics          |
| `stream-analytics`   | Stream Analytics            | Analytics          |
| `service-bus`        | Azure Service Bus           | Integration        |
| `cdn`                | Azure CDN                   | Networking         |
| `redis`              | Azure Cache for Redis       | Databases          |
| `purview`            | Microsoft Purview           | Databases          |
| `defender`           | Microsoft Defender for Cloud| Security           |
| `devops`             | Azure DevOps                | DevOps             |
| `policy`             | Azure Policy                | Management         |
| `cost-management`    | Cost Management             | Management         |
| `data-lake`          | Data Lake Storage           | Storage            |

If an icon isn't in the cache, the engine falls back to a coloured rounded square with
a 2-3 letter abbreviation — still looks clean and professional.

## File Structure
```
azure-architecture-diagram/
├── SKILL.md                           ← You are here
├── references/
│   └── azure-style-guide.md           ← Visual spec, colours, layout patterns
└── scripts/
    ├── setup_icons.py                 ← Downloads & caches official Azure icons
    └── render_azure_diagram.py        ← Rendering engine (Pillow-based)
```
