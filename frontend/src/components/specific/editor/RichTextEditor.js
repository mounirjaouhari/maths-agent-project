// frontend/src/components/specific/editor/RichTextEditor.js

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Node, mergeAttributes } from '@tiptap/core'; // Import mergeAttributes
import Placeholder from '@tiptap/extension-placeholder'; // Pour les placeholders
import Document from '@tiptap/extension-document'; // Pour une meilleure gestion du document
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Bold from '@tiptap/extension-bold';
import Italic from '@tiptap/extension-italic';
import BulletList from '@tiptap/extension-bullet-list';
import ListItem from '@tiptap/extension-list-item';
import OrderedList from '@tiptap/extension-ordered-list';
import Heading from '@tiptap/extension-heading';


import katex from 'katex';
import 'katex/dist/katex.min.css'; // Inclure le CSS de KaTeX

// Logger simple pour le frontend
const logger = {
  info: (...args) => console.log('INFO:', ...args),
  warn: (...args) => console.warn('WARN:', ...args),
  error: (...args) => console.error('ERROR:', ...args),
};

// --- Définition du nœud TipTap pour les formules LaTeX inline ($...$) ---
const MathInline = Node.create({
  name: 'mathInline',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      latex: {
        default: '',
        parseHTML: element => element.getAttribute('data-latex'),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-type="math-inline"]',
        getAttrs: element => ({ latex: element.getAttribute('data-latex') }),
      },
    ];
  },

  renderHTML({ HTMLAttributes, node }) {
    const latex = node.attrs.latex;
    let html = '';
    try {
      html = katex.renderToString(latex, {
        throwOnError: false,
        displayMode: false,
      });
    } catch (e) {
      logger.error('Erreur de rendu KaTeX (inline):', e);
      html = `<span style="color: red; background-color: #ffe0e0; padding: 2px 4px; border-radius: 4px;">Erreur LaTeX: ${latex}</span>`;
    }

    return ['span', mergeAttributes(HTMLAttributes, { 'data-type': 'math-inline', 'data-latex': latex, class: 'math-inline-rendered' }), 0];
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const dom = document.createElement('span');
      dom.classList.add('math-inline-view');
      dom.setAttribute('data-type', 'math-inline');
      dom.setAttribute('data-latex', node.attrs.latex);

      const renderMath = (latex) => {
        try {
          dom.innerHTML = katex.renderToString(latex, { throwOnError: false, displayMode: false });
        } catch (e) {
          dom.innerHTML = `<span style="color: red; background-color: #ffe0e0; padding: 2px 4px; border-radius: 4px;">Erreur LaTeX: ${latex}</span>`;
        }
      };

      renderMath(node.attrs.latex);

      dom.addEventListener('dblclick', () => {
        const currentLatex = node.attrs.latex;
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentLatex;
        input.classList.add('tiptap-math-edit-input');
        
        dom.replaceWith(input);
        input.focus();

        const finishEditing = () => {
          const newLatex = input.value;
          editor.chain().focus().setNodeSelection(getPos()).updateAttributes(MathInline.name, { latex: newLatex }).run();
          input.replaceWith(dom);
        };

        input.addEventListener('blur', finishEditing);
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            finishEditing();
          }
        });
      });

      return {
        dom,
        update: (updatedNode) => {
          if (updatedNode.attrs.latex !== node.attrs.latex) {
            node = updatedNode;
            renderMath(node.attrs.latex);
            return true;
          }
          return false;
        },
        destroy: () => {
          dom.removeEventListener('dblclick', () => {});
        },
      };
    };
  },
});

