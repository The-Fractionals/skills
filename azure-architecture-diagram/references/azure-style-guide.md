# Azure Architecture Diagram — Visual Style Guide

Reference specification matching the Microsoft Azure Architecture Center diagrams.
Source: https://learn.microsoft.com/en-us/azure/architecture/browse/

## Colour Palette

### Canvas & Zones
| Element              | Fill      | Border    | Notes                              |
|----------------------|-----------|-----------|------------------------------------|
| Canvas               | `#FFFFFF` | none      | White background, no outer border  |
| General zone         | `#F2F2F2` | `#BFBFBF` | Grey — most grouping boxes        |
| Scope zone           | `#F1FFF4` | `#00B050` | Green — VNets, Fabric, boundaries |
| Data scope zone      | `#F1FFF4` | `#0070C0` | Blue-bordered green fill           |
| Subtle zone          | `#F8F8F8` | `#A5A5A5` | Very light background grouping     |
| Dashed zone          | `#F2F2F2` | `#BFBFBF` | Dashed border — optional groups    |

### Connectors
| Type               | Colour    | Style     | Width | Arrowhead | Usage                    |
|--------------------|-----------|-----------|-------|-----------|--------------------------|
| Primary flow       | `#000000` | Solid     | 1.5px | Filled    | Main request/data path   |
| Data flow          | `#0070C0` | Solid     | 1.5px | Filled    | Data movement, ETL       |
| Bidirectional      | `#000000` | Solid     | 1.5px | Both ends | Two-way communication    |
| Async/event        | `#000000` | Dashed    | 1.5px | Filled    | Async messages, events   |
| Optional/future    | `#000000` | Dashed    | 1.5px | Filled    | Planned connections      |
| Scope arrow        | `#00B050` | Solid     | 1.5px | Filled    | Scope boundary flows     |
| Secondary          | `#A5A5A5` | Solid     | 1.25px| Filled    | Less important links     |

### Step Number Circles
| Element       | Fill      | Text   | Size  | Usage                        |
|---------------|-----------|--------|-------|------------------------------|
| Default       | `#000000` | White  | 22px  | Primary numbered steps       |
| Data step     | `#0070C0` | White  | 22px  | Data flow numbered steps     |
| Scope step    | `#00B050` | White  | 22px  | Green scope flow steps       |

## Typography

| Element          | Size  | Weight | Colour    | Notes                        |
|------------------|-------|--------|-----------|------------------------------|
| Section header   | 18pt  | Bold   | `#000000` | "Ingest", "Process", "Serve" |
| Zone label       | 14pt  | Bold   | `#000000` | Inside zone top-left         |
| Service name     | 11pt  | Normal | `#000000` | Below icon, centred          |
| Detail/subtitle  | 9pt   | Normal | `#737373` | Below service name           |
| Flow annotation  | 10pt  | Bold+Italic | `#000000` | "Hot path", "Cold path" |
| Annotation text  | 9pt   | Italic | `#000000` | Descriptive text near arrows |
| Step number      | 10pt  | Bold   | `#FFFFFF` | White on coloured circle     |
| Platform label   | 12pt  | Bold   | `#000000` | "Platform" section header    |
| Legend text       | 9pt   | Italic | `#000000` | Legend descriptions           |

Font: Segoe UI (Windows/Visio) → DejaVu Sans (Linux fallback).

## Icon Specifications

### Official Azure Icons
- Source: Microsoft Azure Architecture Icon Set (683 SVG files)
- Download URL: `https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V21.zip`
- Format: Multi-coloured SVGs using gradients and the Azure colour palette
- Typical rendered size: 48×48 to 64×64 pixels in diagrams

### Icon Layout Pattern
```
        ┌─────────┐
        │  [icon]  │   48-64px Azure icon
        │         │
        └─────────┘
     Service Name       11pt, centred, black
    (detail text)       9pt, centred, grey — optional
```

### Fallback (when SVG icon unavailable)
Coloured rounded square (48×48) with white 2-3 letter abbreviation:
```
   ┌──────┐
   │  DF  │  White bold text on #0078D4 rounded square
   └──────┘
```

## Layout Patterns

### Pattern 1: Pipeline (Left-to-Right)
The most common pattern in Azure Architecture Center. Used for ETL, data platforms, streaming.

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Ingest  │→│  Store   │→│ Process  │→│  Enrich  │→│  Serve   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

Column headers: Large bold text above each zone. Sources on far left, consumers on far right.
Typical zones: grey. Scope boundary (e.g., Microsoft Fabric): green.

#### Data source column (far left)
Stack data types vertically with abstract icons:
- Big data streams (streaming icon)
- IoT devices (device icon)
- Unstructured (document icon)
- Semistructured (JSON icon)
- Relational databases (database icon)

#### Consumer column (far right)
- Business users (person icon)
- Analytics (chart icon)
- AI applications (robot icon)
- Shared datasets (share icon)

### Pattern 2: Hub-and-Spoke
Central service (API Gateway, Event Hub) with radiating spokes.

### Pattern 3: Layered (Top-to-Bottom)
N-tier: Presentation → Application → Data → Infrastructure.

### Pattern 4: Zone-Based
Multiple independent zones with cross-zone connections. Good for complex multi-domain architectures.

## Platform Bar

A horizontal row at the very bottom of the diagram showing cross-cutting infrastructure services.
Separated from the main architecture by whitespace or a thin line.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Platform   [icon] Entra ID   [icon] Key Vault   [icon] Monitor  ...  │
└────────────────────────────────────────────────────────────────────────┘
```

Common platform services: Entra ID, Cost Management, Key Vault, Monitor, Defender, DevOps, Policy.

## Arrow Routing

1. **Prefer orthogonal** — horizontal and vertical segments with right-angle turns
2. **Short diagonals OK** — when connecting nearby services at slight angles
3. **Step numbers on arrows** — place circled number at midpoint or near source end
4. **Label on arrows** — small italic text near midpoint
5. **Flow direction** — arrowhead at destination; double-headed for bidirectional
6. **Avoid crossing** — route around zones where possible; crossings OK if unavoidable

## Anti-Patterns (Things NOT to Do)

- ❌ Coloured title bar spanning the top (this is NOT Azure Architecture Center style)
- ❌ Outer border around the entire diagram
- ❌ More than 20 services in one diagram
- ❌ Abbreviation squares when official icons are available
- ❌ Using non-Azure brand colours for zone fills
- ❌ Emojis or decorative elements
- ❌ Drop shadows on zones or icons (flat design)
- ❌ Gradient backgrounds
