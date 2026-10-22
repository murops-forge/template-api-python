# template-api-python

FastAPI service template used by [Forge](https://github.com/murops/forge). Dependencies are managed with [uv](https://docs.astral.sh/uv/).

## Running

```bash
uv sync
uv run pytest
uv run uvicorn app.main:app --reload --port 8080
curl 'localhost:8080/hello?name=forge'
```

Or with Docker:

```bash
docker build -t app .
docker run --rm -p 8080:8080 app
```

## CI

`.github/workflows/ci.yml` runs on pushes to `main`, `homol` and `desen` and on every pull request:

- `test`: ruff lint and format check, pytest with coverage
- `trivy`: scans the Dockerfile and the built image, fails on fixable HIGH/CRITICAL findings and uploads the report to the Security tab
- `sonar`: SonarCloud analysis, the quality gate fails the job on pull requests. Skipped when the organization has no `SONAR_TOKEN`

These are the checks Forge requires on `main` and `homol`.
