import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { 
  ArrowPathIcon, 
  DocumentTextIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  EyeIcon,
  TableCellsIcon
} from '@heroicons/react/24/outline';

const ReviewTab = ({ dataset }) => {
  const [datasetSummary, setDatasetSummary] = useState(null);
  const [healthScore, setHealthScore] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoInsights, setAutoInsights] = useState([]);

  // Mock data for demonstration purposes
  const mockSummary = {
    dataset_id: "ds_abc123",
    name: "Sample Dataset.csv",
    shape: [1000, 15],
    columns: [
      { name: "id", dtype: "int64", missing_count: 0, missing_percentage: 0.0, unique_count: 1000 },
      { name: "name", dtype: "object", missing_count: 5, missing_percentage: 0.5, unique_count: 950 },
      { name: "email", dtype: "object", missing_count: 10, missing_percentage: 1.0, unique_count: 980 },
      { name: "age", dtype: "int64", missing_count: 2, missing_percentage: 0.2, unique_count: 50 },
      { name: "income", dtype: "float64", missing_count: 8, missing_percentage: 0.8, unique_count: 400 },
    ],
    created_at: new Date().toISOString(),
    size_mb: 0.5
  };

  const mockHealthScore = {
    final_score: 87,
    details: {
      completeness: 92,
      consistency: 85,
      accuracy: 88,
      uniqueness: 95,
      timeliness: 80
    },
    diagnostics: {
      missing_values: { id: 0, name: 5, email: 10, age: 2, income: 8 },
      duplicate_rows: 3,
      numeric_columns: ["id", "age", "income"],
      categorical_columns: ["name", "email"]
    },
    recommendations: [
      "Consider filling missing values in the 'email' column",
      "Column 'name' has high cardinality - consider if it's useful for analysis",
      "Remove 3 duplicate rows to improve uniqueness"
    ],
    generated_at: new Date().toISOString()
  };

  const mockInsights = [
    "Dataset has 1000 rows and 15 columns",
    "Only 3 duplicate rows found - data quality is generally good",
    "Column 'email' has 1% missing values that could be imputed",
    "Income column has a wide range - consider normalization for ML models"
  ];

  useEffect(() => {
    if (dataset) {
      // In a real app, we would fetch actual data from the API
      setDatasetSummary(mockSummary);
      setHealthScore(mockHealthScore);
      setAutoInsights(mockInsights);
    } else {
      setDatasetSummary(null);
      setHealthScore(null);
      setAutoInsights([]);
    }
  }, [dataset]);

  const generateReport = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
    }, 1500);
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBadgeText = (score) => {
    if (score >= 95) return "🏆 Perfect Dataset";
    if (score >= 90) return "🥇 Data Master";
    if (score >= 80) return "🥈 Clean Data Apprentice";
    if (score >= 70) return "🥉 Data Novice";
    if (score >= 60) return "⚠️ Needs Attention";
    return "📉 Critical Issues";
  };

  return (
    <div className="space-y-6">
      {!dataset ? (
        <div className="text-center py-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
            <EyeIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No dataset loaded</h3>
          <p className="mt-2 text-gray-500">
            Please upload a dataset in the header section to review it.
          </p>
        </div>
      ) : (
        <>
          {/* Data Summary Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <TableCellsIcon className="h-5 w-5 mr-2 text-blue-500" />
                Data Summary
              </h2>
              <button 
                onClick={generateReport}
                disabled={isLoading}
                className="btn-primary flex items-center"
              >
                {isLoading ? (
                  <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <DocumentTextIcon className="h-4 w-4 mr-2" />
                )}
                {isLoading ? 'Generating...' : 'Generate Report'}
              </button>
            </div>

            {datasetSummary && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-800">Rows</p>
                  <p className="text-2xl font-bold text-blue-600">{datasetSummary.shape[0].toLocaleString()}</p>
                </div>
                <div className="bg-indigo-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-indigo-800">Columns</p>
                  <p className="text-2xl font-bold text-indigo-600">{datasetSummary.shape[1]}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-green-800">Size</p>
                  <p className="text-2xl font-bold text-green-600">{datasetSummary.size_mb} MB</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-purple-800">Created</p>
                  <p className="text-lg font-bold text-purple-600">
                    {new Date(datasetSummary.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            )}

            {datasetSummary && (
              <div className="mt-6 overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column Name</th>
                      <th>Data Type</th>
                      <th>Missing</th>
                      <th>% Missing</th>
                      <th>Unique Values</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datasetSummary.columns.map((col, index) => (
                      <tr key={index}>
                        <td className="font-medium text-gray-900">{col.name}</td>
                        <td>
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            {col.dtype}
                          </span>
                        </td>
                        <td>{col.missing_count}</td>
                        <td>{col.missing_percentage}%</td>
                        <td>{col.unique_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>

          {/* Health Score Card */}
          {healthScore && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2 text-green-500" />
                Data Health Score
              </h2>
              
              <div className="text-center mb-8">
                <div className="text-6xl font-bold mb-2">
                  <span className={getScoreColor(healthScore.final_score)}>
                    {healthScore.final_score}
                  </span>
                  <span className="text-2xl text-gray-500">/100</span>
                </div>
                <p className="text-lg text-gray-700">{getBadgeText(healthScore.final_score)}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {Object.entries(healthScore.details).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700 capitalize">{key.replace('_', ' ')}</p>
                    <p className={`text-2xl font-bold ${getScoreColor(value)}`}>{value}%</p>
                    <div className="mt-2">
                      <div className="progress-bar">
                        <div 
                          className="progress-bar-fill" 
                          style={{ width: `${value}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Auto Insights Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <DocumentTextIcon className="h-5 w-5 mr-2 text-yellow-500" />
              Auto Insights
            </h2>
            
            <div className="space-y-4">
              {autoInsights.length > 0 ? (
                autoInsights.map((insight, index) => (
                  <div key={index} className="flex items-start p-4 bg-blue-50 rounded-lg border border-blue-100">
                    <ExclamationTriangleIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" />
                    <p className="text-gray-700">{insight}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No insights generated yet. Load a dataset to analyze.</p>
              )}
            </div>
          </motion.div>

          {/* Recommendations Card */}
          {healthScore && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-orange-500" />
                Recommendations
              </h2>
              
              <div className="space-y-3">
                {healthScore.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start">
                    <span className="flex-shrink-0 h-6 w-6 rounded-full bg-orange-100 text-orange-800 text-xs flex items-center justify-center mr-3 mt-0.5">
                      {index + 1}
                    </span>
                    <p className="text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
};

export default ReviewTab;