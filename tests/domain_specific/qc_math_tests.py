# tests/domain_specific/qc_math_tests.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import UUID

from backend.qc-service.qc.math_verifier import MathVerifier
from backend.qc-service.qc.external_tools.sympy_client import SymPyClient
from backend.qc-service.qc.external_tools.z3_client import Z3Client
from shared.exceptions import BadRequestException, ExternalToolError, InternalServerError
from shared.models import QCProblem, QCReport

# Mock des clients externes pour isoler les tests
@pytest.fixture
def mock_sympy_client():
    with patch('backend.qc-service.qc.math_verifier.sympy_client', spec=SymPyClient) as mock_client:
        yield mock_client

@pytest.fixture
def mock_z3_client():
    with patch('backend.qc-service.qc.math_verifier.z3_client', spec=Z3Client) as mock_client:
        yield mock_client

@pytest.fixture
def math_verifier(mock_sympy_client, mock_z3_client):
    # Initialiser MathVerifier avec des URLs et chemins mockés
    return MathVerifier(kb_service_url="http://mock-kb-service:80", external_tools_path="/mock/tools")

@pytest.mark.asyncio
async def test_verify_mathematical_statement_true_equality(math_verifier, mock_sympy_client):
    """
    Teste la vérification d'une égalité mathématique simple et vraie.
    """
    statement = "$1+1=2$"
    
    # Configurer le mock de SymPy pour simuler une égalité vraie
    mock_sympy_client.parse_latex_expression.side_effect = [
        AsyncMock(return_value=sympy.sympify("1+1")), # Pour le LHS
        AsyncMock(return_value=sympy.sympify("2"))    # Pour le RHS
    ]
    mock_sympy_client.check_equality.return_value = True

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "verified"
    assert result["confidence"] == 1.0
    assert not result["problems"]
    mock_sympy_client.check_equality.assert_called_once()

@pytest.mark.asyncio
async def test_verify_mathematical_statement_false_equality(math_verifier, mock_sympy_client):
    """
    Teste la vérification d'une égalité mathématique simple et fausse.
    """
    statement = "$1+1=3$"
    
    mock_sympy_client.parse_latex_expression.side_effect = [
        AsyncMock(return_value=sympy.sympify("1+1")),
        AsyncMock(return_value=sympy.sympify("3"))
    ]
    mock_sympy_client.check_equality.return_value = False

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "refuted"
    assert result["confidence"] == 0.1 # Confiance réduite car l'égalité est fausse
    assert len(result["problems"]) == 1
    assert result["problems"][0]["type"] == "math_error"
    assert "fausse" in result["problems"][0]["description"]
    mock_sympy_client.check_equality.assert_called_once()

@pytest.mark.asyncio
async def test_verify_mathematical_statement_sympy_parse_error(math_verifier, mock_sympy_client):
    """
    Teste la gestion d'une erreur de parsing LaTeX par SymPy.
    """
    statement = "$\\frac{1}{0}$" # Division par zéro ou LaTeX mal formé
    
    mock_sympy_client.parse_latex_expression.side_effect = BadRequestException("Erreur de parsing LaTeX")

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "error"
    assert result["confidence"] == 0.0
    assert len(result["problems"]) == 1
    assert result["problems"][0]["type"] == "formatting_error"
    assert "parsing LaTeX" in result["problems"][0]["description"]

@pytest.mark.asyncio
async def test_verify_mathematical_statement_z3_quantifier(math_verifier, mock_z3_client):
    """
    Teste la vérification d'une assertion avec quantificateurs utilisant Z3.
    """
    statement = "$\\forall x \\in \\mathbb{R}, x^2 \\ge 0$"
    
    # Simuler une réponse de Z3 pour une formule valide
    mock_z3_client.check_validity.return_value = {"status": "valid"}

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "verified"
    assert result["confidence"] == 1.0 # Si Z3 valide, confiance élevée
    assert not result["problems"]
    mock_z3_client.check_validity.assert_called_once()

@pytest.mark.asyncio
async def test_verify_mathematical_statement_z3_refuted(math_verifier, mock_z3_client):
    """
    Teste la vérification d'une assertion avec quantificateurs réfutée par Z3.
    """
    statement = "$\\forall x \\in \\mathbb{R}, x^2 < 0$"
    
    # Simuler une réponse de Z3 pour une formule invalide (réfutée)
    mock_z3_client.check_validity.return_value = {"status": "invalid", "counter_example": "(model (define-fun x () Real (- 1.0)))"}

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "refuted"
    assert result["confidence"] == 0.0
    assert len(result["problems"]) == 1
    assert result["problems"][0]["type"] == "math_error"
    assert "réfutée par Z3" in result["problems"][0]["description"]
    mock_z3_client.check_validity.assert_called_once()

@pytest.mark.asyncio
async def test_verify_mathematical_statement_z3_error(math_verifier, mock_z3_client):
    """
    Teste la gestion des erreurs lors de l'appel à Z3.
    """
    statement = "$\\forall x, \\text{invalid_logic}$"
    
    mock_z3_client.check_validity.side_effect = ExternalToolError(tool_name="Z3", detail="Erreur de syntaxe SMT-LIB")

    result = await math_verifier.verify_mathematical_statement(statement)

    assert result["status"] == "error"
    assert result["confidence"] == 0.0
    assert len(result["problems"]) == 1
    assert result["problems"][0]["type"] == "external_tool_error"
    assert "Erreur Z3" in result["problems"][0]["description"]

@pytest.mark.asyncio
async def test_analyze_proof_step_basic(math_verifier, mock_sympy_client):
    """
    Teste l'analyse d'une étape de preuve simple.
    """
    step_latex = "$1+1=2$"
    previous_context = "Précédemment, nous avons défini l'addition."
    theorem_refs = []
    
    mock_sympy_client.check_equality.return_value = True # Simuler la vérification de l'assertion dans l'étape

    result = await math_verifier.analyze_proof_step(step_latex, previous_context, theorem_refs)
    
    assert result["status"] == "valid"
    assert result["confidence"] > 0.5 # Confiance plus élevée si l'assertion est vérifiée
    assert not result["problems"]

@pytest.mark.asyncio
async def test_analyze_proof_step_invalid_assertion(math_verifier, mock_sympy_client):
    """
    Teste l'analyse d'une étape de preuve avec une assertion invalide.
    """
    step_latex = "$1+1=5$"
    previous_context = ""
    theorem_refs = []
    
    mock_sympy_client.check_equality.return_value = False

    result = await math_verifier.analyze_proof_step(step_latex, previous_context, theorem_refs)
    
    assert result["status"] == "invalid"
    assert result["confidence"] == 0.0
    assert len(result["problems"]) == 1
    assert result["problems"][0]["type"] == "math_error"
    assert "fausse" in result["problems"][0]["description"]

