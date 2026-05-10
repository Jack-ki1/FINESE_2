import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Cog6ToothIcon, 
  PlayCircleIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

const ModelTab = ({ dataset }) => {
  const [modelType, setModelType] = useState('classification');
  const [targetColumn, setTargetColumn] = useState('');
  const [featureColumns, setFeatureColumns] = useState([]);
  const [availableColumns, setAvailableColumns] = useState([]);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingResult, setTrainingResult] = useState(null);

  // Mock columns for demonstration
  React.useEffect(() => {
    if (dataset) {
      const mockColumns = [
        { name: 'id', type: 'int64' },
        { name: 'name', type: 'object' },
        { name: 'age', type: 'int64' },
        { name: 'income', type: 'float64' },
        { name: 'category', type: 'object' },
        { name: 'score', type: 'float64' }
      ];
      setAvailableColumns(mockColumns);
    }
  }, [dataset]);

  const toggleFeature = (columnName) => {
    if (featureColumns.includes(columnName)) {
      setFeatureColumns(featureColumns.filter(col => col !== columnName));
    } else {
      setFeatureColumns([...featureColumns, columnName]);
    }
  };

  const startTraining = () => {
    if (!targetColumn || featureColumns.length === 0) {
      alert('Please select a target column and at least one feature column');
      return;
    }

    setIsTraining(true);

    // Simulate training process
    setTimeout(() => {
      // Mock results
      const mockResults = {
        modelId: 'model_' + Math.random().toString(36).substr(2, 9),
        metrics: {
          accuracy: 0.92,
          precision: 0.89,
          recall: 0.91,
          f1: 0.90
        },
        featureImportance: [
          { feature: 'age', importance: 0.42 },
          { feature: 'income', importance: 0.35 },
          { feature: 'category', importance: 0.23 }
        ],
        trainingTime: '2.4s'
      };

      setTrainingResult(mockResults);
      setIsTraining(false);
    }, 3000);
  };

  return (
    <div className="space-y-6">
      {!dataset ? (
        <div className="text-center py-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
            <Cog6ToothIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No dataset loaded</h3>
          <p className="mt-2 text-gray-500">
            Please upload a dataset to train machine learning models.
          </p>
        </div>
      ) : (
        <>
          {/* Model Configuration Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <Cog6ToothIcon className="h-5 w-5 mr-2 text-purple-500" />
              Model Configuration
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Model Type</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: 'classification', name: 'Classification', icon: ChartBarIcon },
                    { id: 'regression', name: 'Regression', icon: ArrowTrendingUpIcon }
                  ].map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setModelType(type.id)}
                      className={`flex flex-col items-center justify-center p-4 rounded-lg border ${
                        modelType === type.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-300 hover:border-purple-300'
                      }`}
                    >
                      <type.icon className={`h-6 w-6 mb-2 ${modelType === type.id ? 'text-purple-600' : 'text-gray-500'}`} />
                      <span className="text-sm font-medium">{type.name}</span>
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Column ({modelType === 'classification' ? 'Categorical' : 'Numerical'})
                </label>
                <select
                  value={targetColumn}
                  onChange={(e) => setTargetColumn(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white py-2 px-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Select target column</option>
                  {availableColumns
                    .filter(col => 
                      modelType === 'classification' 
                        ? col.type === 'object' 
                        : col.type.includes('int') || col.type.includes('float')
                    )
                    .map((col) => (
                      <option key={`target-${col.name}`} value={col.name}>{col.name} ({col.type})</option>
                    ))}
                </select>
                
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Selected Features</label>
                  <div className="flex flex-wrap gap-2">
                    {featureColumns.length > 0 ? (
                      featureColumns.map(col => (
                        <span 
                          key={`feat-${col}`} 
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                        >
                          {col}
                          <button 
                            onClick={() => toggleFeature(col)}
                            className="ml-2 text-purple-600 hover:text-purple-800"
                          >
                            ×
                          </button>
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-gray-500 italic">No features selected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Feature Selection</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-60 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                {availableColumns
                  .filter(col => col.name !== targetColumn)
                  .map((col) => (
                    <button
                      key={`feat-opt-${col.name}`}
                      onClick={() => toggleFeature(col.name)}
                      className={`flex items-center p-2 text-sm rounded ${
                        featureColumns.includes(col.name)
                          ? 'bg-purple-100 text-purple-800 border border-purple-300'
                          : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={featureColumns.includes(col.name)}
                        readOnly
                        className="h-4 w-4 text-purple-600 rounded mr-2"
                      />
                      <span className="truncate" title={col.name}>{col.name}</span>
                    </button>
                  ))}
              </div>
            </div>
            
            <div className="flex justify-end">
              <button
                onClick={startTraining}
                disabled={isTraining || !targetColumn || featureColumns.length === 0}
                className={`flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white ${
                  isTraining || !targetColumn || featureColumns.length === 0
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700'
                }`}
              >
                {isTraining ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Training...
                  </>
                ) : (
                  <>
                    <PlayCircleIcon className="h-5 w-5 mr-2" />
                    Start Training
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* Results Card */}
          {trainingResult && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <ArrowTrendingUpIcon className="h-5 w-5 mr-2 text-green-500" />
                Training Results
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <p className="text-sm font-medium text-green-800">Accuracy</p>
                  <p className="text-2xl font-bold text-green-600">{(trainingResult.metrics.accuracy * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <p className="text-sm font-medium text-blue-800">Precision</p>
                  <p className="text-2xl font-bold text-blue-600">{(trainingResult.metrics.precision * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-indigo-50 rounded-lg p-4 text-center">
                  <p className="text-sm font-medium text-indigo-800">Recall</p>
                  <p className="text-2xl font-bold text-indigo-600">{(trainingResult.metrics.recall * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 text-center">
                  <p className="text-sm font-medium text-purple-800">F1 Score</p>
                  <p className="text-2xl font-bold text-purple-600">{(trainingResult.metrics.f1 * 100).toFixed(1)}%</p>
                </div>
              </div>
              
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Feature Importance</h3>
                <div className="space-y-3">
                  {trainingResult.featureImportance.map((feature, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-32 text-sm font-medium text-gray-700">{feature.feature}</div>
                      <div className="flex-1 ml-4">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className="bg-purple-600 h-2.5 rounded-full" 
                            style={{ width: `${feature.importance * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="w-16 text-right text-sm font-medium text-gray-700">
                        {(feature.importance * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div>
                  <p className="text-sm text-gray-500">Model ID: {trainingResult.modelId}</p>
                  <p className="text-sm text-gray-500">Training Time: {trainingResult.trainingTime}</p>
                </div>
                <div className="flex space-x-3">
                  <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">
                    Download Model
                  </button>
                  <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                    Deploy Model
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
};

export default ModelTab;