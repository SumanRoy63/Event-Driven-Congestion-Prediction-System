import os
import shutil
import json
from fastapi import APIRouter, HTTPException
from src.api.db.database import engine
from src.api.db import models
from src.api.services.model_manager import evict_from_cache, clear_cache

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
REGISTRY_PATH = os.path.join(MODELS_DIR, "model_registry.json")


def _load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {"versions": {}}
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)


def _save_registry(registry):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=4)


# ------------------------------------------------------------------
# POST /admin/reset — Full system wipe (DB + all models + cache)
# ------------------------------------------------------------------
@router.post("/admin/reset")
def reset_system():
    """
    Instantly resets the entire system:
    1. Drops all database tables and recreates them empty.
    2. Deletes all generated ML models and artifacts.
    3. Resets model_registry.json.
    4. Purges the in-memory model cache.
    """
    # 1. Reset Database (Drop all data and recreate empty schema)
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

    # 2. Clear Models Directory
    if os.path.exists(MODELS_DIR):
        for item in os.listdir(MODELS_DIR):
            item_path = os.path.join(MODELS_DIR, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif item.endswith(".pkl") or item.endswith(".png"):
                    os.remove(item_path)
            except Exception as e:
                print(f"Failed to delete {item}: {e}")

    # 3. Reset Model Registry
    _save_registry({"versions": {}})

    # 4. Purge in-memory cache
    evicted = clear_cache()

    return {
        "status": "success",
        "message": f"System completely reset! Database emptied, model artifacts purged, {evicted} cached model(s) evicted.",
    }


# ------------------------------------------------------------------
# DELETE /admin/models/{version_name} — Remove a single model version
# ------------------------------------------------------------------
@router.delete("/admin/models/{version_name}")
def delete_model_version(version_name: str):
    """
    Deletes a single model version:
    1. Removes its entry from model_registry.json.
    2. Deletes the versioned directory on disk (if it exists).
    3. If the version stored .pkl files at the models root (path == ""),
       those root-level .pkl files are also removed.
    4. Evicts the version from the in-memory LRU cache.
    """
    registry = _load_registry()
    versions = registry.get("versions", {})

    if version_name not in versions:
        raise HTTPException(
            status_code=404,
            detail=f"Model version '{version_name}' not found in registry.",
        )

    meta = versions.pop(version_name)
    _save_registry(registry)

    # Delete artifacts from disk
    model_path = meta.get("path", "")
    deleted_files = []

    if model_path:
        # Versioned subdirectory (e.g. models/v_20260619_143000/)
        version_dir = os.path.join(MODELS_DIR, model_path)
        if os.path.isdir(version_dir):
            shutil.rmtree(version_dir)
            deleted_files.append(f"directory: {model_path}/")
    else:
        # Root-level .pkl files (baseline models stored at models/ root)
        root_pkls = [
            "road_closure_xgb.pkl",
            "severity_xgb.pkl",
            "priority_encoder.pkl",
            "encoders.pkl",
            "feature_columns.pkl",
        ]
        for pkl in root_pkls:
            pkl_path = os.path.join(MODELS_DIR, pkl)
            if os.path.exists(pkl_path):
                os.remove(pkl_path)
                deleted_files.append(pkl)

    # Evict from in-memory cache
    evict_from_cache(version_name)

    return {
        "status": "success",
        "message": f"Version '{version_name}' deleted.",
        "deleted_artifacts": deleted_files,
    }


# ------------------------------------------------------------------
# GET /admin/models — List all registered model versions
# ------------------------------------------------------------------
@router.get("/admin/models")
def list_model_versions():
    """
    Returns the full model registry so the frontend can display it
    without needing direct filesystem access.
    """
    return _load_registry()
