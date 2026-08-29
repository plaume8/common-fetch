
#### Data Server 

The data server consists of two layers:
- **Blue layer:** Contains all [FastAPI](https://fastapi.tiangolo.com/#installation) endpoints and server configuration. The `main.py` file holds the full FastAPI setup.
- **Purple layer:** Contains the dataset-specific retriever logic and data handling.

##### Architecture Overview

The overall idea is quite simple:

1. A client sends a request to the `/data` endpoint including a defined request schema.
2. The `data_server` receives the request object and calls the matching retriever function for the specified dataset.
3. The retriever processes the request, fetching, parsing, and cleaning the data, then stores the prepared files in an `outbox` directory and returns their filenames.
4. The FastAPI server returns those filenames to the client.
5. The client downloads each file via the `/data/download/{data_file}` endpoint.

> **Tip:** See the pip package implementation to understand how the data retrieval works on the client side — it uses straightforward Python and is simpler than it looks.

**Additional endpoints:**
- `/dataset_ids`: Returns an array of all available dataset IDs.
- `/schema/{dataset_id}`: Returns the schema for a given dataset, including basic info and a request object boilerplate.

##### Adding a New Dataset

To add a new dataset and to make available via the `data_server` for the API and pip package end users please follow the following steps:

1. Choose a unique `dataset_id` for the new dataset (e.g. `opsd`).
2. Create a folder `/raw_data/<dataset_id>/` and add all raw data files to it.
3. Create a schema file `/schemas/<dataset_id>.yaml` with the following fields:
   - `dataset_id`: The chosen dataset ID.
   - `description`: A short description of the dataset.
   - `request_logic`: A short explanation of the request parameters.
   - `request`: All parameters of the request object (boilerplate).
4. Create a retriever at `/retrievers/<dataset_id>_retriever.py` implementing the following function signature:
    ```python
       def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
           pass
    ```
   > **Tip:** See `dummy_dataset_retriever.py` for a minimal working example.
5. That's it ... the server will now recognise the new dataset, its request schema, and know which retriever to call.

##### Testing Server Locally

To test the implementation locally, you can simply run a local FastAPI instance by executing:
```bash
cd data-server/src/cf_server
export PYTHONPATH="$PWD"
fastapi dev main.py
```
This starts the server at [http://127.0.0.1:8000](http://127.0.0.1:8000). 
Use Postman or any HTTP client to test the endpoints.
See /tests/dummy_testing.ipynb for a simple dummy JupyterNotebook.

##### Deploying the Updated Server

The `data_server` is deployed on the [Friday Server](https://gitlab.lrz.de/EMT/fridaysetup), 
using the k8s deployment strategy described [here](https://gitlab.lrz.de/EMT/fridaysetup/-/tree/main/ci-cd?ref_type=heads), 
with a Jenkins pipeline set up as outlined in the [quick-start guide](https://gitlab.lrz.de/EMT/fridaysetup/-/blob/main/ci-cd/QUICK-START.md?ref_type=heads).
To deploy, simply commit to the `main` branch, the Jenkins pipeline triggers automatically. 
If it does not, trigger it manually via the Friday Jenkins UI.

**Attention:** Raw data is not pushed to the repository due to size constraints. 
The Friday server uses a Longhorn persistent storage volume.
To upload a new `/raw_data/<dataset_id>/` folder, run:
1. Copy raw data to Friday: `scp -r /path/to/raw_data/<dataset_id> emt@10.152.14.66:/home/emt/EMT-Data-Loader`
2. Get the pod name of the emtl-data-loader-server: `kubectl get pods -n production`
3. Copy uploaded data to the correct pod: `kubectl cp /home/emt/EMT-Data-Loader/<dataset_id> production/<emtl-data-loader-server-pod-name>:/app/src/emtl_server/retrievers/raw_data`
4. Check if it was successfully copied: `kubectl exec -it <emtl-data-loader-server-pod-name> -n production -- ls -la /app/src/emtl_server/retrievers/raw_data`

---

## Miscellaneous

### Manage API Keys

The pod includes a Python script called `api_keys_management` for managing API keys. 
To use it, simply run the following commands:

> Attention, before any command: get the pod name of the emtl-data-loader-server first: `kubectl get pods -n production`)

> Hint: for a default user API key checkout Friday server: `/home/emt/EMT-Data-Loader/default-user-CFL-API-KEY.txt`)

Create a new API key:
```bash
kubectl exec -it -n production <emtl-data-loader-server-pod-name> -- \
python /app/src/emtl_server/auth/api_keys_management.py generate_key \
--name "Alice" --mail "alice@example.com" --others "team-a"
```

Deactivate API key:
```bash
kubectl exec -it -n production <emtl-data-loader-server-pod-name> -- \
python /app/src/emtl_server/auth/api_keys_management.py deactivate_key \
--api_key "emt-dataloader-abc123..."
```

Reactivate API key:
```bash
kubectl exec -it -n production <emtl-data-loader-server-pod-name> -- \
python /app/src/emtl_server/auth/api_keys_management.py reactivate_key \
--api_key "emt-dataloader-abc123..."
```

### Get Latest Logs of Data Loader Server Pod 
1. Get the pod name of the emtl-data-loader-server: `kubectl get pods -n production`
2. Get logs: `kubectl logs -n production <emtl-data-loader-server-pod-name>`

### Execute Local Server Tests

Simple system tests are implemented in `/tests/test_system.py`. 
These tests call and verify all low-level API functions from the pip package using dummy data. 
While they do not test the client or server side in depth, they verify base functionality through black-box testing.

To run the tests:
1. Make sure all dependencies are installed (`pip install -r requirements.txt`)
2. Navigate to `/data-loader` or `tests` directory
3. Run: `pytest`

---

## Authors

[Linus Sander](mailto:linus.sander@icloud.com)  