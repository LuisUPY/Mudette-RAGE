#!/usr/bin/env python3
"""Generate a visual PDF glossary of Mudette commands and scripts."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "Mudette-Command-Glossary.pdf"


def _register_fonts(pdf: FPDF) -> str:
    """Return family name for body text (Unicode-capable if available)."""
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            pdf.add_font("Mudette", "", path)
            pdf.add_font("Mudette", "B", path)
            pdf.add_font("Mudette", "I", path)
            return "Mudette"
    return "Helvetica"

# (category, color_rgb, commands)
CATALOG: list[tuple[str, tuple[int, int, int], list[dict[str, str]]]] = [
    (
        "1. Primeros pasos",
        (41, 98, 255),
        [
            {
                "title": "setup.sh",
                "subtitle": "Instalar dependencias",
                "run": "./scripts/setup.sh",
                "desc": "Descarga e instala Python, librerías (Gradio, FAISS, OpenAI) y herramientas de desarrollo con uv.",
                "keys": "No requiere API keys",
                "when": "Primera vez que clonas el repo o tras cambiar pyproject.toml",
            },
            {
                "title": "build-kb.sh",
                "subtitle": "Construir base de conocimiento",
                "run": "./scripts/build-kb.sh",
                "desc": "Regenera el índice FAISS y chunks.json desde los markdown en demo_pack/nexa_copilot/kb_src/.",
                "keys": "No requiere API keys",
                "when": "Tras editar documentación IT en kb_src/",
            },
        ],
    ),
    (
        "2. Ejecutar la demo",
        (16, 185, 129),
        [
            {
                "title": "run-demo.sh",
                "subtitle": "Abrir la demo web",
                "run": "./scripts/run-demo.sh",
                "alt": "uv run Mudette-demo",
                "desc": "Inicia Gradio en http://localhost:7860. Chat con Nexa Copilot, panel TurnTrace, playbooks y capas L1→L2→Fusion.",
                "keys": "Opcional: API key agente (gpt-4o) + API key juez (gpt-4o-mini), separadas",
                "when": "Probar la demo interactiva con modo benigno o red team",
            },
        ],
    ),
    (
        "3. Tests y calidad",
        (139, 92, 246),
        [
            {
                "title": "run-tests.sh",
                "subtitle": "Suite completa pytest",
                "run": "./scripts/run-tests.sh",
                "alt": "uv run pytest -v",
                "desc": "Ejecuta todos los tests offline: L1, L2, fusion, RAG, agente, playbooks y UI.",
                "keys": "No requiere API keys",
                "when": "Antes de commit/PR o para validar el repo",
            },
            {
                "title": "run-benign-check.sh",
                "subtitle": "Corpus benigno sin CONTAIN",
                "run": "./scripts/run-benign-check.sh",
                "desc": "Tests focalizados: 42+ mensajes de soporte IT nunca deben recibir veredicto CONTAIN.",
                "keys": "No requiere API keys",
                "when": "CI rápido o verificar falsos positivos en L1/Fusion",
            },
        ],
    ),
    (
        "4. Benchmarks (playbooks de ataque)",
        (245, 158, 11),
        [
            {
                "title": "run-benchmarks.sh",
                "subtitle": "Benchmarks por defecto (sin juez)",
                "run": "./scripts/run-benchmarks.sh",
                "desc": "Alias de run-benchmarks-no-judge.sh. Ejecuta los 3 escenarios de ataque y comprueba expect_min_verdict.",
                "keys": "No requiere API keys",
                "when": "Medir defensa MTGuard offline (crescendo, salami, jailbreak)",
            },
            {
                "title": "run-benchmarks-no-judge.sh",
                "subtitle": "Benchmarks sin EscalationJudge",
                "run": "./scripts/run-benchmarks-no-judge.sh",
                "alt": "uv run Mudette-scenario --all",
                "desc": "Pipeline L1→L2→Fusion→UserGate solamente. Rápido y reproducible sin llamadas OpenAI.",
                "keys": "No requiere API keys",
                "when": "CI, regresiones de risk_score y veredictos",
            },
            {
                "title": "run-benchmarks-with-judge.sh",
                "subtitle": "Benchmarks con juez online",
                "run": "export JUDGE_API_KEY='sk-…'\n./scripts/run-benchmarks-with-judge.sh",
                "alt": "uv run Mudette-scenario --all --judge --judge-api-key $JUDGE_API_KEY",
                "desc": "Igual que los benchmarks pero activa EscalationJudge (modelo ligero) en turnos WATCH/ALERT con risk≥55.",
                "keys": "Obligatorio: JUDGE_API_KEY. Opcional: MAIN_API_KEY",
                "when": "Probar capa de juez con sesgo ALLOW y DENY→CONTAIN",
            },
            {
                "title": "run-scenario.sh",
                "subtitle": "Un solo escenario",
                "run": "./scripts/run-scenario.sh crescendo_credentials",
                "alt": "uv run Mudette-scenario --scenario jailbreak_direct",
                "desc": "Ejecuta un playbook concreto y muestra risk_score por turno.",
                "keys": "No requiere API keys (salvo flags --judge)",
                "when": "Depurar un ataque específico",
            },
        ],
    ),
    (
        "5. Documentación",
        (100, 116, 139),
        [
            {
                "title": "generate-glossary-pdf.sh",
                "subtitle": "Este glosario en PDF",
                "run": "./scripts/generate-glossary-pdf.sh",
                "desc": "Genera docs/Mudette-Command-Glossary.pdf con todas las órdenes explicadas visualmente.",
                "keys": "No requiere API keys",
                "when": "Compartir referencia con el equipo",
            },
        ],
    ),
]

CLI_COMMANDS = [
    ("Mudette-demo", "Demo web Gradio (:7860)", "uv run Mudette-demo"),
    ("Mudette-scenario --all", "Todos los benchmarks de ataque", "uv run Mudette-scenario --all"),
    ("Mudette-scenario --scenario ID", "Un escenario", "uv run Mudette-scenario --scenario crescendo_credentials"),
    ("pytest", "Tests offline", "uv run pytest -v"),
    ("build_kb.py", "Índice FAISS", "uv run python scripts/build_kb.py"),
]


class GlossaryPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        self.body_font = _register_fonts(self)
        self.mono_font = "Courier" if self.body_font == "Helvetica" else self.body_font

    def body(self, style: str = "", size: int = 10) -> None:
        self.set_font(self.body_font, style, size)

    def mono(self, style: str = "", size: int = 8) -> None:
        self.set_font(self.mono_font, style, size)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.body("I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Mudette - Command Glossary", align="R")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.body("I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def cover_page(pdf: GlossaryPDF) -> None:
    pdf.add_page()
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_y(55)
    pdf.body("B", 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 14, "Mudette", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.body("", 18)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, "Glosario de comandos y scripts", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)
    pdf.body("", 11)
    pdf.set_text_color(226, 232, 240)
    pdf.multi_cell(
        0,
        7,
        "Referencia visual para ejecutar la demo, tests y benchmarks.\n"
        "Los benchmarks sin juez son offline (sin API keys).\n"
        "Agente y juez usan API keys separadas cuando estan online.",
        align="C",
    )
    pdf.ln(30)
    pdf.body("B", 10)
    pdf.set_text_color(56, 189, 248)
    pdf.cell(0, 8, "Nexa Copilot + MTGuard", new_x="LMARGIN", new_y="NEXT", align="C")


def draw_command_card(pdf: GlossaryPDF, cmd: dict[str, str], accent: tuple[int, int, int]) -> None:
    x0 = pdf.get_x()
    y0 = pdf.get_y()
    card_h = 52
    if y0 + card_h > 270:
        pdf.add_page()
        y0 = pdf.get_y()

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(15, y0, 180, card_h, "DF")

    pdf.set_fill_color(*accent)
    pdf.rect(15, y0, 4, card_h, "F")

    pdf.set_xy(22, y0 + 4)
    pdf.body("B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, cmd["title"], new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(22)
    pdf.body("I", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, cmd.get("subtitle", ""), new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(22)
    pdf.mono("B", 8)
    pdf.set_text_color(30, 64, 175)
    pdf.multi_cell(170, 4, cmd["run"])

    if alt := cmd.get("alt"):
        pdf.set_x(22)
        pdf.mono("", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(170, 3.5, f"equiv: {alt}")

    pdf.set_x(22)
    pdf.body("", 8)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(170, 3.8, cmd["desc"])

    pdf.set_x(22)
    pdf.body("B", 7)
    pdf.set_text_color(180, 83, 9)
    pdf.cell(85, 4, f"API keys: {cmd.get('keys', 'N/A')}", new_x="RIGHT", new_y="TOP")
    pdf.body("", 7)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(85, 4, f"Cuando: {cmd.get('when', '')}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(x0, y0 + card_h + 4)


def section_page(pdf: GlossaryPDF, title: str, color: tuple[int, int, int], commands: list[dict]) -> None:
    pdf.add_page()
    pdf.body("B", 16)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*color)
    pdf.line(15, pdf.get_y(), 80, pdf.get_y())
    pdf.ln(6)
    for cmd in commands:
        draw_command_card(pdf, cmd, color)


def cli_reference_page(pdf: GlossaryPDF) -> None:
    pdf.add_page()
    pdf.body("B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Comandos uv / entry points", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.body("B", 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(51, 65, 85)
    col_w = (55, 55, 70)
    for i, h in enumerate(("Comando", "Que hace", "Ejemplo")):
        pdf.cell(col_w[i], 7, h, border=1, fill=True)
    pdf.ln()
    pdf.body("", 8)
    for name, purpose, example in CLI_COMMANDS:
        pdf.cell(col_w[0], 7, name, border=1)
        pdf.cell(col_w[1], 7, purpose, border=1)
        pdf.cell(col_w[2], 7, example, border=1)
        pdf.ln()

    pdf.ln(10)
    pdf.body("B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "Variables de entorno (benchmarks con juez)", new_x="LMARGIN", new_y="NEXT")
    pdf.mono("", 8)
    pdf.set_text_color(51, 65, 85)
    env_lines = [
        "JUDGE_API_KEY  - Obligatoria para run-benchmarks-with-judge.sh",
        "MAIN_API_KEY   - Opcional; agente Nexa online durante benchmark",
    ]
    for line in env_lines:
        pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.body("B", 11)
    pdf.cell(0, 8, "Flujo recomendado", new_x="LMARGIN", new_y="NEXT")
    pdf.body("", 9)
    flow = (
        "1. ./scripts/setup.sh\n"
        "2. ./scripts/run-tests.sh\n"
        "3. ./scripts/run-benchmarks-no-judge.sh\n"
        "4. ./scripts/run-demo.sh"
    )
    pdf.multi_cell(0, 5, flow)


def flow_diagram_page(pdf: GlossaryPDF) -> None:
    pdf.add_page()
    pdf.body("B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Mapa rapido: que script usar", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    rows = [
        ("Quiero...", "Script", (248, 250, 252)),
        ("Instalar el proyecto", "setup.sh", (255, 255, 255)),
        ("Abrir la demo web", "run-demo.sh", (255, 255, 255)),
        ("Correr todos los tests", "run-tests.sh", (255, 255, 255)),
        ("Benchmarks sin juez (CI)", "run-benchmarks-no-judge.sh", (255, 255, 255)),
        ("Benchmarks con juez LLM", "run-benchmarks-with-judge.sh", (255, 255, 255)),
        ("Un ataque concreto", "run-scenario.sh <id>", (255, 255, 255)),
        ("Verificar corpus benigno", "run-benign-check.sh", (255, 255, 255)),
        ("Regenerar KB FAISS", "build-kb.sh", (255, 255, 255)),
        ("Este PDF", "generate-glossary-pdf.sh", (255, 255, 255)),
    ]
    pdf.body("B", 9)
    for i, (a, b, bg) in enumerate(rows):
        pdf.set_fill_color(*bg)
        pdf.body("B" if i == 0 else "", 9)
        pdf.cell(90, 8, a, border=1, fill=True)
        pdf.cell(90, 8, b, border=1, fill=True)
        pdf.ln()


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = GlossaryPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    cover_page(pdf)
    flow_diagram_page(pdf)
    for title, color, commands in CATALOG:
        section_page(pdf, title, color, commands)
    cli_reference_page(pdf)

    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
