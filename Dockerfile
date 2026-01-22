# SPDX-FileCopyrightText: 2025 chatvote
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

FROM python:3.11.3-slim

# Install Poetry
RUN pip install poetry

# Copy only the necessary files for Poetry (to leverage Docker layer caching)
COPY pyproject.toml poetry.lock /app/

WORKDIR /app

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code and optional Firebase credentials
# This will include files like:
# - chat-vote-dev-firebase-adminsdk-fbsvc-5357066618.json
# if they are present in the project root.
# If these files are absent, Google Application Default Credentials must be provided when running the container
COPY . /app

CMD ["poetry", "run", "python", "-m", "src.aiohttp_app", "--host", "0.0.0.0", "--port", "8080"]
