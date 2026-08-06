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


## A git reflog that saved my entire work:

We've all been there—a late-night coding session, a few too many branches, and one clumsy command that makes your entire project vanish into thin air. Here is how a catastrophic Git mistake almost wiped out my Django backend, and how `git reflog` acted as the ultimate time machine to bring it back from the dead.

### The Backdrop
I was deep in the zone working on a `Register_endpoint` branch for a Django application, carefully building out:
* Disposable email domain checkers
* Form/serializer validation layers
* Celery task offloaders for generic background responses
* DB migration files

### The Incident 
While sitting on my feature branch, I meant to merge my feature into main, but accidentally ran:
```bash
git merge main
```
This unintended merge created a messy hybrid commit (`b511491`). Realizing something went sideways, I panicked, checked out `main`, and tried to forcefully reset my way out of it. 

### The Disaster
Instead of resetting to safety, I mistakenly targeted an older migration commit hash (`754304e`) from earlier in the day:
```bash
git reset --hard 754304e
```
**The result:** Instant cardiac arrest. My code editor flashed red with deletions. My views, serializers, and validation logic completely disappeared from my disk. The working directory was cleared out, and my recent work was entirely gone.

### The Rescue via `git reflog`
Because Git rarely actually deletes anything, I used `git reflog` to look past my current broken `HEAD` and see the hidden history of the repository:

```bash
754304e HEAD@{0}: reset: moving to 754304e <--- (Where everything vanished)
b511491 HEAD@{1}: checkout: moving from Register_endpoint to main
...
b511491 HEAD@{5}: merge Register_endpoint: Fast-forward <--- (The Golden Commit!)
```

Even though my local folder was empty, the reflog proved that my completed code was still floating in Git's memory at commit `b511491`. 

### The Fix
To fix it, I jumped straight past the panic-reset and forced my repository forward to the exact moment before the file destruction:
```bash
git reset --hard b511491
```

Instantly, all my Django files reappeared in my editor exactly as I left them. 

### Lesson Learned
Never trust your eyes when a `reset --hard` clears your screen. Your files aren't gone until Git says they're gone. Always trust `git reflog`.

