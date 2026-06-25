"""
Premium modern theme system for Streamlit.

Goals:
- Strong visual identity (gradient + subtle glow + glass effects)
- Light/dark palettes via CSS variables
- Backward compatible with existing app CSS class constants:
  SECTION_HEADER_CLASS, SECTION_SUBHEADER_CLASS, CARD_CLASS, CARD_HEADER_CLASS, CARD_BODY_CLASS
- Best-effort styling of common Streamlit widgets and containers
"""

from __future__ import annotations

from typing import Dict, Literal

# ----------------------------
# Backward-compatible constants
# ----------------------------
SECTION_HEADER_CLASS = "section-h"
SECTION_SUBHEADER_CLASS = "section-sub"

CARD_CLASS = "card"
CARD_HEADER_CLASS = "card-header"
CARD_BODY_CLASS = "card-body"

ThemeMode = Literal["light", "dark"]

LIGHT_THEME: Dict[str, str] = {
    "bg0": "#F7FBFF",
    "bg1": "#EEF6FF",
    "panel": "#FFFFFF",
    "panel2": "#F1F5F9",
    "text": "#0B1220",
    "muted": "#475569",
    "muted2": "#64748B",
    "border": "rgba(148, 163, 184, 0.35)",
    "border2": "rgba(148, 163, 184, 0.22)",
    "shadow": "0 18px 60px rgba(2, 6, 23, 0.08)",
    "shadow2": "0 8px 28px rgba(2, 6, 23, 0.06)",
    "brand": "#0ea5e9",
    "brand2": "#3b82f6",
    "brandSoft": "rgba(14,165,233,0.20)",
    "ring": "rgba(59,130,246,0.35)",
    "cardBorder": "rgba(14,165,233,0.18)",
    "danger": "#ef4444",
    "success": "#22c55e",
    "warning": "#f59e0b",
}

DARK_THEME: Dict[str, str] = {
    "bg0": "#070B14",
    "bg1": "#0B1630",
    "panel": "rgba(16, 24, 40, 0.70)",
    "panel2": "rgba(17, 30, 58, 0.65)",
    "text": "#E7EEF8",
    "muted": "#93A3B8",
    "muted2": "#7788A5",
    "border": "rgba(148, 163, 184, 0.22)",
    "border2": "rgba(148, 163, 184, 0.16)",
    "shadow": "0 24px 80px rgba(0, 0, 0, 0.45)",
    "shadow2": "0 14px 40px rgba(0, 0, 0, 0.30)",
    "brand": "#38BDF8",
    "brand2": "#60A5FA",
    "brandSoft": "rgba(56,189,248,0.20)",
    "ring": "rgba(96,165,250,0.35)",
    "cardBorder": "rgba(56,189,248,0.16)",
    "danger": "#fb7185",
    "success": "#34d399",
    "warning": "#fbbf24",
}


def _get_mode(default: ThemeMode = "light") -> ThemeMode:
    try:
        import streamlit as st

        mode = getattr(st.session_state, "theme", None)
        if mode in ("light", "dark"):
            return mode
    except Exception:
        pass
    return default


