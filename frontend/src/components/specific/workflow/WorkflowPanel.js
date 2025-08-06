// frontend/src/components/specific/workflow/WorkflowPanel.js

import React from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaHourglassHalf, FaTimesCircle, FaEdit, FaDownload } from 'react-icons/fa';
import DocumentTree from '../visualizations/DocumentTree';
import QcReportGraph from '../visualizations/QcReportGraph';

// Composant pour le panneau de workflow
const WorkflowPanel = ({ project, contentBlocks, onSendSignal, onDownloadExport, currentBlock, onSelectNode }) => {
  if (!project) {
    return (
      <div className="p-4 bg-white rounded-lg shadow-sm text-gray-500 text-center">
        Chargement du projet...
      </div>
    );
  }

  // Déterminer le statut global du projet pour l'affichage
  let projectStatusText = '';
  let projectStatusColor = 'text-gray-600';
  let projectStatusIcon = <FaHourglassHalf className="text-gray-500" />;

  switch (project.status) {
    case 'draft':
      projectStatusText = 'Brouillon';
      projectStatusIcon = <FaEdit className="text-blue-500" />;
      break;
    case 'in_progress':
      projectStatusText = `En cours - ${project.current_step || 'Étape non spécifiée'}`;
      projectStatusIcon = <FaHourglassHalf className="text-blue-500 animate-pulse" />;
      break;
    case 'completed':
      projectStatusText = 'Terminé';
      projectStatusIcon = <FaCheckCircle className="text-green-500" />;
      projectStatusColor = 'text-green-600';
      break;
    case 'export_pending':
      projectStatusText = 'Exportation en cours...';
      projectStatusIcon = <FaDownload className="text-purple-500 animate-pulse" />;
      projectStatusColor = 'text-purple-600';
      break;
    case 'completed_exported':
      projectStatusText = 'Terminé et Exporté';
      projectStatusIcon = <FaCheckCircle className="text-green-500" />;
      projectStatusColor = 'text-green-600';
      break;
    case 'error':
      projectStatusText = 'Erreur critique';
      projectStatusIcon = <FaTimesCircle className="text-red-500" />;
      projectStatusColor = 'text-red-600';
      break;
    case 'assembly_failed':
      projectStatusText = 'Échec d\'assemblage';
      projectStatusIcon = <FaTimesCircle className="text-red-500" />;
      projectStatusColor = 'text-red-600';
      break;
    case 'export_failed':
      projectStatusText = 'Échec d\'exportation';
      projectStatusIcon = <FaTimesCircle className="text-red-500" />;
      projectStatusColor = 'text-red-600';
      break;
    default:
      projectStatusText = project.status;
      break;
  }

  // Déterminer si les boutons "Valider" / "Refaire" doivent être activés
  const canValidate = project.mode === 'Supervisé' && currentBlock && 
                      (currentBlock.status === 'pending_validation' || currentBlock.status === 'qc_passed');
  const canRedo = project.mode === 'Supervisé' && currentBlock && 
                   (currentBlock.status === 'pending_validation' || currentBlock.status === 'qc_failed' || currentBlock.status === 'refinement_failed');
  const canCompileAndExport = project.mode === 'Autonome' && project.status === 'completed';
  const canDownload = project.status === 'completed_exported';

  // Trouver le rapport QC pertinent à afficher (celui du bloc courant si en échec, sinon le dernier QC)
  const qcReportToDisplay = currentBlock?.qc_report?.status === 'failed' ? currentBlock.qc_report : 
                            contentBlocks.find(b => b.qc_report?.status === 'failed')?.qc_report || 
                            contentBlocks[contentBlocks.length - 1]?.qc_report;

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md p-4 space-y-6">
      {/* Section Informations Générales du Projet */}
      <div className="border-b pb-4 border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-2">{project.title}</h2>
        <div className="text-sm text-gray-600">
          <p>Sujet: <span className="font-medium">{project.subject}</span></p>
          <p>Niveau: <span className="font-medium">{project.level}</span></p>
          <p>Style: <span className="font-medium">{project.style}</span></p>
          <p>Mode: <span className="font-medium">{project.mode}</span></p>
        </div>
      </div>

      {/* Section Progression & Actions Workflow */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">Progression & Révision</h3>
        <div className={`flex items-center text-md font-semibold ${projectStatusColor}`}>
          <span className="mr-2">{projectStatusIcon}</span>
          <span>{projectStatusText}</span>
        </div>

        {project.mode === 'Supervisé' && currentBlock && (
          <div className="flex space-x-2">
            <button
              onClick={() => onSendSignal(project.project_id, { signal_type: 'VALIDATED', block_id: currentBlock.block_id })}
              className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              title="Valider le contenu actuel"
              disabled={!canValidate}
            >
              Valider
            </button>
            <button
              onClick={() => onSendSignal(project.project_id, { signal_type: 'REDO', block_id: currentBlock.block_id, feedback: { source: 'user', details: 'Nécessite des modifications (feedback détaillé à implémenter)' } })}
              className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors duration-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              title="Demander des modifications"
              disabled={!canRedo}
            >
              Refaire
            </button>
          </div>
        )}

        {canCompileAndExport && (
          <div className="mt-4">
            <button
              onClick={() => onSendSignal(project.project_id, { signal_type: 'ALL_APPROVED' })}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200 shadow-md"
              title="Compiler et exporter le document final"
            >
              Compiler et Exporter
            </button>
          </div>
        )}
        
        {canDownload && (
          <div className="mt-4">
            <button
              onClick={() => onDownloadExport(project.project_id, 'pdf')} {/* project_id comme placeholder pour export_id */}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors duration-200 shadow-md flex items-center justify-center"
              title="Télécharger le document PDF"
            >
              <FaDownload className="mr-2" /> Télécharger PDF
            </button>
          </div>
        )}

        {/* Notifications (simplifiées) */}
        <div className="mt-4">
          <h4 className="text-md font-semibold mb-2 text-gray-700">Notifications</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            {project.status === 'qc_failed' && (
              <li className="flex items-center text-orange-600">
                <FaExclamationTriangle className="mr-2" /> Bloc actuel: QC Échoué. Raffinement nécessaire.
              </li>
            )}
            {project.status === 'refinement_failed' && (
              <li className="flex items-center text-red-600">
                <FaTimesCircle className="mr-2" /> Bloc actuel: Raffinement Échoué. Intervention manuelle.
              </li>
            )}
            {/* Ajoutez d'autres notifications basées sur project.status ou des messages spécifiques */}
            {project.current_step && project.mode === 'Supervisé' && (
              <li className="flex items-center text-blue-600">
                <FaHourglassHalf className="mr-2" /> Étape actuelle: {project.current_step}
              </li>
            )}
            {project.mode === 'Autonome' && project.status === 'in_progress' && (
              <li className="flex items-center text-blue-600">
                <FaHourglassHalf className="mr-2" /> Génération autonome en cours...
              </li>
            )}
            {project.mode === 'Autonome' && project.status === 'completed' && (
              <li className="flex items-center text-green-600">
                <FaCheckCircle className="mr-2" /> Plan autonome terminé. Document prêt pour compilation.
              </li>
            )}
          </ul>
        </div>
      </div>

      {/* Arborescence du Document */}
      <div className="flex-grow overflow-y-auto border-t pt-4 border-gray-200">
        <DocumentTree 
          documentStructure={project.document_structure} 
          contentBlocks={contentBlocks} 
          onSelectNode={onSelectNode} 
        />
      </div>

      {/* Rapport QC Résumé (si un bloc est sélectionné ou si pertinent pour le projet global) */}
      {qcReportToDisplay && (
        <div className="border-t pt-4 border-gray-200">
          <QcReportGraph qcReport={qcReportToDisplay} />
        </div>
      )}
    </div>
  );
};

export default WorkflowPanel;
