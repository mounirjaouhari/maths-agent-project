# backend/api-gateway/api/v1/endpoints/projects.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List, Optional
import httpx
import logging

from shared.config import get_settings
from shared.models import (
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectDetailResponse,
    WorkflowSignal, QCReport, ContentBlockResponse
)
from shared.exceptions import (
    NotFoundException, BadRequestException, ForbiddenException, ServiceUnavailableException,
    DocumentExportError
)
from ..auth.dependencies import get_current_user_id # Pour obtenir l'ID de l'utilisateur authentifié

router = APIRouter()
logger = logging.getLogger(__name__)

settings = get_settings()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Créer un nouveau projet de rédaction mathématique")
async def create_project(
    project_data: ProjectCreate,
    current_user_id: str = Depends(get_current_user_id) # Dépendance pour l'authentification
):
    """
    Crée un nouveau projet de rédaction mathématique pour l'utilisateur authentifié.
    """
    try:
        # Ajouter l'ID de l'utilisateur au projet
        project_data_with_user = project_data.model_dump()
        project_data_with_user["user_id"] = current_user_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects",
                json=project_data_with_user
            )
            response.raise_for_status()
            created_project = response.json()
            return ProjectResponse(**created_project)
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur lors de l'appel au service de persistance pour la création de projet: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la création du projet.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création du projet: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.get("/", response_model=List[ProjectResponse], summary="Obtenir la liste des projets de l'utilisateur")
async def list_projects(
    current_user_id: str = Depends(get_current_user_id),
    status_filter: Optional[str] = None # Renommé pour éviter le conflit avec 'status'
):
    """
    Retourne la liste de tous les projets appartenant à l'utilisateur authentifié,
    avec une option de filtrage par statut.
    """
    try:
        params = {"user_id": current_user_id}
        if status_filter:
            params["status"] = status_filter

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects",
                params=params
            )
            response.raise_for_status()
            projects_data = response.json()
            return [ProjectResponse(**p) for p in projects_data]
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur lors de l'appel au service de persistance pour lister les projets: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la récupération des projets.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la liste des projets: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.get("/{project_id}", response_model=ProjectDetailResponse, summary="Obtenir les détails d'un projet spécifique")
async def get_project(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retourne les détails d'un projet spécifique, y compris sa structure de document
    et les informations sur les blocs de contenu.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Récupérer le projet
            project_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}"
            )
            project_response.raise_for_status()
            project_data = project_response.json()

            # Vérifier que l'utilisateur est bien le propriétaire du projet
            if project_data.get("user_id") != current_user_id:
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à accéder à ce projet.")
            
            # Récupérer la version actuelle du document et sa structure
            document_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/documents/project/{project_id}" # Endpoint à implémenter dans persistence-service
            )
            document_response.raise_for_status()
            document_data = document_response.json()
            current_version_id = document_data.get("current_version_id")

            document_version_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/document-versions/{current_version_id}"
            )
            document_version_response.raise_for_status()
            document_version_data = document_version_response.json()
            
            # Récupérer tous les blocs de contenu pour cette version
            content_blocks_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/content-blocks/version/{current_version_id}" # Endpoint à implémenter
            )
            content_blocks_response.raise_for_status()
            content_blocks_data = content_blocks_response.json()

            # Construire la réponse détaillée
            project_detail = ProjectDetailResponse(
                **project_data,
                document_structure=document_version_data.get("content_structure", {}),
                content_blocks=[ContentBlockResponse(**cb) for cb in content_blocks_data]
            )
            return project_detail
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour récupérer le projet: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la récupération du projet.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except ForbiddenException: # Re-lève l'exception Forbidden si déjà levée
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération du projet: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.put("/{project_id}", response_model=ProjectResponse, summary="Mettre à jour un projet existant")
async def update_project(
    project_id: str,
    project_update_data: ProjectUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Met à jour les informations d'un projet existant.
    """
    try:
        # Récupérer le projet pour vérifier la propriété
        async with httpx.AsyncClient() as client:
            project_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}"
            )
            project_response.raise_for_status()
            existing_project = project_response.json()

            if existing_project.get("user_id") != current_user_id:
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à modifier ce projet.")

            # Appeler le service de persistance pour mettre à jour le projet
            response = await client.put(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}",
                json=project_update_data.model_dump(exclude_unset=True) # N'envoie que les champs qui sont définis
            )
            response.raise_for_status()
            updated_project = response.json()
            return ProjectResponse(**updated_project)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour la mise à jour de projet: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la mise à jour du projet.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la mise à jour du projet: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un projet")
async def delete_project(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Supprime un projet existant.
    """
    try:
        # Récupérer le projet pour vérifier la propriété
        async with httpx.AsyncClient() as client:
            project_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}"
            )
            project_response.raise_for_status()
            existing_project = project_response.json()

            if existing_project.get("user_id") != current_user_id:
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à supprimer ce projet.")

            # Appeler le service de persistance pour supprimer le projet
            response = await client.delete(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}"
            )
            response.raise_for_status()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour la suppression de projet: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la suppression du projet.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la suppression du projet: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.post("/{project_id}/signal", response_model=ProjectResponse, summary="Envoyer un signal utilisateur au moteur de workflow")