def inject_css() -> None:
    """Inject premium CSS. Called once per page run from app.py."""
    import streamlit as st

    mode = _get_mode("light")
    t = DARK_THEME if mode == "dark" else LIGHT_THEME

    # Avoid CSS features that may not work everywhere (e.g., color-mix).
    st.markdown(
        f"""
        <style>
          :root {{
            --bg0: {t["bg0"]};
            --bg1: {t["bg1"]};

            --panel: {t["panel"]};
            --panel2: {t["panel2"]};

            --text: {t["text"]};
            --muted: {t["muted"]};
            --muted2: {t["muted2"]};

            --border: {t["border"]};
            --border2: {t["border2"]};

            --shadow: {t["shadow"]};
            --shadow2: {t["shadow2"]};

            --brand: {t["brand"]};
            --brand2: {t["brand2"]};
            --brandSoft: {t["brandSoft"]};

            --ring: {t["ring"]};
            --cardBorder: {t["cardBorder"]};

            --danger: {t["danger"]};
            --success: {t["success"]};
            --warning: {t["warning"]};
          }}

          /* Base canvas */
          html, body {{
            background: radial-gradient(1200px 900px at 10% 0%, rgba(59,130,246,0.18), transparent 55%),
                        radial-gradient(900px 700px at 90% 20%, rgba(14,165,233,0.16), transparent 50%),
                        linear-gradient(180deg, var(--bg0), var(--bg1)) !important;
            color: var(--text) !important;
          }}

          #root {{
            color: var(--text);
          }}

          footer {{
            background: transparent !important;
          }}

          /* Subtle “noise” overlay using gradients (no images) */
          .bb-noise {{
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.05;
            background-image:
              radial-gradient(circle at 20% 30%, rgba(255,255,255,0.35) 0 1px, transparent 2px),
              radial-gradient(circle at 80% 60%, rgba(255,255,255,0.28) 0 1px, transparent 2px);
            background-size: 180px 180px, 220px 220px;
            mix-blend-mode: overlay;
          }}

          /* Typography consistency */
          body {{
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji" !important;
          }}

          /* ---- Existing header primitives ---- */
          .{SECTION_HEADER_CLASS} {{
            font-size: 1.35rem;
            font-weight: 900;
            margin: 12px 0 8px 0;
            letter-spacing: -0.02em;
            color: var(--text);
            position: relative;
          }}
          .{SECTION_HEADER_CLASS}::after {{
            content: "";
            position: absolute;
            left: 0;
            bottom: -8px;
            width: 92px;
            height: 3px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--brand), var(--brand2));
            box-shadow: 0 0 18px rgba(59,130,246,0.25);
          }}

          .{SECTION_SUBHEADER_CLASS} {{
            font-size: 0.98rem;
            font-weight: 750;
            margin: 0 0 12px 0;
            color: var(--muted);
            letter-spacing: -0.01em;
          }}

          /* ---- Card primitives (existing class names) ---- */
          .{CARD_CLASS} {{
            background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.40)) !important;
            border: 1px solid var(--cardBorder) !important;
            border-radius: 18px !important;
            box-shadow: var(--shadow2) !important;
            overflow: hidden;
            transform: translateZ(0);
          }}

          /* Dark mode glass tweak */
          .stApp .{CARD_CLASS} {{
            {"background: linear-gradient(180deg, rgba(16,24,40,0.65), rgba(16,24,40,0.35)) !important;" if mode == "dark" else ""}
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
          }}
          .{CARD_CLASS}:hover {{
            border-color: rgba(59,130,246,0.35) !important;
            box-shadow: var(--shadow) !important;
            transform: translateY(-1px);
          }}

          .{CARD_HEADER_CLASS} {{
            padding: 12px 16px;
            background: linear-gradient(135deg, rgba(14,165,233,0.18), rgba(59,130,246,0.10)) !important;
            background: linear-gradient(135deg, var(--brandSoft), rgba(59,130,246,0.08)) !important;
            border-bottom: 1px solid var(--border) !important;
            font-weight: 900;
            color: var(--text);
          }}

          .{CARD_BODY_CLASS} {{
            padding: 14px 16px;
          }}

          /* Make tabs content breathe */
          section [data-testid="stTabsContent"] {{
            padding-top: 10px;
            padding-bottom: 14px;
          }}

          /* ---- Widget styling (best-effort) ---- */
          /* Inputs */
          input, textarea, select {{
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            background: rgba(255,255,255,0.65);
            color: var(--text) !important;
          }}
          /* Dark mode override for input bg */
          .stApp input, .stApp textarea, .stApp select {{
            {"background: rgba(15,26,46,0.55) !important;" if mode == "dark" else ""}
          }}

          input:focus, textarea:focus, select:focus {{
            outline: none !important;
            box-shadow: 0 0 0 3px var(--ring) !important;
            border-color: rgba(59,130,246,0.65) !important;
          }}

          /* Buttons: primary / secondary patterns */
          button {{
            border-radius: 12px !important;
          }}

          /* Streamlit base button inner */
          div[data-baseweb="button"] {{
            border-radius: 12px !important;
          }}

          /* Hover micro-interaction */
          button:hover {{
            box-shadow: 0 10px 24px rgba(59,130,246,0.18) !important;
          }}

          /* Expander headers */
          details > summary {{
            border-radius: 12px;
            font-weight: 800;
          }}

          /* Sidebar */
          section[data-testid="stSidebar"] {{
            border-right: 1px solid var(--border) !important;
          }}
          section[data-testid="stSidebar"] {{
            background: rgba(255,255,255,0.03) !important;
          }}
          .stApp section[data-testid="stSidebar"] {{
            {"background: rgba(10,16,34,0.45) !important;" if mode == "dark" else ""}
          }}

          section[data-testid="stSidebar"] * {{
            color: var(--text) !important;
          }}

          /* Metric labels/values */
          div[data-testid="stMetricLabel"] {{
            color: var(--muted) !important;
            font-weight: 800 !important;
          }}
          div[data-testid="stMetricValue"] {{
            color: var(--text) !important;
            font-weight: 950 !important;
            letter-spacing: -0.02em;
          }}

          /* HR */
          hr {{
            border-top-color: var(--border) !important;
          }}

          /* Tables in app */
          table {{
            color: var(--text) !important;
          }}

          /* Scrollbar (best-effort) */
          ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
          }}
          ::-webkit-scrollbar-track {{
            background: rgba(148,163,184,0.10);
            border-radius: 999px;
          }}
          ::-webkit-scrollbar-thumb {{
            background: rgba(59,130,246,0.35);
            border-radius: 999px;
            border: 2px solid rgba(0,0,0,0);
            background-clip: padding-box;
          }}
          ::-webkit-scrollbar-thumb:hover {{
            background: rgba(59,130,246,0.55);
            border: 2px solid rgba(0,0,0,0);
            background-clip: padding-box;
          }}

          /* Plotly polish */
          .js-plotly-plot .plotly {{
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji" !important;
          }}
          .js-plotly-plot .xtick text,
          .js-plotly-plot .ytick text {{
            fill: var(--muted) !important;
          }}

          /* Radio / checkbox accent (best-effort) */
          .stRadio label {{
            color: var(--text) !important;
          }}

          /* Reduce layout cramping */
          .stTabs {{
            padding-top: 2px;
          }}
        </style>
        <div class="bb-noise"></div>
        """,
        unsafe_allow_html=True,
    )
