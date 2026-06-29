# Mudette

**Nexa Copilot** conoce secretos y políticas internas (simulados). Prueba un flujo normal o un ataque gradual; el panel muestra cómo **MTGuard** detecta el acercamiento antes del exfil.

Demo web de defensa multi-turno contra prompt injection (Crescendo, salami slicing, jailbreak gradual) protegiendo un agente empresarial ficticio: **Nexa Copilot** (NexaCorp IT).

## Quick start

```bash
./scripts/setup.sh
./scripts/run-tests.sh
export MAIN_API_KEY='nvapi-…'   # obligatoria para benchmarks y demo (NVIDIA NIM)
./scripts/run-benchmarks-no-judge.sh
./scripts/run-demo.sh
```

Abre [http://localhost:7860](http://localhost:7860).

## Glosario visual (PDF)

```bash
./scripts/generate-glossary-pdf.sh
```

Genera **`docs/Mudette-Command-Glossary.pdf`** — referencia ilustrada de cada script y comando.

## Scripts principales

| Script | Qué hace |
|--------|----------|
| `setup.sh` | Instalar dependencias (`uv sync`) |
| `run-demo.sh` | Demo web Gradio |
| `run-tests.sh` | Suite pytest (API mockeada) |
| `run-benchmarks-no-judge.sh` | Benchmarks de ataque **sin** juez (`MAIN_API_KEY`) |
| `run-benchmarks-with-judge.sh` | Benchmarks **con** juez (`MAIN_API_KEY` + `JUDGE_API_KEY`) |
| `run-scenario.sh` | Un playbook por ID |
| `run-benign-check.sh` | Corpus benigno → 0 CONTAIN |
| `build-kb.sh` | Regenerar índice FAISS |
| `generate-glossary-pdf.sh` | PDF de comandos |

Ver [QUICKSTART.md](QUICKSTART.md) para más detalle.

## Pipeline MTGuard

```
user_message → L1 RegexGuard → L2 TrajectoryGuard → Fusion → UserGate
  → [risk≥55, WATCH|ALERT] EscalationJudge → [si permitido] LLM + RAG FAISS
```

## API keys (demo web)

| Campo | Uso | Modelo |
|-------|-----|--------|
| Agente principal | **Obligatoria** — respuestas Nexa Copilot | `meta/llama-3.3-70b-instruct` |
| Juez | Obligatoria si activas el juez | `meta/llama-3.1-8b-instruct` |

Obtén las keys en [build.nvidia.com](https://build.nvidia.com). Endpoint: `https://integrate.api.nvidia.com/v1`.

Sin key del agente la sesión no inicia. Errores de NVIDIA NIM se muestran en terminal y en la UI.

## Visión v2 (no implementada)

Otros `demo_pack/` por empresa (mismo motor MTGuard).

## Licencia

Demo de investigación — credenciales en `secrets_vault.json` son **simuladas**.
