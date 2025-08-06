# tests/domain_specific/refinement_tests.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import UUID

from backend.interaction-service.refinement.refinement_engine import RefinementEngine
from backend.interaction-service.refinement.feedback_analyzer import FeedbackAnalyzer
from shared.exceptions import BadRequestException, InternalServerError, ServiceUnavailableException, LLMGenerationError
from shared.models import QCProblem, QCReport

# Mock des services externes
@pytest.fixture
def mock_generation_service_client():
    """Mock du client HTTP pour le Generation Service."""
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_instance = MockAsyncClient.return_value
        # Configurez les méthodes de mock_instance si nécessaire
        yield mock_instance

@pytest.fixture
def mock_kb_service_client():
    """Mock du client HTTP pour le KB Service."""
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_instance = MockAsyncClient.return_value
        # Configurez les méthodes de mock_instance si nécessaire
        yield mock_instance

@pytest.fixture
def refinement_engine(mock_generation_service_client, mock_kb_service_client):
    """Fixture pour le moteur de raffinement avec des clients mockés."""
    # Le moteur de raffinement s'attend à ce que les clients soient accessibles via httpx.AsyncClient
    # et non directement passés dans le constructeur.
    # Nous allons mocker les URLs pour qu'elles soient interceptées par httpx.AsyncClient.
    with patch('backend.interaction-service.refinement.refinement_engine.settings') as mock_settings:
        mock_settings.GENERATION_SERVICE_URL = "http://mock-gen-service"
        mock_settings.KB_SERVICE_URL = "http://mock-kb-service"
        yield RefinementEngine(
            generation_service_url=mock_settings.GENERATION_SERVICE_URL,
            kb_service_url=mock_settings.KB_SERVICE_URL
        )

@pytest.fixture
def feedback_analyzer():
    """Fixture pour l'analyseur de feedback."""
    return FeedbackAnalyzer()

@pytest.mark.asyncio
async def test_refine_content_math_error_from_qc(refinement_engine, mock_generation_service_client, feedback_analyzer):
    """
    Teste le raffinement d'un contenu avec une erreur mathématique détectée par le QC.
    """
    original_content = "$1+1=3$"
    qc_report_data = QCReport(
        overall_score=20.0,
        status="failed",
        problems=[
            QCProblem(type="math_error", severity="critical", description="L'égalité $1+1=3$ est fausse.")
        ]
    ).model_dump()

    feedback = feedback_analyzer.analyze_feedback({'source': 'qc', 'qc_report': qc_report_data})

    block_type = "text"
    level = "L1"
    style = "Hybride"
    context = {}

    # Configurer le mock du Generation Service pour retourner le contenu raffiné
    mock_generation_service_client.post.return_value = AsyncMock(
        json=AsyncMock(return_value={"content_latex": "$1+1=2$"})
    )
    mock_generation_service_client.post.return_value.raise_for_status = AsyncMock() # Mock raise_for_status

    refined_content = await refinement_engine.refine_content(
        original_content, feedback, block_type, level, style, context
    )

    assert refined_content == "$1+1=2$"
    # Vérifier que le Generation Service a été appelé avec le bon prompt
    mock_generation_service_client.post.assert_called_once()
    call_args = mock_generation_service_client.post.call_args[1]['json']
    assert "content_latex" in call_args
    assert "feedback" in call_args
    assert call_args["feedback"]["type"] == "math_error"
    assert "Correction mathématique requise" in refinement_engine._formulate_llm_instructions(feedback, block_type, level, style, {})


@pytest.mark.asyncio
async def test_refine_content_clarity_issue_from_user(refinement_engine, mock_generation_service_client, feedback_analyzer):
    """
    Teste le raffinement d'un contenu avec un problème de clarté signalé par l'utilisateur.
    """
    original_content = "La dérivée, c'est un truc un peu bizarre."
    user_feedback_data = {
        'source': 'user',
        'details': 'Ceci n\'est pas clair, veuillez reformuler de manière plus intuitive.',
        'location': {'line': 1, 'char_start': 0, 'char_end': 30}
    }
    feedback = feedback_analyzer.analyze_feedback(user_feedback_data)

    block_type = "intuition"
    level = "L1"
    style = "Feynman"
    context = {"concept_id": UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")} # Mock concept ID

    # Mock KB Service pour retourner des analogies pertinentes
    mock_generation_service_client.get.side_effect = [
        AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value={"intuitive_definitions": [], "pitfalls": [], "analogies": [{"description_latex": "L'analogie de la vitesse."}]}))),
        AsyncMock(return_value=AsyncMock(json=AsyncMock(return_value={"content_latex": "La dérivée mesure la vitesse à laquelle une fonction change, comme la vitesse d'une voiture."})))
    ]
    mock_generation_service_client.get.return_value.raise_for_status = AsyncMock()


    # Configurer le mock du Generation Service pour retourner le contenu raffiné
    mock_generation_service_client.post.return_value = AsyncMock(
        json=AsyncMock(return_value={"content_latex": "La dérivée mesure la vitesse à laquelle une fonction change, comme la vitesse d'une voiture."})
    )
    mock_generation_service_client.post.return_value.raise_for_status = AsyncMock()

    refined_content = await refinement_engine.refine_content(
        original_content, feedback, block_type, level, style, context
    )

    assert "vitesse d'une voiture" in refined_content
    assert "clarté requise" in refinement_engine._formulate_llm_instructions(feedback, block_type, level, style, {})


@pytest.mark.asyncio
async def test_refine_content_llm_failure(refinement_engine, mock_generation_service_client, feedback_analyzer):
    """
    Teste la gestion d'un échec de l'appel au LLM pendant le raffinement.
    """
    original_content = "Contenu original."
    feedback = feedback_analyzer.analyze_feedback({'source': 'user', 'details': 'Corrigez ceci.'})
    block_type = "text"
    level = "L1"
    style = "Hybride"
    context = {}

    # Configurer le mock du Generation Service pour lever une erreur HTTP
    mock_generation_service_client.post.side_effect = httpx.HTTPStatusError(
        "Service Error", request=httpx.Request("POST", "http://mock-gen-service"), response=httpx.Response(500)
    )

    with pytest.raises(LLMGenerationError) as excinfo:
        await refinement_engine.refine_content(
            original_content, feedback, block_type, level, style, context
        )
    assert "Échec du raffinement par le LLM" in str(excinfo.value)
    mock_generation_service_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_formulate_llm_instructions_style_mismatch(refinement_engine, feedback_analyzer):
    """
    Teste la formulation des instructions pour un problème de style.
    """
    original_content = "Ceci est une preuve très intuitive."
    user_feedback_data = {
        'source': 'user',
        'details': 'Le style est trop informel pour du Bourbaki.',
        'location': None
    }
    feedback = feedback_analyzer.analyze_feedback(user_feedback_data)

    block_type = "proof_skeleton"
    level = "M1"
    style = "Bourbaki"
    context = {}

    instructions = refinement_engine._formulate_llm_instructions(feedback, block_type, level, style, {})
    assert "Ajustement stylistique nécessaire" in instructions
    assert "pleinement conforme au style Bourbaki" in instructions

