# Mudette

**Nexa Copilot** conoce secretos y políticas internas (simulados). Prueba un flujo normal o un ataque gradual; el panel muestra cómo **MTGuard** detecta el acercamiento antes del exfil.

Demo web de defensa multi-turno contra prompt injection (Crescendo, salami slicing, jailbreak gradual) protegiendo un agente empresarial ficticio: **Nexa Copilot** (NexaCorp IT).

## Quick start

```bash
./scripts/setup.sh
./scripts/run-tests.sh
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
| `run-tests.sh` | Suite pytest offline |
| `run-benchmarks-no-judge.sh` | Benchmarks de ataque **sin** juez (CI) |
| `run-benchmarks-with-judge.sh` | Benchmarks **con** juez (`JUDGE_API_KEY`) |
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
| Agente principal | Respuestas Nexa Copilot | `gpt-4o` |
| Juez | EscalationJudge | `gpt-4o-mini` |

Sin key del agente → respuestas offline vía RAG. El juez requiere su propia key.

## Visión v2 (no implementada)

Otros `demo_pack/` por empresa (mismo motor MTGuard).

## Licencia

Demo de investigación — credenciales en `secrets_vault.json` son **simuladas**.
