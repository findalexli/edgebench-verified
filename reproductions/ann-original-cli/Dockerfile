# Same pinned Python base and installed core versions as the accepted ANN run.
FROM python@sha256:2ed6491b93cd49272ee6de2b5a38440c3448360322c089fc23e370722d74179d
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
COPY evidence/selected/maintained-core-runtime-versions.txt /tmp/requirements.lock.txt
RUN python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/requirements.lock.txt
COPY pyproject.toml README.md /opt/source/
COPY sforge /opt/source/sforge
RUN python -m pip install --no-cache-dir --no-deps /opt/source
COPY evidence/selected/maintained-core-runtime.json /opt/expected-runtime.json
RUN python -c "import json,platform,importlib.metadata as m; d=json.load(open('/opt/expected-runtime.json')); assert platform.python_version()=='3.12.15'; assert all(m.version(p['name'])==p['version'] for p in d['packages'])"
WORKDIR /output
