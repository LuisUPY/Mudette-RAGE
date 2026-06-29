"""Gradio demo — MTGuard multi-turn defense for Nexa Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import gradio as gr

from mtguard.agent import MTGuardSession
from mtguard.nim import DEFAULT_JUDGE_MODEL, DEFAULT_MAIN_MODEL
from mtguard.pack_loader import (
    DemoPack,
    get_playbook_scenario,
    nexa_summary_markdown,
    playbook_choices,
)
from mtguard.trace import format_layers_modal, format_trace_panel

PACK_DIR = Path(__file__).resolve().parents[3] / "demo_pack" / "nexa_copilot"
DEFAULT_PACK = DemoPack.load(PACK_DIR)


@dataclass
class AppSession:
    mtguard: MTGuardSession
    main_api_key: str = ""
    judge_api_key: str = ""
    judge_enabled: bool = False
    mode: str = "benign"
    playbook_id: str | None = None
    playbook_step: int = 0
    last_trace: dict | None = None
    history: list[dict[str, str]] = field(default_factory=list)


def _mode_from_radio(choice: str) -> str:
    return "redteam" if "Red" in choice else "benign"


def _playbook_dropdown_update(mode_label: str) -> gr.Dropdown:
    mode = _mode_from_radio(mode_label)
    choices = playbook_choices(DEFAULT_PACK, mode)
    return gr.Dropdown(choices=choices, value=choices[0][1] if choices else None)


def _session_status(main_key: str, judge_key: str, judge_on: bool) -> str:
    parts = []
    if main_key.strip():
        parts.append(f"**Agente:** NVIDIA NIM · `{DEFAULT_MAIN_MODEL}`")
    else:
        parts.append("**Agente:** NVIDIA API key principal **obligatoria**")
    if judge_on:
        if judge_key.strip():
            parts.append(f"**Juez:** habilitado · `{DEFAULT_JUDGE_MODEL}`")
        else:
            parts.append("**Juez:** NVIDIA API key del juez **obligatoria** si está activo")
    else:
        parts.append("**Juez:** desactivado")
    return " · ".join(parts)


def _api_error_response(
    app: AppSession | None,
    message: str,
    error: str,
) -> tuple[AppSession | None, list, str, str, dict | None]:
    history = list(app.history) if app else []
    history = [*history, {"role": "user", "content": message.strip()}]
    history = [
        *history,
        {"role": "assistant", "content": f"**Error API:** {error}"},
    ]
    if app:
        app.history = history
    return app, history, f"**Error:** {error}", "", app.last_trace if app else None


def start_session(
    main_api_key: str,
    judge_api_key: str,
    mode_label: str,
    judge_enabled: bool,
) -> tuple[AppSession, str, gr.update, gr.update, list, str, str, gr.update]:
    mode = _mode_from_radio(mode_label)
    main_key = (main_api_key or "").strip()
    judge_key = (judge_api_key or "").strip()
    if not main_key:
        raise gr.Error(
            "Error Crítico: No se detectó la NVIDIA API Key principal para Nexa Copilot."
        )
    if judge_enabled and not judge_key:
        raise gr.Error(
            "Error Crítico: El Juez de Escalación está activo pero requiere una NVIDIA API Key "
            "válida para el modelo mini juez."
        )
    judge_on = judge_enabled and bool(judge_key)

    session = AppSession(
        mtguard=MTGuardSession.from_pack_dir(
            PACK_DIR,
            main_api_key=main_key,
            judge_api_key=judge_key or None,
            judge_enabled=judge_on,
        ),
        main_api_key=main_key,
        judge_api_key=judge_key,
        judge_enabled=judge_on,
        mode=mode,
    )
    choices = playbook_choices(DEFAULT_PACK, mode)
    playbook_val = choices[0][1] if choices else None
    return (
        session,
        _session_status(main_key, judge_key, judge_enabled),
        gr.update(visible=False),
        gr.update(visible=True),
        [],
        "*Esperando primer mensaje…*",
        "",
        gr.update(value=playbook_val, choices=choices),
    )


def handle_chat(
    message: str,
    app: AppSession | None,
) -> tuple[AppSession | None, list, str, str, dict | None]:
    if not app or not message.strip():
        return app, app.history if app else [], format_trace_panel(None), "", None

    try:
        result = app.mtguard.turn(message.strip())
    except Exception as exc:
        return _api_error_response(app, message, str(exc))

    trace = result.trace.to_dict()
    app.last_trace = trace
    app.history = [*app.history, {"role": "user", "content": message.strip()}]
    app.history = [*app.history, {"role": "assistant", "content": result.response}]
    return app, app.history, format_trace_panel(trace), format_layers_modal(trace), trace


def playbook_next_turn(
    app: AppSession | None,
    playbook_id: str | None,
) -> tuple[AppSession | None, list, str, str, dict | None, str]:
    if not app or not playbook_id:
        return app, [], format_trace_panel(None), "", None, ""

    scenario = get_playbook_scenario(DEFAULT_PACK, app.mode, playbook_id)
    if not scenario:
        return app, app.history, format_trace_panel(app.last_trace), "", app.last_trace, ""

    app.playbook_id = playbook_id
    if app.playbook_step >= len(scenario["turns"]):
        status = "Playbook completado."
        return app, app.history, format_trace_panel(app.last_trace), "", app.last_trace, status

    message = scenario["turns"][app.playbook_step]
    app.playbook_step += 1
    app, history, panel, layers, trace = handle_chat(message, app)
    remaining = len(scenario["turns"]) - app.playbook_step
    status = f"Turno {app.playbook_step}/{len(scenario['turns'])} enviado. Quedan {remaining}."
    return app, history, panel, layers, trace, status


def reset_playbook(app: AppSession | None, playbook_id: str | None) -> AppSession | None:
    if app:
        app.playbook_id = playbook_id
        app.playbook_step = 0
    return app


def show_layers(trace: dict | None) -> tuple[gr.update, str]:
    return gr.update(visible=True), format_layers_modal(trace)


def hide_layers() -> gr.update:
    return gr.update(visible=False)


def reset_conversation(app: AppSession | None) -> tuple[AppSession | None, list, str, str, dict | None, str]:
    if app:
        app.mtguard.reset()
        app.history = []
        app.last_trace = None
        app.playbook_step = 0
    return app, [], "*Sesión reiniciada.*", "", None, ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Mudette — MTGuard Demo") as demo:
        app_state = gr.State(None)
        trace_state = gr.State(None)

        gr.Markdown("# Mudette · MTGuard Demo")
        gr.Markdown(nexa_summary_markdown(DEFAULT_PACK))

        with gr.Row(visible=True) as setup_row:
            with gr.Column(scale=1):
                main_api_key = gr.Textbox(
                    label="NVIDIA API Key — Agente principal (Nexa Copilot)",
                    type="password",
                    placeholder="nvapi-… (llama-3.3-70b-instruct)",
                )
                judge_api_key = gr.Textbox(
                    label="NVIDIA API Key — Juez (EscalationJudge)",
                    type="password",
                    placeholder="nvapi-… (llama-3.1-8b-instruct)",
                )
                mode = gr.Radio(
                    ["Modo Usuario (benigno)", "Modo Red Team"],
                    value="Modo Usuario (benigno)",
                    label="Modo",
                )
                judge_toggle = gr.Checkbox(
                    label="Habilitar Juez (solo con API key del juez)",
                    value=False,
                )
                start_btn = gr.Button("Iniciar sesión", variant="primary")
            with gr.Column(scale=1):
                gr.Markdown(
                    "1. **NVIDIA API key del agente es obligatoria** (build.nvidia.com).\n"
                    f"2. Modelo principal: `{DEFAULT_MAIN_MODEL}` · Juez: `{DEFAULT_JUDGE_MODEL}`.\n"
                    "3. Errores de NIM (clave inválida, cuota, red) se muestran en el chat."
                )

        judge_status = gr.Markdown("")

        with gr.Row(visible=False) as main_row:
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Nexa Copilot", height=420)
                with gr.Row():
                    user_input = gr.Textbox(
                        label="Mensaje",
                        placeholder="Escribe tu consulta de soporte IT…",
                        scale=4,
                    )
                    send_btn = gr.Button("Enviar", variant="primary", scale=1)
                reset_btn = gr.Button("Reiniciar conversación")

            with gr.Column(scale=2):
                trace_panel = gr.Markdown("*Esperando primer mensaje…*")
                layers_btn = gr.Button("Ver capas")
                with gr.Column(visible=False) as layers_box:
                    gr.Markdown("### Capas de defensa MTGuard")
                    layers_md = gr.Markdown()
                    layers_close = gr.Button("Cerrar")
                gr.Markdown("### Playbooks")
                playbook_dd = gr.Dropdown(
                    label="Escenario",
                    choices=playbook_choices(DEFAULT_PACK, "benign"),
                    value=playbook_choices(DEFAULT_PACK, "benign")[0][1],
                )
                playbook_btn = gr.Button("Siguiente turno del playbook")
                playbook_status = gr.Markdown("")

        start_btn.click(
            start_session,
            inputs=[main_api_key, judge_api_key, mode, judge_toggle],
            outputs=[app_state, judge_status, setup_row, main_row, chatbot, trace_panel, layers_md, playbook_dd],
        )

        mode.change(_playbook_dropdown_update, inputs=[mode], outputs=[playbook_dd])

        send_inputs = [user_input, app_state]

        def _send(msg, app):
            app, hist, panel, layers, trace = handle_chat(msg, app)
            return app, hist, panel, layers, trace, ""

        send_btn.click(
            _send,
            inputs=send_inputs,
            outputs=[app_state, chatbot, trace_panel, layers_md, trace_state, user_input],
        )
        user_input.submit(
            _send,
            inputs=send_inputs,
            outputs=[app_state, chatbot, trace_panel, layers_md, trace_state, user_input],
        )

        playbook_btn.click(
            playbook_next_turn,
            inputs=[app_state, playbook_dd],
            outputs=[app_state, chatbot, trace_panel, layers_md, trace_state, playbook_status],
        )

        playbook_dd.change(reset_playbook, inputs=[app_state, playbook_dd], outputs=[app_state])

        layers_btn.click(show_layers, inputs=[trace_state], outputs=[layers_box, layers_md])
        layers_close.click(hide_layers, outputs=[layers_box])

        reset_btn.click(
            reset_conversation,
            inputs=[app_state],
            outputs=[app_state, chatbot, trace_panel, layers_md, trace_state, playbook_status],
        )

    return demo


def main() -> None:
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=gr.themes.Soft(),
    )


if __name__ == "__main__":
    main()
