# QUICKSTART — Mudette

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## 1. Instalar

```bash
git clone <repo>
cd Mudette-F
./scripts/setup.sh
```

## 2. Validar

```bash
./scripts/run-tests.sh                    # pytest con API mockeada (sin keys reales)
export MAIN_API_KEY='nvapi-…'                # obligatoria para benchmarks (NVIDIA NIM)
./scripts/run-benchmarks-no-judge.sh
```

Salida esperada de benchmarks: `PASS` en `crescendo_credentials`, `salami_export`, `jailbreak_direct`.

## 3. Demo web

```bash
./scripts/run-demo.sh
```

1. **NVIDIA API key del agente obligatoria** (build.nvidia.com). Key del juez solo si activas el toggle.
2. Modo Usuario o Red Team → **Iniciar sesión**.
3. Chatea o usa **Siguiente turno del playbook**.
4. **Ver capas** muestra L1, L2, Fusion, Judge, Gate.

## 4. Benchmarks con juez

```bash
export MAIN_API_KEY='nvapi-…'
export JUDGE_API_KEY='nvapi-…'
./scripts/run-benchmarks-with-judge.sh
```

## 5. Un escenario

```bash
./scripts/run-scenario.sh crescendo_credentials
./scripts/run-scenario.sh ticket_status   # modo benigno vía CLI:
uv run Mudette-scenario --scenario ticket_status --mode benign
```

## 6. PDF de comandos

```bash
./scripts/generate-glossary-pdf.sh
open docs/Mudette-Command-Glossary.pdf
```

## Comandos uv equivalentes

| Acción | Comando |
|--------|---------|
| Demo | `uv run Mudette-demo` |
| Benchmarks | `uv run Mudette-scenario --all` |
| Tests | `uv run pytest -v` |
| KB | `uv run python scripts/build_kb.py` |

## Estructura

```
demo_pack/nexa_copilot/   # Agente, vault, playbooks, KB
src/mtguard/              # Motor MTGuard
corpus/                   # benign.json + attacks.json
scripts/                  # Scripts documentados + PDF
docs/                     # Glosario PDF generado
```
