"""PII identification engine backed by Microsoft Presidio and spaCy NLP models.

Provides the PIIIdentifier class that wraps Presidio's AnalyzerEngine with
multi-language spaCy models (Portuguese and English by default). The analyzer
is lazily initialized on first use to avoid spaCy model caching issues when
multiple instances are created in the same process.
"""

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider


LANGUAGES = ["pt", "en"]

MODEL_NAMES = {
    "pt": "pt_core_news_sm",
    "en": "en_core_web_sm",
}


class PIIIdentifier:
    """Identifies PII entity types in text using Presidio AnalyzerEngine.

    Wraps Microsoft Presidio with configurable spaCy NLP models. Iterates
    through multiple language analyzers and returns the highest-confidence
    result. The architecture is engine-agnostic — the detection library
    can be swapped by modifying only this module.
    """

    def __init__(self, languages=None):
        """Initialize PIIIdentifier with the given languages.

        Args:
            languages: List of language codes to use for analysis.
                Defaults to LANGUAGES (["pt", "en"]).
        """
        self.languages = languages or LANGUAGES
        self._analyzer = None

    def _build_analyzer(self):
        """Build a Presidio AnalyzerEngine with spaCy NLP models for all configured languages.

        Returns:
            AnalyzerEngine configured with the NLP engine and supported languages.
        """
        models = []
        for lang in self.languages:
            model_name = MODEL_NAMES[lang]
            models.append((lang, model_name))
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": lang, "model_name": model} for lang, model in models],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=self.languages)

    def _ensure_analyzer(self):
        """Return the cached AnalyzerEngine, building it on first call.

        Lazy initialization avoids spaCy model caching issues when
        multiple PIIIdentifier instances are created in the same process.

        Returns:
            The Presidio AnalyzerEngine instance.
        """
        if self._analyzer is None:
            self._analyzer = self._build_analyzer()
        return self._analyzer

    def identify(self, text):
        """Identify the highest-confidence PII entity type in the given text.

        Iterates through all configured language analyzers, collects every
        detected entity, and returns the one with the highest confidence score.

        Args:
            text: The text string to analyze. Non-string or empty values
                return None.

        Returns:
            A tuple of (entity_type, confidence_score) if PII is found,
            e.g. ("EMAIL_ADDRESS", 0.85). Returns None if no PII is detected.
        """
        if not text or not isinstance(text, str):
            return None
        text = str(text).strip()
        if not text:
            return None
        best_entity = None
        best_score = 0.0
        for lang in self.languages:
            results = self._ensure_analyzer().analyze(text=text, language=lang)
            for result in results:
                if result.score > best_score:
                    best_score = result.score
                    best_entity = result.entity_type
        if best_entity:
            return (best_entity, best_score)
        return None