async def send_workflow_signal(
    project_id: str,
    signal: WorkflowSignal,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Envoie un signal (ex: validation, demande de raffinement) au moteur de workflow
    pour un projet spécifique.
    """
    try:
        # Récupérer le projet pour vérifier la propriété
        async with httpx.AsyncClient() as client:
            project_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{project_id}"
            )
            project_response.raise_for_status()
            existing_project = project_response.json()

            if existing_project.get("user_id") != current_user_id:
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à envoyer un signal pour ce projet.")

            # Envoyer le signal au service de workflow
            response = await client.post(
                f"{settings.WORKFLOW_SERVICE_URL}/internal/projects/{project_id}/signal", # Endpoint à implémenter dans workflow-service
                json=signal.model_dump()
            )
            response.raise_for_status()
            updated_project_data = response.json()
            return ProjectResponse(**updated_project_data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Projet avec l'ID {project_id} non trouvé.")
        logger.error(f"Erreur lors de l'appel au service de workflow pour le signal: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de workflow lors du traitement du signal.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de workflow: {e}")
        raise ServiceUnavailableException(detail="Le service de workflow n'est pas disponible.")
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'envoi du signal: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.get("/content-blocks/{block_id}/qc-report", response_model=QCReport, summary="Obtenir le rapport QC détaillé pour un bloc de contenu")
async def get_qc_report_for_block(
    block_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Récupère le rapport de contrôle qualité détaillé pour un bloc de contenu spécifique.
    """
    try:
        # Récupérer le bloc de contenu pour vérifier la propriété via le projet parent
        async with httpx.AsyncClient() as client:
            block_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/content-blocks/{block_id}"
            )
            block_response.raise_for_status()
            block_data = block_response.json()

            # Récupérer la version du document
            version_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/document-versions/{block_data['version_id']}"
            )
            version_response.raise_for_status()
            version_data = version_response.json()

            # Récupérer le projet parent de la version du document
            project_response = await client.get(
                f"{settings.PERSISTENCE_SERVICE_URL}/internal/projects/{version_data['document_id']}" # document_id est en fait le project_id dans notre modèle simplifié
            )
            project_response.raise_for_status()
            project_data = project_response.json()

            if project_data.get("user_id") != current_user_id:
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à accéder à ce rapport QC.")

            # Le rapport QC est stocké directement dans le bloc de contenu
            qc_report = block_data.get("qc_report")
            if not qc_report:
                raise NotFoundException(detail=f"Rapport QC non disponible pour le bloc {block_id}.")
            
            return QCReport(**qc_report)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Bloc de contenu avec l'ID {block_id} non trouvé.")
        logger.error(f"Erreur lors de l'appel au service de persistance pour le rapport QC: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service de persistance lors de la récupération du rapport QC.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service de persistance: {e}")
        raise ServiceUnavailableException(detail="Le service de persistance n'est pas disponible.")
    except ForbiddenException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération du rapport QC: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

@router.get("/exports/{export_id}/download", summary="Télécharger un document exporté")
async def download_exported_document(
    export_id: str, # Dans notre modèle actuel, export_id pourrait être le document_id ou une tâche d'exportation
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Permet de télécharger un document qui a été exporté.
    """
    try:
        # Dans un système réel, vous vérifieriez ici la propriété de l'exportation
        # et récupéreriez l'URL du fichier exporté depuis le service de persistance
        # ou le service d'assemblage/exportation.
        # Pour cet exemple, nous allons simuler un chemin de fichier.

        # Exemple: Récupérer le statut de l'exportation pour obtenir l'URL du fichier
        async with httpx.AsyncClient() as client:
            export_status_response = await client.get(
                f"{settings.ASSEMBLY_EXPORT_SERVICE_URL}/internal/exports/{export_id}/status"
            )
            export_status_response.raise_for_status()
            export_status_data = export_status_response.json()

            if export_status_data.get("status") != "completed":
                raise BadRequestException(detail="L'exportation n'est pas encore terminée ou a échoué.")
            
            # Supposons que l'URL du fichier est dans exported_files[0].url
            download_url = None
            if export_status_data.get("exported_files"):
                for file_info in export_status_data["exported_files"]:
                    if file_info.get("url"):
                        download_url = file_info["url"]
                        break
            
            if not download_url:
                raise NotFoundException(detail="URL de téléchargement non disponible pour cette exportation.")

            # Dans un cas réel, vous redirigeriez vers cette URL ou streamerait le fichier.
            # Pour l'instant, nous retournons juste l'URL.
            return {"download_url": download_url}

    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundException(detail=f"Exportation avec l'ID {export_id} non trouvée.")
        logger.error(f"Erreur lors de l'appel au service d'exportation pour le statut: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail="Erreur du service d'exportation lors de la récupération du statut.")
    except httpx.RequestError as e:
        logger.error(f"Erreur réseau lors de l'appel au service d'exportation: {e}")
        raise ServiceUnavailableException(detail="Le service d'assemblage/exportation n'est pas disponible.")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du téléchargement du document exporté: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur.")

