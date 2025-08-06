// frontend/src/components/specific/visualizations/DocumentTree.js

import React from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaHourglassHalf, FaTimesCircle, FaEdit } from 'react-icons/fa'; // Icônes pour les statuts
import { FaCircleDot } from "react-icons/fa6"; // Icône pour le statut par défaut

// Helper function to determine the aggregated status of a node based on its children
const getAggregatedStatus = (children, contentBlocksStatus) => {
  if (!children || children.length === 0) {
    return 'default';
  }

  const statuses = children.map(child => {
    if (child.type === 'block' && contentBlocksStatus[child.block_id]) {
      return contentBlocksStatus[child.block_id].status;
    } else if (child.sections || child.blocks) {
      // Recursively get status for nested sections/blocks
      const nestedChildren = [...(child.sections || []), ...(child.blocks || [])];
      return getAggregatedStatus(nestedChildren, contentBlocksStatus);
    }
    return 'default';
  });

  if (statuses.includes('critical_error')) return 'critical_error';
  if (statuses.includes('generation_failed') || statuses.includes('refinement_failed') || statuses.includes('qc_failed')) return 'failed';
  if (statuses.includes('pending_validation')) return 'pending_validation';
  if (statuses.includes('generation_in_progress') || statuses.includes('qc_in_progress') || statuses.includes('refinement_in_progress')) return 'in_progress';
  if (statuses.some(s => s !== 'validated' && s !== 'archived' && s !== 'default')) return 'in_progress'; // If any child is not finalized
  if (statuses.every(s => s === 'validated' || s === 'archived' || s === 'default')) return 'validated'; // All children are finalized
  
  return 'default';
};

// Composant récursif pour rendre un nœud de l'arborescence
const TreeNode = ({ node, onSelectNode, contentBlocksStatus }) => {
  const { id, title, type, blocks, sections, chapter_id, section_id, block_id } = node;

  // Use the appropriate ID based on node type
  const nodeId = id || chapter_id || section_id || block_id;

  let status = 'default';
  let icon = <FaCircleDot className="text-gray-400" />;
  let statusColorClass = 'text-gray-500';

  if (type === 'block') {
    status = contentBlocksStatus[nodeId]?.status || 'default';
  } else {
    // For chapters/sections, aggregate statuses of children
    const childrenToAggregate = [...(sections || []), ...(blocks || [])];
    status = getAggregatedStatus(childrenToAggregate, contentBlocksStatus);
  }

  // Define icon and color based on status
  switch (status) {
    case 'validated':
      icon = <FaCheckCircle className="text-green-500" />;
      statusColorClass = 'text-green-600';
      break;
    case 'pending_validation':
      icon = <FaEdit className="text-yellow-500" />;
      statusColorClass = 'text-yellow-600';
      break;
    case 'in_progress':
      icon = <FaHourglassHalf className="text-blue-500 animate-pulse" />;
      statusColorClass = 'text-blue-600';
      break;
    case 'qc_failed':
    case 'generation_failed':
    case 'refinement_failed':
      icon = <FaExclamationTriangle className="text-orange-500" />;
      statusColorClass = 'text-orange-600';
      break;
    case 'critical_error':
      icon = <FaTimesCircle className="text-red-500" />;
      statusColorClass = 'text-red-600';
      break;
    default:
      icon = <FaCircleDot className="text-gray-400" />;
      statusColorClass = 'text-gray-500';
  }

  return (
    <li className="mb-1">
      <div 
        className={`flex items-center p-2 rounded-md cursor-pointer hover:bg-gray-100 transition-colors duration-200 ${statusColorClass}`}
        onClick={() => onSelectNode(nodeId, node)} // Pass node ID and full node object
      >
        <span className="mr-2 text-sm">{icon}</span>
        <span className="text-sm font-medium">{title || `Bloc ${nodeId.substring(0, 4)}...`}</span>
        {/* Display QC score if available and relevant for blocks */}
        {type === 'block' && contentBlocksStatus[nodeId] && contentBlocksStatus[nodeId].qc_report && (
          <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full ${contentBlocksStatus[nodeId].qc_report.overall_score >= 80 ? 'bg-green-200 text-green-800' : contentBlocksStatus[nodeId].qc_report.overall_score >= 60 ? 'bg-yellow-200 text-yellow-800' : 'bg-red-200 text-red-800'}`}>
            QC: {contentBlocksStatus[nodeId].qc_report.overall_score.toFixed(0)}%
          </span>
        )}
      </div>
      {sections && sections.length > 0 && (
        <ul className="ml-4 mt-1 border-l border-gray-200 pl-2">
          {sections.map(subSection => (
            <TreeNode 
              key={subSection.id || subSection.section_id} 
              node={subSection} 
              onSelectNode={onSelectNode} 
              contentBlocksStatus={contentBlocksStatus} 
            />
          ))}
        </ul>
      )}
      {blocks && blocks.length > 0 && (
        <ul className="ml-4 mt-1 border-l border-gray-200 pl-2">
          {blocks.map(block => (
            <TreeNode 
              key={block.block_id} 
              node={{ id: block.block_id, title: block.block_type, type: 'block' }} 
              onSelectNode={onSelectNode} 
              contentBlocksStatus={contentBlocksStatus} 
            />
          ))}
        </ul>
      )}
    </li>
  );
};

const DocumentTree = ({ documentStructure, contentBlocks, onSelectNode }) => {
  // Map content blocks by ID for easy status access
  const contentBlocksStatus = contentBlocks.reduce((acc, block) => {
    acc[block.block_id] = block;
    return acc;
  }, {});

  if (!documentStructure || !documentStructure.chapters || documentStructure.chapters.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Aucune structure de document disponible.
      </div>
    );
  }

  return (
    <div className="font-sans">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">Arborescence du Document</h3>
      <ul className="space-y-1">
        {documentStructure.chapters.map(chapter => (
          <TreeNode 
            key={chapter.id || chapter.chapter_id} 
            node={chapter} 
            onSelectNode={onSelectNode} 
            contentBlocksStatus={contentBlocksStatus} 
          />
        ))}
      </ul>
    </div>
  );
};

export default DocumentTree;
