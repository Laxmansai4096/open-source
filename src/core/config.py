"""Enterprise Core Configuration Module.

Supports Dual-Mode execution:
- 'azure': Live Azure OpenAI, Azure AI Search, Azure Document Intelligence.
- 'local': In-memory zero-cost mock engines for continuous development and CI/CD.
"""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Global runtime mode
    run_mode: Literal["local", "azure"] = Field(
        default="local",
        description="Execution mode: 'azure' for cloud, 'local' for offline fallback"
    )

    # Azure OpenAI & Gateway
    azure_openai_endpoint: str = Field(
        default="https://mock.openai.azure.com/",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_api_key: str = Field(
        default="mock-key",
        description="Azure OpenAI API Key"
    )
    azure_openai_api_version: str = Field(
        default="2024-08-01-preview",
        description="API version"
    )
    azure_openai_chat_deployment: str = Field(
        default="gpt-4o",
        description="Deployment name for reasoning model"
    )
    azure_openai_embedding_deployment: str = Field(
        default="text-embedding-3-large",
        description="Deployment name for embeddings"
    )

    # Open-Source Fallback (vLLM / Ollama)
    fallback_opensource_endpoint: str = Field(
        default="http://localhost:11434/v1",
        description="Fallback endpoint for local/open-source LLM"
    )
    fallback_opensource_model: str = Field(
        default="llama3.3:70b",
        description="Fallback model name"
    )

    # Azure AI Search
    azure_search_endpoint: str = Field(
        default="https://mock.search.windows.net",
        description="Azure AI Search service endpoint"
    )
    azure_search_api_key: str = Field(
        default="mock-search-key",
        description="Azure AI Search API key"
    )
    azure_search_index_name: str = Field(
        default="enterprise-contract-vault",
        description="Target index name"
    )

    # Azure Document Intelligence
    azure_doc_intelligence_endpoint: str = Field(
        default="https://mock.cognitiveservices.azure.com/",
        description="Document Intelligence endpoint"
    )
    azure_doc_intelligence_key: str = Field(
        default="mock-doc-key",
        description="Document Intelligence API key"
    )

    # Azure Content Safety
    azure_content_safety_endpoint: str = Field(
        default="https://mock-safety.cognitiveservices.azure.com/",
        description="Azure AI Content Safety endpoint"
    )
    azure_content_safety_key: str = Field(
        default="mock-safety-key",
        description="Azure AI Content Safety key"
    )

    # Enterprise ERP Client API
    erp_api_base_url: str = Field(
        default="http://localhost:8000/api/v1/erp",
        description="Client ERP/Procurement API base URL"
    )
    erp_api_bearer_token: str = Field(
        default="mock-erp-token",
        description="Bearer token for Client ERP API"
    )

    # Concurrency & Cache
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    rate_limit_rpm: int = Field(
        default=100,
        description="Rate limit in requests per minute"
    )


# Singleton instance
settings = Settings()
