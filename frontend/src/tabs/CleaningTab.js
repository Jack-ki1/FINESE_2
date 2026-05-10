import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowPathIcon, 
  TrashIcon, 
  ArrowsRightLeftIcon,
  FunnelIcon,
  WrenchScrewdriverIcon
} from '@heroicons/react/24/outline';

const CleaningTab = ({ dataset, setDataset }) => {
  const [selectedOperations, setSelectedOperations] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Mock operations available
  const cleaningOperations = [
    { id: 'remove_duplicates', name: 'Remove Duplicates', description: 'Remove duplicate rows from the dataset' },
    { id: 'fill_missing', name: 'Fill Missing Values', description: 'Fill missing values with mean, median or mode' },
    { id: 'convert_types', name: 'Convert Data Types', description: 'Automatically convert data types for optimization' },
    { id: 'normalize', name: 'Normalize Data', description: 'Scale numeric columns to a standard range' },
    { id: 'remove_outliers', name: 'Remove Outliers', description: 'Detect and remove statistical outliers' },
    { id: 'drop_columns', name: 'Drop Columns', description: 'Remove specified columns from the dataset' },
  ];

  const handleOperationToggle = (operationId) => {
    if (selectedOperations.includes(operationId)) {
      setSelectedOperations(selectedOperations.filter(id => id !== operationId));
    } else {
      setSelectedOperations([...selectedOperations, operationId]);
    }
  };

  const handleApplyOperations = () => {
    setIsProcessing(true);
    // Simulate API call to apply cleaning operations
    setTimeout(() => {
      setIsProcessing(false);
      // In a real app, we would update the dataset based on the operations applied
      alert(`Applied ${selectedOperations.length} cleaning operations to the dataset`);
      setSelectedOperations([]);
    }, 2000);
  };

  const handlePreview = () => {
    // In a real app, this would call the API to get a preview of the cleaned data
    alert('Preview functionality would show the effect of selected operations');
  };

  return (
    <div className="space-y-6">
      <motion.div 
        className="card p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            <WrenchScrewdriverIcon className="h-5 w-5 mr-2 text-blue-500" />
            Data Cleaning Operations
          </h2>
          <div className="flex space-x-3">
            <button 
              onClick={handlePreview}
              disabled={selectedOperations.length === 0 || isProcessing}
              className={`${selectedOperations.length === 0 || isProcessing ? 'bg-gray-300 cursor-not-allowed' : 'bg-gray-200 hover:bg-gray-300'} text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center`}
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Preview
            </button>
            <button 
              onClick={handleApplyOperations}
              disabled={selectedOperations.length === 0 || isProcessing}
              className={`${selectedOperations.length === 0 || isProcessing ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'} text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center`}
            >
              {isProcessing ? (
                <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <ArrowPathIcon className="h-4 w-4 mr-2" />
              )}
              {isProcessing ? 'Processing...' : 'Apply Changes'}
            </button>
          </div>
        </div>

        <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <h3 className="font-medium text-blue-800 flex items-center">
            <ArrowsRightLeftIcon className="h-4 w-4 mr-2" />
            Selected Operations: {selectedOperations.length}
          </h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {selectedOperations.length > 0 ? (
              selectedOperations.map(opId => {
                const op = cleaningOperations.find(o => o.id === opId);
                return (
                  <span 
                    key={opId} 
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {op.name}
                    <button 
                      onClick={() => handleOperationToggle(opId)}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                );
              })
            ) : (
              <p className="text-blue-700 italic">No operations selected</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cleaningOperations.map((operation) => (
            <div 
              key={operation.id}
              className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                selectedOperations.includes(operation.id)
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
              }`}
              onClick={() => handleOperationToggle(operation.id)}
            >
              <div className="flex items-start">
                <input
                  type="checkbox"
                  checked={selectedOperations.includes(operation.id)}
                  onChange={() => handleOperationToggle(operation.id)}
                  className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-900">{operation.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{operation.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Data Preview Section */}
      <motion.div 
        className="card p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <TrashIcon className="h-5 w-5 mr-2 text-red-500" />
          Data Preview
        </h2>
        
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Age</th>
                <th>Income</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="font-medium">1</td>
                <td>John Doe</td>
                <td>john@example.com</td>
                <td>32</td>
                <td>$75,000</td>
              </tr>
              <tr>
                <td className="font-medium">2</td>
                <td>Jane Smith</td>
                <td>jane@example.com</td>
                <td>28</td>
                <td>$68,000</td>
              </tr>
              <tr>
                <td className="font-medium">3</td>
                <td>Robert Johnson</td>
                <td>NULL</td>
                <td>45</td>
                <td>$92,000</td>
              </tr>
              <tr>
                <td className="font-medium">4</td>
                <td>Sarah Williams</td>
                <td>sarah@example.com</td>
                <td>NULL</td>
                <td>$61,000</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            Show More Rows →
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default CleaningTab;