#!/usr/bin/env python3
"""
render_azure_diagram.py — Azure Architecture Center style diagram renderer.

Produces high-resolution PNG diagrams matching the visual language of
https://learn.microsoft.com/en-us/azure/architecture/browse/

Uses official Azure SVG icons (converted to PNG) when available,
falling back to coloured abbreviation squares.

Usage:
    from render_azure_diagram import AzureDiagram

    d = AzureDiagram("My Architecture", width=2800, height=1600)
    d.add_zone(...)
    d.add_service(...)
    d.add_connector(...)
    d.render("output.png")
"""

import json
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════
# Colour palette — matches Azure Architecture Center
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # Canvas
    "canvas":       "#FFFFFF",
    # Zone fills
    "zone_grey":    "#F2F2F2",
    "zone_green":   "#F1FFF4",
    "zone_subtle":  "#F8F8F8",
    # Zone borders
    "border_grey":  "#BFBFBF",
    "border_green": "#00B050",
    "border_blue":  "#0070C0",
    "border_subtle":"#A5A5A5",
    # Text
    "text_black":   "#000000",
    "text_grey":    "#737373",
    "text_white":   "#FFFFFF",
    # Connectors
    "arrow_black":  "#000000",
    "arrow_blue":   "#0070C0",
    "arrow_green":  "#00B050",
    "arrow_grey":   "#A5A5A5",
    # Service icon fallback colours (by category)
    "cat_compute":  "#0078D4",
    "cat_data":     "#0078D4",
    "cat_ai":       "#5C2D91",
    "cat_identity": "#008272",
    "cat_security": "#008272",
    "cat_devops":   "#D83B01",
    "cat_monitor":  "#D83B01",
    "cat_network":  "#0078D4",
    "cat_storage":  "#0078D4",
    "cat_analytics":"#F2C811",
    "cat_integration":"#0078D4",
    "cat_iot":      "#0078D4",
    "cat_default":  "#0078D4",
}

# Zone style presets
ZONE_STYLES = {
    "grey":    {"fill": COLORS["zone_grey"],   "border": COLORS["border_grey"],   "dash": False},
    "green":   {"fill": COLORS["zone_green"],  "border": COLORS["border_green"],  "dash": False},
    "blue":    {"fill": COLORS["zone_green"],  "border": COLORS["border_blue"],   "dash": False},
    "subtle":  {"fill": COLORS["zone_subtle"], "border": COLORS["border_subtle"], "dash": False},
    "dashed":  {"fill": COLORS["zone_grey"],   "border": COLORS["border_grey"],   "dash": True},
    "dashed_green": {"fill": COLORS["zone_green"], "border": COLORS["border_green"], "dash": True},
}

# Category → fallback colour for abbreviation squares
CATEGORY_COLORS = {
    "compute": COLORS["cat_compute"], "data": COLORS["cat_data"],
    "ai": COLORS["cat_ai"], "identity": COLORS["cat_identity"],
    "security": COLORS["cat_security"], "devops": COLORS["cat_devops"],
    "monitor": COLORS["cat_monitor"], "network": COLORS["cat_network"],
    "storage": COLORS["cat_storage"], "analytics": COLORS["cat_analytics"],
    "integration": COLORS["cat_integration"], "iot": COLORS["cat_iot"],
    "databases": COLORS["cat_data"], "management": COLORS["cat_devops"],
    "networking": COLORS["cat_network"],
}

# ═══════════════════════════════════════════════════════════════
# Font loading
# ═══════════════════════════════════════════════════════════════

def _load_fonts():
    fonts = {}
    for name, style in [("regular", ""), ("bold", "-Bold"), ("italic", "-Oblique"),
                         ("bolditalic", "-BoldOblique")]:
        for base in [f"/usr/share/fonts/truetype/dejavu/DejaVuSans{style}.ttf",
                      f"/usr/share/fonts/truetype/liberation/LiberationSans{style.replace('Oblique','Italic')}.ttf"]:
            if os.path.exists(base):
                fonts[name] = base
                break
        if name not in fonts:
            fonts[name] = fonts.get("regular", "")
    return fonts

