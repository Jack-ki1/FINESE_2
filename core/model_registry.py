# core/model_registry.py (new file)
import json, os, uuid
from datetime import datetime

_REGISTRY_PATH = "models/registry.json"

def _load():
    if os.path.exists(_REGISTRY_PATH):
        with open(_REGISTRY_PATH) as f:
            return json.load(f)
    return {}

def _save(data):
    os.makedirs("models", exist_ok=True)
    with open(_REGISTRY_PATH, "w") as f:
        json.dump(data, f, indent=2)

def register(name, model_type, metrics, hyperparams, version="1.0"):
    reg = _load()
    model_id = str(uuid.uuid4())
    reg[model_id] = {
        "id": model_id,
        "name": name,
        "type": model_type,
        "metrics": metrics,
        "hyperparameters": hyperparams,
        "version": version,
        "created_at": datetime.now().isoformat(),
        "status": "registered",
    }
    _save(reg)
    return model_id

def list_models():
    return list(_load().values())

def get_model(model_id):
    return _load().get(model_id)