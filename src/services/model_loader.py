import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None


def get_model():
    """
    Load the embedding model only when it is needed.
    Reuse the loaded model for subsequent requests.
    """

    global _model

    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)

    return _model