FONT_FILES = _load_fonts()

def get_font(size, style="regular"):
    path = FONT_FILES.get(style, FONT_FILES.get("regular", ""))
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# ═══════════════════════════════════════════════════════════════
# Icon loading
# ═══════════════════════════════════════════════════════════════

_icon_index = None

def _load_icon_index():
    global _icon_index
    idx_file = Path("/home/claude/.azure-icons/index.json")
    if idx_file.exists():
        with open(idx_file) as f:
            _icon_index = json.load(f)
    else:
        _icon_index = {}
    return _icon_index

def get_icon_image(key, size=64):
    """Load an icon PNG. Returns PIL Image or None."""
    global _icon_index
    if _icon_index is None:
        _load_icon_index()
    
    path = _icon_index.get(key)
    if path and os.path.exists(path):
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
            return img
        except:
            pass
    return None

def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════
# AzureDiagram class
# ═══════════════════════════════════════════════════════════════

class AzureDiagram:
    """
    Azure Architecture Center style diagram builder.
    
    Example:
        d = AzureDiagram("Enterprise BI with Fabric", 2800, 1600)
        d.add_zone("fabric", "Microsoft Fabric", 300, 80, 1400, 700, style="green")
        d.add_service("df", "Data Factory", 400, 200, icon="data-factory")
        d.add_connector("df", "lh", step=1)
        d.add_platform_bar(["entra-id", "key-vault", "monitor"])
        d.render("output.png")
    """
    
    def __init__(self, title="", width=2800, height=1600, dpi=150):
        self.title = title
        self.width = width
        self.height = height
        self.dpi = dpi
        self.zones = []
        self.services = {}      # id → service dict
        self.connectors = []
        self.actors = []
        self.annotations = []
        self.section_headers = []
        self.platform_services = []
        self.legend_items = []
    
    # ─── Zone methods ─────────────────────────────────────────
    
    def add_zone(self, id, label, x, y, w, h, style="grey", sublabel=""):
        """Add a grouping zone (rounded rectangle).
        
        style: "grey" | "green" | "blue" | "subtle" | "dashed" | "dashed_green"
        """
        self.zones.append({
            "id": id, "label": label, "sublabel": sublabel,
            "x": x, "y": y, "w": w, "h": h,
            "style": style,
        })
    
    # ─── Service methods ──────────────────────────────────────
    
    def add_service(self, id, label, x, y, icon=None, detail="",
                    category="default", abbrev=None, icon_size=56):
        """Add an Azure service with icon.
        
        icon:     Key from icon catalogue (e.g., "data-factory")
        category: Fallback colour category if icon missing
        abbrev:   2-3 letter abbreviation for fallback icon
        """
        if abbrev is None:
            # Auto-generate abbreviation from label
            words = label.split()
            if len(words) == 1:
                abbrev = label[:3].upper()
            else:
                abbrev = "".join(w[0].upper() for w in words[:3])
        
        self.services[id] = {
            "id": id, "label": label, "detail": detail,
            "x": x, "y": y,
            "icon": icon, "category": category, "abbrev": abbrev,
            "icon_size": icon_size,
        }
    
    # ─── Connector methods ────────────────────────────────────
    
    def add_connector(self, from_id, to_id, style="solid", color="black",
                      label="", step=None, from_side="right", to_side="left"):
        """Add an arrow connector between two services.
        
        style:     "solid" | "dashed"
        color:     "black" | "blue" | "green" | "grey"
        step:      Optional step number (circled digit on arrow)
        from_side: "right" | "left" | "top" | "bottom" | "center"
        to_side:   "right" | "left" | "top" | "bottom" | "center"
        """
        color_map = {
            "black": COLORS["arrow_black"], "blue": COLORS["arrow_blue"],
            "green": COLORS["arrow_green"], "grey": COLORS["arrow_grey"],
        }
        self.connectors.append({
            "from": from_id, "to": to_id,
            "style": style,
            "color": color_map.get(color, color),
            "label": label, "step": step,
            "from_side": from_side, "to_side": to_side,
        })
    
    def add_connector_xy(self, x1, y1, x2, y2, style="solid", color="black",
                         label="", step=None, bidirectional=False):
        """Add an arrow connector between explicit coordinates."""
        color_map = {
            "black": COLORS["arrow_black"], "blue": COLORS["arrow_blue"],
            "green": COLORS["arrow_green"], "grey": COLORS["arrow_grey"],
        }
        self.connectors.append({
            "from": None, "to": None,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "style": style,
            "color": color_map.get(color, color),
            "label": label, "step": step,
            "bidirectional": bidirectional,
        })
    
    # ─── Annotation methods ───────────────────────────────────
    
    def add_section_header(self, text, x, y):
        """Add a large section header (e.g., "Ingest", "Process", "Serve")."""
        self.section_headers.append({"text": text, "x": x, "y": y})
    
    def add_annotation(self, text, x, y, style="italic", color="black"):
        """Add a text annotation at a specific position."""
        self.annotations.append({
            "text": text, "x": x, "y": y,
            "style": style, "color": color,
        })
    
    def add_actor(self, label, x, y, detail="", icon_type="user"):
        """Add a user/system actor at diagram edge.
        icon_type: "user" | "system" | "database" | "device"
        """
        self.actors.append({
            "label": label, "detail": detail,
            "x": x, "y": y, "icon_type": icon_type,
        })
    
    def add_legend(self, items):
        """Add legend items. Each item: {"style": "solid|dashed", "color": "...", "label": "..."}"""
        self.legend_items = items
    
    # ─── Platform bar ─────────────────────────────────────────
    
    def add_platform_bar(self, service_keys, y=None, label="Platform"):
        """Add a platform services bar at the bottom of the diagram.
        
        service_keys: list of icon keys (e.g., ["entra-id", "key-vault", "monitor"])
        """
        self.platform_services = service_keys
        self._platform_y = y
        self._platform_label = label
    
    # ─── Rendering ────────────────────────────────────────────
    
    def render(self, output_path, show_grid=False):
        """Render the diagram to a PNG file."""
        img = Image.new("RGBA", (self.width, self.height), hex_to_rgb(COLORS["canvas"]) + (255,))
        d = ImageDraw.Draw(img)
        
        # 1. Draw zones (back to front)
        for zone in self.zones:
            self._draw_zone(d, zone)
        
        # 2. Draw section headers
        for hdr in self.section_headers:
            f = get_font(22, "bold")
            d.text((hdr["x"], hdr["y"]), hdr["text"], font=f, fill=COLORS["text_black"])
        
        # 3. Draw connectors (before services so arrows go behind icons)
        for conn in self.connectors:
            self._draw_connector(d, img, conn)
        
        # 4. Draw services
        for svc in self.services.values():
            self._draw_service(d, img, svc)
        
        # 5. Draw actors
        for actor in self.actors:
            self._draw_actor(d, actor)
        
        # 6. Draw annotations
        for ann in self.annotations:
            style_name = "italic" if ann["style"] == "italic" else \
                         "bolditalic" if ann["style"] == "bolditalic" else \
                         "bold" if ann["style"] == "bold" else "regular"
            f = get_font(12, style_name)
            fill = COLORS["text_black"] if ann["color"] == "black" else ann["color"]
            d.text((ann["x"], ann["y"]), ann["text"], font=f, fill=fill)
        
        # 7. Draw platform bar
        if self.platform_services:
            self._draw_platform_bar(d, img)
        
        # 8. Draw legend
        if self.legend_items:
            self._draw_legend(d)
        
        # 9. Title (top-left, if set)
        if self.title:
            f = get_font(11, "italic")
            # Small italic title at very bottom or top — match Azure style
            # (Azure diagrams often have no title on the diagram itself)
        
        # Convert to RGB and save
        rgb = Image.new("RGB", img.size, (255, 255, 255))
        rgb.paste(img, mask=img.split()[3])
        rgb.save(output_path, "PNG", dpi=(self.dpi, self.dpi))
        print(f"Rendered: {output_path} ({self.width}×{self.height})")
        return output_path
    
    # ─── Internal drawing methods ─────────────────────────────
    
    def _draw_zone(self, d, zone):
        """Draw a zone grouping rectangle."""
        s = ZONE_STYLES.get(zone["style"], ZONE_STYLES["grey"])
        x, y, w, h = zone["x"], zone["y"], zone["w"], zone["h"]
        fill = hex_to_rgb(s["fill"])
        border = hex_to_rgb(s["border"])
        
        if s["dash"]:
            # Dashed border
            d.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=fill)
            self._draw_dashed_rect(d, x, y, x+w, y+h, border, dash=10, gap=6, width=1)
        else:
            d.rounded_rectangle([x, y, x+w, y+h], radius=10, fill=fill, outline=border, width=1)
        
        # Zone label
        if zone["label"]:
            f = get_font(16, "bold")
            d.text((x + 12, y + 8), zone["label"], font=f, fill=COLORS["text_black"])
        if zone.get("sublabel"):
            f = get_font(11, "italic")
            lbl_w = d.textbbox((0, 0), zone["label"], font=get_font(16, "bold"))[2]
            d.text((x + 18 + lbl_w, y + 12), zone["sublabel"],
                   font=f, fill=COLORS["text_grey"])
    
    def _draw_service(self, d, img, svc):
        """Draw a service icon with label."""
        x, y = svc["x"], svc["y"]
        sz = svc["icon_size"]
        
        # Try official icon first
        icon_img = get_icon_image(svc["icon"], sz) if svc["icon"] else None
        
        if icon_img:
            # Paste official icon (centred at x, y)
            ix, iy = x - sz // 2, y - sz // 2
            img.paste(icon_img, (ix, iy), icon_img)
        else:
            # Fallback: coloured rounded square with abbreviation
            cat_color = CATEGORY_COLORS.get(svc["category"], COLORS["cat_default"])
            half = sz // 2
            d.rounded_rectangle(
                [x - half, y - half, x + half, y + half],
                radius=8, fill=hex_to_rgb(cat_color)
            )
            f = get_font(18 if len(svc["abbrev"]) <= 3 else 14, "bold")
            bbox = d.textbbox((0, 0), svc["abbrev"], font=f)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text((x - tw/2, y - th/2), svc["abbrev"],
                   font=f, fill=COLORS["text_white"])
        
        # Service name below icon
        f_name = get_font(13, "regular")
        name_bbox = d.textbbox((0, 0), svc["label"], font=f_name)
        name_w = name_bbox[2] - name_bbox[0]
        d.text((x - name_w/2, y + sz//2 + 4), svc["label"],
               font=f_name, fill=COLORS["text_black"])
        
        # Detail text below name
        if svc["detail"]:
            f_det = get_font(10, "italic")
            det_bbox = d.textbbox((0, 0), svc["detail"], font=f_det)
            det_w = det_bbox[2] - det_bbox[0]
            d.text((x - det_w/2, y + sz//2 + 20), svc["detail"],
                   font=f_det, fill=COLORS["text_grey"])
    
    def _get_service_anchor(self, svc_id, side):
        """Get connection point for a service."""
        svc = self.services.get(svc_id)
        if not svc:
            return (0, 0)
        x, y = svc["x"], svc["y"]
        sz = svc["icon_size"]
        half = sz // 2
        offsets = {
            "right":  (x + half + 4, y),
            "left":   (x - half - 4, y),
            "top":    (x, y - half - 4),
            "bottom": (x, y + half + 4),
            "center": (x, y),
        }
        return offsets.get(side, (x, y))
    
    def _draw_connector(self, d, img, conn):
        """Draw an arrow connector."""
        # Resolve endpoints
        if conn["from"] and conn["to"]:
            x1, y1 = self._get_service_anchor(conn["from"], conn.get("from_side", "right"))
            x2, y2 = self._get_service_anchor(conn["to"], conn.get("to_side", "left"))
        else:
            x1, y1 = conn.get("x1", 0), conn.get("y1", 0)
            x2, y2 = conn.get("x2", 0), conn.get("y2", 0)
        
        color = hex_to_rgb(conn["color"])
        width = 2
        
        # Draw line
        if conn["style"] == "dashed":
            self._draw_dashed_line(d, x1, y1, x2, y2, color, dash=8, gap=6, width=width)
        else:
            d.line([(x1, y1), (x2, y2)], fill=color, width=width)
        
        # Arrowhead at destination
        self._draw_arrowhead(d, x1, y1, x2, y2, color, size=10)
        
        # Bidirectional arrowhead
        if conn.get("bidirectional"):
            self._draw_arrowhead(d, x2, y2, x1, y1, color, size=10)
        
        # Step number
        if conn.get("step") is not None:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self._draw_step_circle(d, mx, my, conn["step"], conn["color"])
        
        # Label
        if conn.get("label"):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            f = get_font(10, "italic")
            d.text((mx + 6, my - 16), conn["label"], font=f, fill=COLORS["text_black"])
    
    def _draw_arrowhead(self, d, x1, y1, x2, y2, color, size=10):
        """Draw a filled triangle arrowhead at (x2, y2)."""
        angle = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2, y2)
        p2 = (x2 - size * math.cos(angle - 0.35), y2 - size * math.sin(angle - 0.35))
        p3 = (x2 - size * math.cos(angle + 0.35), y2 - size * math.sin(angle + 0.35))
        d.polygon([p1, p2, p3], fill=color)
    
    def _draw_step_circle(self, d, cx, cy, number, color):
        """Draw a circled step number."""
        r = 12
        fill = hex_to_rgb(color) if isinstance(color, str) and color.startswith("#") else \
               hex_to_rgb(COLORS["arrow_black"])
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
        f = get_font(12, "bold")
        text = str(number)
        bbox = d.textbbox((0, 0), text, font=f)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((cx - tw/2, cy - th/2 - 1), text, font=f, fill=COLORS["text_white"])
    
    def _draw_actor(self, d, actor):
        """Draw a user/system actor."""
        x, y = actor["x"], actor["y"]
        
        if actor["icon_type"] == "user":
            # Simple person icon
            d.ellipse([x-8, y-22, x+8, y-6], outline=COLORS["text_black"], width=2)
            d.arc([x-16, y-4, x+16, y+16], 0, 180, fill=COLORS["text_black"], width=2)
        elif actor["icon_type"] == "database":
            # Simple database icon
            d.ellipse([x-14, y-18, x+14, y-8], outline=COLORS["text_black"], width=2)
            d.line([(x-14, y-13), (x-14, y+10)], fill=COLORS["text_black"], width=2)
            d.line([(x+14, y-13), (x+14, y+10)], fill=COLORS["text_black"], width=2)
            d.arc([x-14, y, x+14, y+20], 0, 180, fill=COLORS["text_black"], width=2)
        
        f = get_font(13, "bold")
        bbox = d.textbbox((0, 0), actor["label"], font=f)
        tw = bbox[2] - bbox[0]
        d.text((x - tw/2, y + 22), actor["label"], font=f, fill=COLORS["text_black"])
        
        if actor["detail"]:
            f2 = get_font(10, "regular")
            bbox2 = d.textbbox((0, 0), actor["detail"], font=f2)
            tw2 = bbox2[2] - bbox2[0]
            d.text((x - tw2/2, y + 38), actor["detail"], font=f2, fill=COLORS["text_grey"])
    
    def _draw_platform_bar(self, d, img):
        """Draw the platform services bar at the bottom."""
        bar_y = self._platform_y or (self.height - 100)
        bar_h = 80
        x_start = 40
        
        # Light background
        d.rounded_rectangle(
            [x_start, bar_y, self.width - 40, bar_y + bar_h],
            radius=8, fill=hex_to_rgb(COLORS["zone_grey"]),
            outline=hex_to_rgb(COLORS["border_grey"]), width=1
        )
        
        # "Platform" label
        f_lbl = get_font(14, "bold")
        d.text((x_start + 16, bar_y + bar_h//2 - 10), self._platform_label,
               font=f_lbl, fill=COLORS["text_black"])
        
        # Services spread evenly
        n = len(self.platform_services)
        if n == 0:
            return
        label_start = x_start + 120
        spacing = (self.width - 80 - label_start) // max(n, 1)
        
        for i, key in enumerate(self.platform_services):
            sx = label_start + i * spacing + spacing // 2
            sy = bar_y + bar_h // 2
            
            # Try icon
            icon_img = get_icon_image(key, 36)
            if icon_img:
                img.paste(icon_img, (sx - 18, sy - 22), icon_img)
            else:
                # Small fallback square
                d.rounded_rectangle([sx-14, sy-22, sx+14, sy-0],
                                    radius=4, fill=hex_to_rgb(COLORS["cat_default"]))
            
            # Label below
            # Derive friendly name from key
            name = key.replace("-", " ").title()
            name_map = {
                "entra-id": "Microsoft\nEntra ID", "key-vault": "Azure Key\nVault",
                "monitor": "Azure\nMonitor", "defender": "Microsoft Defender\nfor Cloud",
                "devops": "Azure DevOps\nand GitHub", "policy": "Azure\nPolicy",
                "cost-management": "Cost\nManagement", "app-insights": "Application\nInsights",
            }
            display = name_map.get(key, name)
            f_svc = get_font(10, "regular")
            for j, line in enumerate(display.split("\n")):
                bbox = d.textbbox((0, 0), line, font=f_svc)
                tw = bbox[2] - bbox[0]
                d.text((sx - tw/2, sy + 16 + j * 13), line,
                       font=f_svc, fill=COLORS["text_black"])
    
    def _draw_legend(self, d):
        """Draw legend in bottom-left corner."""
        lx, ly = 50, self.height - 140
        f = get_font(10, "italic")
        
        for i, item in enumerate(self.legend_items):
            iy = ly + i * 20
            color = hex_to_rgb(item.get("color", COLORS["arrow_black"]))
            if item.get("style") == "dashed":
                self._draw_dashed_line(d, lx, iy + 6, lx + 30, iy + 6, color, width=2)
            else:
                d.line([(lx, iy + 6), (lx + 30, iy + 6)], fill=color, width=2)
            self._draw_arrowhead(d, lx, iy + 6, lx + 30, iy + 6, color, size=7)
            d.text((lx + 36, iy), item["label"], font=f, fill=COLORS["text_black"])
    
    def _draw_dashed_line(self, d, x1, y1, x2, y2, color, dash=8, gap=6, width=2):
        """Draw a dashed line."""
        length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if length == 0:
            return
        dx, dy = (x2-x1)/length, (y2-y1)/length
        pos = 0
        while pos < length:
            end = min(pos + dash, length)
            sx, sy = x1 + dx*pos, y1 + dy*pos
            ex, ey = x1 + dx*end, y1 + dy*end
            d.line([(sx, sy), (ex, ey)], fill=color, width=width)
            pos += dash + gap
    
    def _draw_dashed_rect(self, d, x1, y1, x2, y2, color, dash=10, gap=6, width=1):
        """Draw a dashed rectangle."""
        for sx, sy, ex, ey in [(x1,y1,x2,y1), (x2,y1,x2,y2),
                                (x2,y2,x1,y2), (x1,y2,x1,y1)]:
            self._draw_dashed_line(d, sx, sy, ex, ey, color, dash, gap, width)
