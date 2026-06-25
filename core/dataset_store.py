import os
import uuid
import pickle
import pandas as pd

class DatasetStore:
    def __init__(self, base_path='static/uploads'):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _path(self, dataset_id):
        return os.path.join(self.base_path, f"{dataset_id}.pkl")

    def save(self, df, name, dataset_id=None):
        if dataset_id is None:
            dataset_id = str(uuid.uuid4())
        path = self._path(dataset_id)
        with open(path, 'wb') as f:
            pickle.dump({'df': df, 'name': name}, f)
        return dataset_id

    def load(self, dataset_id):
        path = self._path(dataset_id)
        if not os.path.exists(path):
            return None, None
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data['df'], data['name']

    def delete(self, dataset_id):
        path = self._path(dataset_id)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, dataset_id):
        return os.path.exists(self._path(dataset_id))
