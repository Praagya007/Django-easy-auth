# Use the lightweight Python 3.12 image as the base image for the Docker container.
FROM python:3.12-slim 

# Create a working directory in the container for the application code., called /app.
WORKDIR /app 

# System dependencies, esp. for psycopg2, which is a PostgreSQL adapter for Python.

#This does this exactly: 
# 1) RUN: Execute this command during the image build process.

# 2) apt-get-update: Update the local index of available packages from the internet. It is, 
# located at files: /app/apt/sources.list.d/debian.sources.

# 3) && apt-get-install -y: And install the following packages. Note -y flag automatically confirms prompts during installation.

# 4) --no-install-recommends: Avoids installing unnecessary recommended packages, keeping the image smaller.

# 5) build-essential: Installs bundle of essential packages for compiling software, including gcc, g++, make, etc.

# 6) libpq-dev: Installs the development libraries and headers for PostgreSQL.

# 7) && rm -rf /var/lib/apt/lists/*: Delete them package list installed during apt-get update to reduce the image size. 
# This is a common practice in Dockerfiles to keep the final image as small as possible.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


#This does this exactly:
# 1) COPY --from=ghcr.io/astral-sh/uv:latest: Grabs a file from a separate, 
#  external image provided by Astral rather than your current build steps.

# 2) /uv: The path of the compiled uv binary file inside that external image.

# 3) /usr/local/bin/uv: The destination path inside your new image where the file is placed, 
# making it globally available as a command-line tool.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv


# Copy the pyproject.toml and put them in a container, which is the dependencies of the project.

# uv.lock file pins exact versions of dependencies.
# The * sign means optional, even if the file doesn't exist, the build will continue without error.

# ./ is the destination inside container, which is the current working directory /app.
COPY pyproject.toml uv.lock* ./


# Installs dependencies using uv with a smart fallback mechanism:
# 1. Attempts --frozen first: Fast and secure. Fails if pyproject.toml and uv.lock do not match 
#    (e.g., due to manual pyproject.toml edits, bad git merges, or a missing uv.lock file).

# 2. Falls back to a standard sync: Automatically updates/generates the lockfile during build if out of sync.

# --no-install-project ensures heavy 3rd-party libs are cached before copying local source code.

RUN uv sync --frozen --no-install-project || uv sync --no-install-project

#Imp fix: Add the uv virtual environment to the system PATH. Do not forget the :$PATH at the end,
# Otherwise, Docker forgets that Linux commands exist on this container lol😂

# Optimization: 
# Logs appear in your terminal asap, no buffering.
# Python won't write those annoying .pyc files to disk.
ENV PATH="/app/.venv/bin:$PATH" \
PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1

#COPY . . builds the code into the permanent image for production, 
# while the bind-mount .:/app overrides it at runtime with your live files for development.
COPY . .


EXPOSE 8000

# Define the default startup command (MUST BE LAST)
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000"]
