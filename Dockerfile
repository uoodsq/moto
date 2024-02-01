FROM python:3.11

COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY moto moto

RUN pip install .

ENTRYPOINT ["python", "-m", "moto"]
