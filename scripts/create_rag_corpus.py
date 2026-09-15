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

"""Create a serverless Vertex AI RAG Corpus for ChefGenie."""

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-01-1294b1272871"
LOCATION = "us-central1"  # Serverless RAG Engine is us-central1
GCS_PATH = "gs://chef-genie-media-qwiklabs-gcp-01-1294b1272871/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, herbs, culinary uses, and recipes described in this text. "
    "Ignore and omit all boilerplate and Project Gutenberg licensing metadata. "
    "Output clean, self-contained prose."
)


def create_serverless_rag_corpus():
    """Build serverless RAG corpus and import Culpeper's Herbal text file."""
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Set RAG engine config to serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    # 2. Create the corpus with text-embedding-005
    corpus = rag.create_corpus(
        display_name="chef-genie-herbal-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"CREATED_CORPUS_NAME: {corpus.name}")

    # 3. Import, parse, chunk, and embed
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT,
        ),
    )
    print(f"IMPORTED_FILES_COUNT: {resp.imported_rag_files_count}")
    return corpus.name


if __name__ == "__main__":
    create_serverless_rag_corpus()
