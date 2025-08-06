// frontend/src/pages/ProjectEditorPage.js

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../api/apiService';
import RichTextEditor from '../components/specific/editor/RichTextEditor';
import WorkflowPanel from '../components/specific/workflow/WorkflowPanel';
import { FaSave, FaDownload } from 'react-icons/fa';

const ProjectEditorPage = () => {
  const { projectId } = useParams(); // Retrieves project ID from URL
  const queryClient = useQueryClient();
  const [editorContent, setEditorContent] = useState(''); // State for editor's LaTeX content
  const [currentBlockId, setCurrentBlockId] = useState(null); // ID of the block currently being edited/focused
  const editorRef = useRef(null); // Ref for the RichTextEditor component to access its internal methods

  // Query to fetch project details with polling for status updates
  const { data: project, isLoading, isError, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => apiService.getProject(projectId),
    refetchInterval: 5000, // Refreshes data every 5 seconds for polling
    onSuccess: (data) => {
      // If project is loaded for the first time or if content changes,
      // update the editor with the content of the first 'in_progress' or 'pending_validation' block
      if (!currentBlockId && data.content_blocks && data.content_blocks.length > 0) {
        const firstEditableBlock = data.content_blocks.find(
          (block) => block.status === 'in_progress' || block.status === 'pending_validation' || block.status === 'qc_failed' || block.status === 'refinement_failed' || block.status === 'draft'
        );
        if (firstEditableBlock) {
          setEditorContent(firstEditableBlock.content_latex || '');
          setCurrentBlockId(firstEditableBlock.block_id);
        } else {
          // If all blocks are validated, display the first validated block
          const firstValidatedBlock = data.content_blocks.find(
            (block) => block.status === 'validated'
          );
          if (firstValidatedBlock) {
            setEditorContent(firstValidatedBlock.content_latex || '');
            setCurrentBlockId(firstValidatedBlock.block_id);
          }
        }
      } else if (currentBlockId) {
        // If a block is already in focus, update its content if the backend has modified it
        const updatedBlock = data.content_blocks.find(
          (block) => block.block_id === currentBlockId
        );
        if (updatedBlock && updatedBlock.content_latex !== editorContent) {
          setEditorContent(updatedBlock.content_latex || '');
        }
      }
    },
  });

  // Mutation to save block content (manual editing)
  const saveBlockMutation = useMutation({
    mutationFn: ({ blockId, contentLatex }) => apiService.updateContentBlock(blockId, { content_latex: contentLatex }),
    onSuccess: () => {
      queryClient.invalidateQueries(['project', projectId]); // Invalidates project cache to refresh
      // alert('Block content saved!'); // Use a custom toast or visual indicator
    },
    onError: (err) => {
      console.error('Error saving block:', err);
      alert(`Failed to save block: ${err.message || 'Unknown error'}`);
    },
  });

  // Mutation to send a signal to the workflow (validation, redo, etc.)
  const sendSignalMutation = useMutation({
    mutationFn: ({ projectId, signalType, blockId, feedback }) =>
      apiService.sendWorkflowSignal(projectId, { signal_type: signalType, block_id: blockId, feedback }),
    onSuccess: () => {
      queryClient.invalidateQueries(['project', projectId]); // Project will be refreshed by polling
      alert('Signal sent to workflow!');
    },
    onError: (err) => {
      console.error('Error sending signal:', err);
      alert(`Failed to send signal: ${err.message || 'Unknown error'}`);
    },
  });

  // Mutation to download an exported document
  const downloadExportMutation = useMutation({
    mutationFn: ({ projectId, format }) => apiService.downloadExportedDocument(projectId, format),
    onSuccess: (data) => {
      if (data && data.download_url) {
        window.open(data.download_url, '_blank'); // Opens download URL in a new tab
      } else {
        alert('Download URL not available.');
      }
    },
    onError: (err) => {
      console.error('Error downloading export:', err);
      alert(`Failed to download: ${err.message || 'Unknown error'}`);
    },
  });

  // Handle content change in the editor
  const handleEditorContentChange = useCallback((newContent) => {
    setEditorContent(newContent.latex); // Updates local state with LaTeX
    // Optional: Trigger auto-save after a delay (debounce)
    // saveBlockMutation.mutate({ blockId: currentBlockId, contentLatex: newContent.latex });
  }, [currentBlockId, saveBlockMutation]);

  // Handle node selection in the document tree (to change editor content)
  const handleSelectNodeInTree = useCallback((nodeId, nodeObject) => {
    if (nodeObject.type === 'block') {
      const selectedBlock = project.content_blocks.find(b => b.block_id === nodeId);
      if (selectedBlock) {
        setEditorContent(selectedBlock.content_latex || '');
        setCurrentBlockId(selectedBlock.block_id);
        // Optional: Scroll the editor to the selected block
        // if (editorRef.current && editorRef.current.scrollToBlock) {
        //   editorRef.current.scrollToBlock(nodeId);
        // }
      }
    }
  }, [project]);


  const handleSaveContent = () => {
    if (currentBlockId && editorContent) {
      saveBlockMutation.mutate({ blockId: currentBlockId, contentLatex: editorContent });
    } else {
      alert('No block selected or empty content to save.');
    }
  };

  const handleDownloadExport = (projectId, format) => {
    downloadExportMutation.mutate({ projectId, format });
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-gray-600 text-lg">Loading project...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <p className="text-red-700 text-lg">Error loading project: {error.message}</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-gray-600 text-lg">Project not found.</p>
      </div>
    );
  }

  // Find the currently displayed block in the editor to pass its info to WorkflowPanel
  const currentBlock = project.content_blocks.find(b => b.block_id === currentBlockId);


  return (
    <div className="min-h-screen bg-gray-100 p-8 flex">
      {/* Main Column - Content Editor */}
      <div className="flex-1 bg-white rounded-xl shadow-lg p-8 mr-6 flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Project : {project.title}</h1>
          <div className="flex space-x-3">
            <button
              onClick={handleSaveContent}
              className="flex items-center px-4 py-2 bg-blue-500 text-white font-semibold rounded-md shadow-sm hover:bg-blue-600 transition-colors duration-200"
              disabled={saveBlockMutation.isPending}
            >
              <FaSave className="mr-2" /> Save
            </button>
            {project.status === 'completed_exported' && (
              <button
                onClick={() => handleDownloadExport(project.project_id, 'pdf')}
                className="flex items-center px-4 py-2 bg-purple-600 text-white font-semibold rounded-md shadow-sm hover:bg-purple-700 transition-colors duration-200"
                disabled={downloadExportMutation.isPending}
              >
                <FaDownload className="mr-2" /> Download PDF
              </button>
            )}
            {/* Project Settings Button (to be implemented) */}
            <button
              onClick={() => alert('Project Settings feature to be implemented')}
              className="px-4 py-2 bg-gray-200 text-gray-800 font-semibold rounded-md shadow-sm hover:bg-gray-300 transition-colors duration-200"
            >
              Settings
            </button>
          </div>
        </div>

        <div className="flex-1">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Content Editor</h2>
          <RichTextEditor 
            ref={editorRef} // Attach ref to the editor
            content={editorContent} 
            onContentChange={handleEditorContentChange} 
            editable={project.mode === 'Supervisé' || (project.mode === 'Autonome' && project.status !== 'completed' && project.status !== 'completed_exported')}
          />
        </div>
      </div>

      {/* Sidebar - Workflow Panel and Tools */}
      <div className="w-96 bg-white rounded-xl shadow-lg p-6 flex flex-col">
        <WorkflowPanel 
          project={project} 
          contentBlocks={project.content_blocks} 
          onSendSignal={sendSignalMutation.mutate} 
          onDownloadExport={handleDownloadExport}
          currentBlock={currentBlock}
          onSelectNode={handleSelectNodeInTree}
        />
      </div>
    </div>
  );
};

export default ProjectEditorPage;
