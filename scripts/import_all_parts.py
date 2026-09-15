# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sequentially import all parts of Culpeper Herbal into RAG corpus."""

import time
import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-01-1294b1272871"
LOCATION = "us-central1"
CORPUS_NAME = "projects/178057287160/locations/us-central1/ragCorpora/1849668828988964864"

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Get existing imported file names
existing = {f.display_name for f in rag.list_files(corpus_name=CORPUS_NAME)}
print("Already imported files:", existing)

parts = ["part_aa", "part_ab", "part_ac", "part_ad", "part_ae", "part_af", "part_ag", "part_ah", "part_ai", "part_aj", "part_ak", "part_al", "part_am", "part_an", "part_ao"]

for part in parts:
    if part in existing:
        print(f"Skipping {part} (already imported)")
        continue
    gcs_uri = f"gs://chef-genie-media-qwiklabs-gcp-01-1294b1272871/rag/parts/{part}"
    print(f"Importing {part}...")
    try:
        resp = rag.import_files(
            corpus_name=CORPUS_NAME,
            paths=[gcs_uri],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
            ),
            max_embedding_requests_per_min=100
        )
        print(f"Imported {part}: {resp}")
    except Exception as e:
        print(f"Error importing {part}: {e}")
    time.sleep(2)

print("Finished importing all parts!")