// --- Définition du nœud TipTap pour les blocs de formules LaTeX ($$...$$ ou \begin{equation}...\end{equation}) ---
const MathBlock = Node.create({
  name: 'mathBlock',
  group: 'block',
  content: 'text*',
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      latex: {
        default: '',
        parseHTML: element => element.getAttribute('data-latex'),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="math-block"]',
        getAttrs: element => ({ latex: element.getAttribute('data-latex') }),
      },
    ];
  },

  renderHTML({ HTMLAttributes, node }) {
    const latex = node.attrs.latex;
    let html = '';
    try {
      html = katex.renderToString(latex, {
        throwOnError: false,
        displayMode: true,
      });
    } catch (e) {
      logger.error('Erreur de rendu KaTeX (bloc):', e);
      html = `<div style="color: red; background-color: #ffe0e0; padding: 8px; border-radius: 4px; text-align: center;">Erreur LaTeX: ${latex}</div>`;
    }

    return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'math-block', 'data-latex': latex, class: 'math-block-rendered' }), 0];
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const dom = document.createElement('div');
      dom.classList.add('math-block-view');
      dom.setAttribute('data-type', 'math-block');
      dom.setAttribute('data-latex', node.attrs.latex);

      const renderMath = (latex) => {
        try {
          dom.innerHTML = katex.renderToString(latex, { throwOnError: false, displayMode: true });
        } catch (e) {
          dom.innerHTML = `<div style="color: red; background-color: #ffe0e0; padding: 8px; border-radius: 4px; text-align: center;">Erreur LaTeX: ${latex}</div>`;
        }
      };

      renderMath(node.attrs.latex);

      dom.addEventListener('dblclick', () => {
        const currentLatex = node.attrs.latex;
        const textarea = document.createElement('textarea');
        textarea.value = currentLatex;
        textarea.classList.add('tiptap-math-edit-textarea');
        
        dom.replaceWith(textarea);
        textarea.focus();

        const finishEditing = () => {
          const newLatex = textarea.value;
          editor.chain().focus().setNodeSelection(getPos()).updateAttributes(MathBlock.name, { latex: newLatex }).run();
          textarea.replaceWith(dom);
        };

        textarea.addEventListener('blur', finishEditing);
        textarea.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            finishEditing();
          }
        });
      });

      return {
        dom,
        update: (updatedNode) => {
          if (updatedNode.attrs.latex !== node.attrs.latex) {
            node = updatedNode;
            renderMath(node.attrs.latex);
            return true;
          }
          return false;
        },
        destroy: () => {
          dom.removeEventListener('dblclick', () => {});
        },
      };
    };
  },
});


// Helper function to extract full LaTeX from TipTap editor content
// This function needs to correctly reconstruct LaTeX from a TipTap JSON document
// considering custom nodes and their attributes.
const getFullLatexFromTiptapJSON = (jsonContent) => {
  let fullLatex = '';

  const traverse = (node) => {
    if (!node) return;

    if (node.type === 'mathInline') {
      fullLatex += `$${node.attrs.latex}$`;
    } else if (node.type === 'mathBlock') {
      fullLatex += `\\[${node.attrs.latex}\\]\n\n`; // Add newlines for block math
    } else if (node.text) {
      fullLatex += node.text;
    }

    if (node.content) {
      node.content.forEach(child => traverse(child));
    }

    // Add paragraph breaks or other block-level element breaks
    if (node.type === 'paragraph' || node.type === 'heading') {
      fullLatex += '\n\n';
    }
  };

  if (jsonContent && jsonContent.content) {
    jsonContent.content.forEach(node => traverse(node));
  }

  return fullLatex.trim();
};


