# Lessons Learned So Far

## Docker Pitfall

If your Python environment is on Windows and you accidentally mount your entire project directory into the container like this:

```yaml
volumes:
  - .:/app
```

**Especially without this line, below the - .:/app**

```yaml
volumes:
  - /app/.venv
```

your Docker container will do exactly what you instructed: it will copy **everything** from your host into the container.

This means your **Windows** virtual environment (`.venv`) will overwrite the **Linux** virtual environment inside Docker, causing it to break because Windows packages are incompatible with Linux.

## The Fix

Add an anonymous volume for the virtual environment:

```yaml
volumes:
  - .:/app
  - /app/.venv
```

This tells Docker to keep `/app/.venv` isolated inside the container, preventing your host's `.venv` from being copied over.

## Caveat

The downside is that your host's `.venv` and the container's `.venv` can become **out of sync** whenever you install new packages.

## Ways to Mitigate This

### 1. Best Practice (Recommended)

Rebuild the container and recreate the anonymous volumes:

```bash
docker compose up --build --renew-anon-volumes
```

This ensures the container recreates its virtual environment from scratch using your project's dependency definitions.

### 2. Sync the Running Container

If your container is already running, you can update its virtual environment without rebuilding:

```bash
docker compose exec < your_service_name > uv sync
```

This installs any newly added dependencies inside the container's isolated `.venv`.

## Celery pitfall during Docker setup:

The exact pitfall that I ran into from the above setup, forgetting the `- /app/.venv` line, was that Celery would not start properly. It would throw an error about missing packages, even though they were installed in the host's `.venv`. This is because Celery was trying to use the host's virtual environment instead of the container's isolated one.
