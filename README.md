# Hiring test for DevOps Engineer position

## Introduction

This test is designed to assess your skills as a DevOps engineer.

Throughout this test, you will be required to complete practical tasks based on an existing application, which you will need to run locally on your computer.

The provided application follows the RealWorld specification to implement a full-stack blogging/social media platform similar to Medium. The technical stack contains a backend implemented in Python with FastAPI framework and a PostgreSQL database, and a frontend implemented using React.

Feel free to explore the application to discover its features. Note that the application (intentionally) contains some bugs and some questionable design decisions.

---

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [How to submit your answers](#how-to-submit-your-answers)
- [How to run the application (legacy, manual setup)](#how-to-run-the-application-legacy-manual-setup)
- [How to run the application's tests? (legacy, manual setup)](#how-to-run-the-applications-tests-legacy-manual-setup)
- [Local development environment (recommended)](#local-development-environment-recommended)
- [Continuous Integration](#continuous-integration)
- [Releasing](#releasing)
- [Tasks](#tasks)
  - [Task 1: Standard local development environment](#task-1-standard-local-development-environment)
  - [Task 2: Continuous Integration](#task-2-continuous-integration)
  - [Task 3: Releasing](#task-3-releasing)
  - [Task 4: Deployment (discussion only)](#task-4-deployment-discussion-only)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## How to submit your answers

Open a separate pull request for each task of this test. A pull request template is provided in `.github/pull_request_template.md`. You _can_ use this template to structure your pull requests, but feel free to adapt it as you see fit.
In each pull request, you should explain the changes you made to the codebase, and how they solve the task at hand. You can also add any comments or decisions you have about the task.

AI-assisted coding tools (Claude, Copilot, Codex, Gemini, etc.) are allowed. Whether you choose to use them or solve the tasks manually is entirely up to you. If you do use such a tool, please declare it explicitly in the pull request of each task where it was used.

## How to run the application (legacy, manual setup)

> [!NOTE]
> This manual setup is kept for reference only. The recommended way to run the application locally is described in [Local development environment (recommended)](#local-development-environment-recommended) below, and requires none of the local installs described here.

Running this application locally requires the installation of [uv](https://docs.astral.sh/uv/getting-started/installation/), [Node.js and npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm), as well as PostgreSQL.

To run the application's backend, enter the `backend` folder, then:

1. Start the PostgreSQL database. For example, rely on Docker by running
   ```bash
   docker run --name conduit-db \
      --env-file .env \
      -p 5432:5432 \
      -d postgres:16-alpine
   ```

2. Install dependencies and populate the database by running the following commands:
   ```bash
   uv sync
   uv run alembic upgrade head
   ```
3. Run the backend server by running
   ```bash
   uv run uvicorn conduit.app:app --host 0.0.0.0 --port 8080
   ```

The backend should run on http://localhost:8080. You can access the backend API documentation at http://localhost:8080/.

To run the application's frontend, enter the `frontend` folder, then:

1. Install dependencies and run the frontend server by running the following commands:
   ```bash
   npm install
   ```

2. Before running the frontend server, make sure to set the `REACT_APP_BACKEND_URL` environment variable to point to the backend server you just ran:
   ```bash
   export REACT_APP_BACKEND_URL='http://localhost:8080/api'
   ```

3. Run the frontend server:
   ```bash
   npm start
   ```

The frontend should run on http://localhost:4100.

## How to run the application's tests? (legacy, manual setup)

> [!NOTE]
> This manual setup is kept for reference only. See [Local development environment (recommended)](#local-development-environment-recommended) below for the recommended way to run the test suites (`make test-backend` / `make test-frontend`), which requires none of the local installs described here.

**Backend tests**

The backend integration tests require a dedicated PostgreSQL instance. The test database connection is configured in `backend/.env.test`. The tests create the schema automatically on first run and truncate all tables between each test, so no manual migration step is needed. Start the test database using Docker:

```bash
docker run --name conduit-test-db \
  -e POSTGRES_USER=conduit_test -e POSTGRES_PASSWORD=conduit_test -e POSTGRES_DB=conduit_test \
  -p 5433:5432 \
  -d postgres:16-alpine
```

Then, from the `backend` folder, install application and test dependencies

```bash
uv sync --group dev
```

then run the tests:

```bash
uv run pytest tests/ -v
```

**Frontend tests**

From the `frontend` folder, install dependencies

```bash
npm install
```

then run the tests:

```bash
npm test -- --watchAll=false
```

## Local development environment (recommended)

The whole stack — frontend, backend and PostgreSQL — runs with a single command, with no local install of uv, Node.js or PostgreSQL required.

**Prerequisites**

- [Docker](https://docs.docker.com/get-docker/) (with Compose v2, bundled with Docker Desktop)
- [GNU Make](https://www.gnu.org/software/make/) — a thin, discoverable wrapper around the `docker compose` commands below; not strictly required, since every target can be run as the equivalent `docker compose` command directly (see [Makefile](./Makefile))

**Quick start**

```bash
make up
```

This builds the images, starts PostgreSQL, applies database migrations automatically, and starts the backend and frontend with hot reload on file changes:

- Frontend: http://localhost:4100
- Backend API docs: http://localhost:8080

**Other commands**

All recurring commands (starting/stopping the stack, running the backend and frontend test suites, applying migrations by hand, tailing logs, ...) are defined as `make` targets. Run `make help` to list them, or read the [Makefile](./Makefile) directly.

**One-time setup: git hooks**

```bash
make install-hooks
```

Wires up this repo's `pre-commit` (backend + frontend linters) and `pre-push` (linters + both test suites) hooks, so style/test issues are caught before they reach a pull request. Skip a one-off check with `git commit`/`git push --no-verify`.

## Continuous Integration

Every pull request runs automatically on GitHub Actions, scoped to what it actually touches:

- **`CI - Backend`** (on changes under `backend/`, `docker-compose.yml`, `Makefile`): ruff lint + format check, the pytest suite against a disposable Postgres service, and a Docker build sanity check (no push).
- **`CI - Frontend`** (on changes under `frontend/`, `docker-compose.yml`, `Makefile`): eslint + prettier check, the Jest suite, and a Docker build sanity check (no push).
- **`Release`**: on every push to `main`, builds and pushes the backend and frontend images to GHCR (tagged with the commit SHA, plus a rolling `main` tag), then cuts a release — see [Releasing](#releasing) below.

See [.github/workflows](./.github/workflows) for the full definitions.

## Releasing

Every merge to `main` is a release: no manual step, no hand-editing [infrastructure/release.yaml](./infrastructure/release.yaml). The `Release` workflow, once the images above are pushed:

1. Reads the label on the pull request that was just merged to decide the version bump.
2. Bumps `infrastructure/release.yaml`'s `version`, points its `images` at the commit's freshly-pushed GHCR images, and commits that change directly to `main`.
3. Tags the release (`vX.Y.Z`) and publishes a [GitHub Release](../../releases) with auto-generated notes (grouped from the PRs merged since the last release).

**Label your PR before merging** — this is what decides the version bump:

| Label | Bump | Use for |
|---|---|---|
| `release:major` | `X`.0.0 | Breaking change |
| `release:minor` | x.`Y`.0 | New backward-compatible feature |
| `release:patch` (or no label) | x.y.`Z` | Bug fix, chore, docs, anything else — **this is the default if you forget to label** |

Forgetting a label never blocks your merge — it just falls back to a patch release, so there's no excuse to skip labeling deliberately, but also no way to get stuck.

**To see releases**: the [Releases page](../../releases) lists every version with its changelog. **To see what's currently declared**: [infrastructure/release.yaml](./infrastructure/release.yaml) on `main` always reflects it — that file is the single source of truth an external tool syncs production against.

## Tasks

> [!IMPORTANT]
> The suggested effort for this test is 2 to 4 hours. Complete as many tasks as you can with production-minded quality. If you cannot finish a task, simply document what is done, what remains, and your intended next steps.

Each task describes the outcome we are looking for, not the way to get there. The tooling and the trade-offs are yours to choose, so use your pull request to explain why you picked your solution.

### Task 1: Standard local development environment

Today, running this application means installing `uv`, Node.js and a PostgreSQL server on your own machine, then starting three things by hand in the right order. We want a new engineer to clone this repository and get the whole stack — frontend, backend and database — running and reachable in a browser without that setup work.

We also want the recurring commands of this project (starting the stack, running the tests, running the linters) to be discoverable and repeatable.

### Task 2: Continuous Integration

We want every change proposed to this repository to be validated automatically, before a human spends time reviewing it: opening a pull request should give a clear signal, on that pull request, on whether the test suites pass and whether the code respects a consistent style. The project has, currently, no tools to enforce a consistent style on the backend code, nor on the frontend.

Once a change lands on `main` branch, we also want the deployable artifacts of the application to be built and published automatically, so that any commit of `main` has a corresponding build that can be retrieved and deployed later.

### Task 3: Releasing

We want the application to be released following GitOps principles: the `main` branch is the single source of truth for what runs in production, and [infrastructure/release.yaml](./infrastructure/release.yaml) declares the version that should be running. Releasing today means editing that file by hand, and we want merging a pull request into `main` to be enough to release. Assume that we already provide a tool to synchronize the git configuration and the application running in production.

A release should also be easy to follow from the outside: which versions exist, what changed between them, and which one is currently declared.

### Task 4: Deployment (discussion only)

There is nothing to deliver for this task, and nothing to prepare: we will simply take 10 to 15 minutes during the interview to talk about how you would run this application in production. It is an informal conversation about your approach, not an exercise.