// Main RichTextEditor component
const RichTextEditor = ({ content, onContentChange, editable = true, placeholderText = "Commencez à rédiger votre contenu mathématique ici..." }) => {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Désactiver les extensions par défaut si vous voulez les contrôler plus finement
        // par exemple, pour éviter les conflits avec les nœuds mathématiques
        heading: { levels: [1, 2, 3] },
        // paragraph: false, // Ne pas désactiver le paragraphe, sinon le texte n'aura pas de parent
        // text: false,
      }),
      MathInline,
      MathBlock,
      Placeholder.configure({
        placeholder: placeholderText,
      }),
      // Add other TipTap extensions as needed (e.g., Link, Image, Table)
    ],
    content: content,
    editable: editable,
    onUpdate: ({ editor }) => {
      const jsonContent = editor.getJSON();
      const htmlContent = editor.getHTML();
      const currentFullLatex = getFullLatexFromTiptapJSON(jsonContent); // Use the improved function

      onContentChange({
        json: jsonContent,
        html: htmlContent,
        latex: currentFullLatex,
      });
    },
  }, [editable]); // Re-initialise l'éditeur si 'editable' change

  // Synchronize external content with the editor if 'content' changes
  // This is a more robust way to handle external content updates.
  useEffect(() => {
    if (editor && content) {
      const currentEditorJson = editor.getJSON();
      const incomingContentJson = editor.schema.nodeFromJSON(content).toJSON(); // Convert incoming content to TipTap JSON structure

      // Deep comparison might be needed for complex structures
      if (JSON.stringify(currentEditorJson) !== JSON.stringify(incomingContentJson)) {
        editor.commands.setContent(incomingContentJson, false); // false to prevent triggering onUpdate immediately
        logger.info("Editor content updated from external source.");
      }
    }
  }, [content, editor]);


  // Toolbar functions (to be implemented in a separate Toolbar component)
  const addMathInline = useCallback(() => {
    if (editor) {
      editor.chain().focus().insertContent('$').insertContent('$').setNodeSelection(editor.state.selection.from - 1).run();
    }
  }, [editor]);

  const addMathBlock = useCallback(() => {
    if (editor) {
      editor.chain().focus().insertContent('\\[').insertContent('\\]').setNodeSelection(editor.state.selection.from - 2).run(); // Adjusted selection for \\[
    }
  }, [editor]);

  const addEquationEnvironment = useCallback(() => {
    if (editor) {
      editor.chain().focus().insertContent('\\begin{equation}\n\n\\end{equation}').setNodeSelection(editor.state.selection.from - 13).run();
    }
  }, [editor]);


  if (!editor) {
    return null;
  }

  return (
    <div className="border border-gray-300 rounded-lg shadow-sm overflow-hidden bg-white">
      {/* Editor Toolbar (simplified here) */}
      <div className="flex flex-wrap p-2 border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-2 rounded-md hover:bg-gray-200 ${editor.isActive('bold') ? 'bg-gray-200' : ''}`}
          title="Gras"
        >
          <strong>B</strong>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-2 rounded-md hover:bg-gray-200 ${editor.isActive('italic') ? 'bg-gray-200' : ''}`}
          title="Italique"
        >
          <em>I</em>
        </button>
        <button
          onClick={addMathInline}
          className="p-2 rounded-md hover:bg-gray-200"
          title="Insérer formule inline ($...$)"
        >
          $f(x)$
        </button>
        <button
          onClick={addMathBlock}
          className="p-2 rounded-md hover:bg-gray-200"
          title="Insérer bloc formule (\\[...\\])"
        >
          $$\sum$$
        </button>
        <button
          onClick={addEquationEnvironment}
          className="p-2 rounded-md hover:bg-gray-200"
          title="Insérer environnement equation"
        >
          Eq
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-2 rounded-md hover:bg-gray-200 ${editor.isActive('bulletList') ? 'bg-gray-200' : ''}`}
          title="Liste à puces"
        >
          UL
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-2 rounded-md hover:bg-gray-200 ${editor.isActive('orderedList') ? 'bg-gray-200' : ''}`}
          title="Liste numérotée"
        >
          OL
        </button>
        <select
          onChange={(e) => editor.chain().focus().toggleHeading({ level: parseInt(e.target.value) }).run()}
          value={editor.isActive('heading') ? editor.state.doc.resolve(editor.state.selection.from).node().attrs.level : ''}
          className="p-2 rounded-md border border-gray-300 bg-white text-sm"
          title="Titre"
        >
          <option value="">Texte normal</option>
          <option value="1">Titre 1</option>
          <option value="2">Titre 2</option>
          <option value="3">Titre 3</option>
        </select>
      </div>

      {/* Editor Area */}
      <EditorContent editor={editor} className="p-4 min-h-[300px] max-h-[600px] overflow-y-auto" />

      {/* Styles for TipTap Editor and KaTeX */}
      <style jsx>{`
        /* Base styles for the editor */
        .ProseMirror {
          min-height: 300px;
          outline: none;
        }

        /* Placeholder style */
        .ProseMirror p.is-empty::before {
          content: attr(data-placeholder);
          float: left;
          color: #adb5bd;
          pointer-events: none;
          height: 0;
        }

        /* Styles for math nodes */
        .math-inline-rendered, .math-block-rendered {
          cursor: pointer;
          display: inline-block;
          vertical-align: middle;
          margin: 0 2px;
          padding: 1px 3px;
          border-radius: 4px;
          transition: background-color 0.2s ease-in-out;
        }
        .math-inline-rendered:hover, .math-block-rendered:hover {
          background-color: #e0e7ff;
        }

        .math-block-rendered {
          display: block;
          text-align: center;
          margin: 10px auto;
          padding: 10px;
          background-color: #f8faff;
          border: 1px solid #e0e7ff;
        }

        /* Styles for math editing input/textarea */
        .tiptap-math-edit-input, .tiptap-math-edit-textarea {
          width: 100%;
          padding: 8px;
          border: 1px solid #a0c0ff;
          border-radius: 4px;
          font-family: 'monospace';
          font-size: 0.9rem;
          background-color: #f0f8ff;
          box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }
        .tiptap-math-edit-textarea {
          min-height: 80px;
          resize: vertical;
        }
      `}</style>
    </div>
  );
};

export default RichTextEditor;
