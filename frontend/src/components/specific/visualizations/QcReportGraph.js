// frontend/src/components/specific/visualizations/QcReportGraph.js

import React, { useState } from 'react';
// Pour les icônes si nous voulons les utiliser dans la légende ou le titre
// import { FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from 'react-icons/fa';

// Composant Modal pour afficher les détails des problèmes
const ProblemDetailsModal = ({ problems, onClose }) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-11/12 md:w-2/3 lg:w-1/2 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center border-b pb-3 mb-4">
          <h3 className="text-xl font-semibold text-gray-800">Détails des Problèmes QC</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl font-bold">&times;</button>
        </div>
        {problems.length === 0 ? (
          <p className="text-gray-600">Aucun problème détaillé à afficher.</p>
        ) : (
          <ul className="space-y-4">
            {problems.map((problem, index) => (
              <li key={index} className="border border-gray-200 rounded-md p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className={`font-semibold text-sm px-2 py-0.5 rounded-full 
                    ${problem.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      problem.severity === 'major' ? 'bg-orange-100 text-orange-800' :
                      problem.severity === 'minor' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'}`}>
                    {problem.severity.charAt(0).toUpperCase() + problem.severity.slice(1)}
                  </span>
                  <span className="text-xs text-gray-500">{problem.type.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-gray-700 mb-2">{problem.description}</p>
                {problem.location && (
                  <p className="text-xs text-gray-500">
                    Localisation: Ligne {problem.location.line || 'N/A'}, Caractère {problem.location.char_start || 'N/A'}-{problem.location.char_end || 'N/A'}
                  </p>
                )}
                {problem.suggested_fix && (
                  <p className="text-sm text-blue-600 mt-2">Suggestion: {problem.suggested_fix}</p>
                )}
              </li>
            ))}
          </ul>
        )}
        <div className="text-right mt-4">
          <button onClick={onClose} className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">Fermer</button>
        </div>
      </div>
    </div>
  );
};


const QcReportGraph = ({ qcReport }) => {
  const [showModal, setShowModal] = useState(false);

  if (!qcReport || !qcReport.problems) {
    return (
      <div className="p-4 text-gray-500 text-center">
        Aucun rapport QC disponible.
      </div>
    );
  }

  // Calculate the distribution of problem types
  const problemTypeCounts = qcReport.problems.reduce((acc, problem) => {
    acc[problem.type] = (acc[problem.type] || 0) + 1;
    return acc;
  }, {});

  const totalProblems = qcReport.problems.length;

  // Prepare data for the pie chart (if totalProblems > 0)
  const pieChartData = totalProblems > 0 ? Object.keys(problemTypeCounts).map(type => ({
    type,
    count: problemTypeCounts[type],
    percentage: (problemTypeCounts[type] / totalProblems) * 100
  })) : [];

  // Define colors for problem types (customizable)
  const typeColors = {
    'math_error': '#EF4444', // Red for math errors
    'clarity_issue': '#F59E0B', // Orange for clarity issues
    'style_mismatch': '#3B82F6', // Blue for style issues
    'coherence_issue': '#10B981', // Green for coherence issues
    'formatting_error': '#6B7280', // Gray for formatting errors
    'pedagogic_pitfall': '#8B5CF6', // Violet for pedagogical pitfalls
    'other': '#6366F1', // Indigo for others
  };

  // Function to get the SVG path of a pie segment
  const getPath = (cx, cy, radius, startAngle, endAngle) => {
    const toRadians = (angle) => angle * (Math.PI / 180);
    const x1 = cx + radius * Math.cos(toRadians(startAngle));
    const y1 = cy + radius * Math.sin(toRadians(startAngle));
    const x2 = cx + radius * Math.cos(toRadians(endAngle));
    const y2 = cy + radius * Math.sin(toRadians(endAngle));

    const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;

    return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
  };

  let currentAngle = 0;
  const pieSegments = pieChartData.map((data, index) => {
    const angle = (data.percentage / 100) * 360;
    const path = getPath(100, 100, 80, currentAngle, currentAngle + angle);
    const color = typeColors[data.type] || '#CCCCCC'; // Default color
    currentAngle += angle;
    return <path key={data.type} d={path} fill={color} />;
  });

  // Determine the color class for the overall score
  let scoreColorClass = 'bg-gray-200 text-gray-800';
  if (qcReport.overall_score >= 90) {
    scoreColorClass = 'bg-green-200 text-green-800';
  } else if (qcReport.overall_score >= 70) {
    scoreColorClass = 'bg-yellow-200 text-yellow-800';
  } else {
    scoreColorClass = 'bg-red-200 text-red-800';
  }

  return (
    <div className="font-sans p-4 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">Rapport QC Résumé</h3>
      
      {/* Overall Score */}
      <div className="mb-4 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Score Global:</span>
        <span className={`text-lg font-bold px-3 py-1 rounded-full ${scoreColorClass}`}>
          {qcReport.overall_score.toFixed(0)}%
        </span>
      </div>

      {/* Report Status */}
      <div className="mb-4 text-sm text-gray-700">
        Statut: <span className="font-semibold">{qcReport.status}</span>
      </div>

      {/* Pie chart of problem distribution */}
      {totalProblems > 0 ? (
        <div className="mb-4">
          <h4 className="text-md font-semibold mb-2 text-gray-700">Répartition des Problèmes ({totalProblems} au total)</h4>
          <div className="flex flex-col items-center">
            <svg width="200" height="200" viewBox="0 0 200 200">
              {pieSegments}
            </svg>
            <div className="flex flex-wrap justify-center mt-3 text-sm">
              {pieChartData.map((data, index) => (
                <div key={data.type} className="flex items-center mr-4 mb-2">
                  <span className="inline-block w-3 h-3 rounded-full mr-2" style={{ backgroundColor: typeColors[data.type] || '#CCCCCC' }}></span>
                  {data.type.replace(/_/g, ' ')} ({data.percentage.toFixed(1)}%)
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-4 text-gray-500 text-center border border-gray-200 rounded-md">
          Aucun problème détecté.
        </div>
      )}

      {/* Link to detailed report */}
      <div className="text-center mt-4">
        <button 
          onClick={() => setShowModal(true)}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Voir le rapport détaillé
        </button>
      </div>

      {showModal && (
        <ProblemDetailsModal problems={qcReport.problems} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
};

export default QcReportGraph;
