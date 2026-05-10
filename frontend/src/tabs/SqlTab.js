import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CommandLineIcon, 
  TableCellsIcon, 
  ArrowPathIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const SqlTab = ({ dataset }) => {
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM dataset LIMIT 10;');
  const [queryResult, setQueryResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);
  const [availableColumns, setAvailableColumns] = useState([]);
  const [executionTime, setExecutionTime] = useState(null);

  // Mock columns for demonstration
  useEffect(() => {
    if (dataset) {
      setAvailableColumns([
        { name: 'id', type: 'INTEGER', nullable: false, unique_values: 1000, null_count: 0 },
        { name: 'name', type: 'TEXT', nullable: true, unique_values: 950, null_count: 5 },
        { name: 'email', type: 'TEXT', nullable: true, unique_values: 980, null_count: 10 },
        { name: 'age', type: 'INTEGER', nullable: false, unique_values: 50, null_count: 2 },
        { name: 'income', type: 'REAL', nullable: true, unique_values: 400, null_count: 8 },
      ]);
    }
  }, [dataset]);

  const executeQuery = () => {
    if (!sqlQuery.trim() || !dataset) return;

    setIsLoading(true);
    
    // Add to history
    const newQuery = {
      id: queryHistory.length + 1,
      query: sqlQuery,
      timestamp: new Date().toISOString()
    };
    setQueryHistory([newQuery, ...queryHistory.slice(0, 9)]); // Keep only last 10

    // Simulate query execution
    setTimeout(() => {
      // Mock result data
      const mockResult = {
        success: true,
        data: [
          { id: 1, name: 'John Doe', email: 'john@example.com', age: 32, income: 75000 },
          { id: 2, name: 'Jane Smith', email: 'jane@example.com', age: 28, income: 68000 },
          { id: 3, name: 'Robert Johnson', email: 'robert@example.com', age: 45, income: 92000 },
          { id: 4, name: 'Sarah Williams', email: 'sarah@example.com', age: 35, income: 81000 },
          { id: 5, name: 'Michael Brown', email: 'michael@example.com', age: 29, income: 72000 },
        ],
        row_count: 5,
        columns: ['id', 'name', 'email', 'age', 'income'],
        execution_time: '0.12s'
      };
      
      setQueryResult(mockResult);
      setExecutionTime(mockResult.execution_time);
      setIsLoading(false);
    }, 1500);
  };

  const loadSampleQuery = (type) => {
    switch(type) {
      case 'basic':
        setSqlQuery('SELECT * FROM dataset LIMIT 10;');
        break;
      case 'aggregate':
        setSqlQuery('SELECT COUNT(*), AVG(age), MAX(income) FROM dataset;');
        break;
      case 'filter':
        setSqlQuery("SELECT * FROM dataset WHERE age > 30 AND income > 50000;");
        break;
      case 'sort':
        setSqlQuery("SELECT name, age, income FROM dataset ORDER BY income DESC LIMIT 10;");
        break;
      default:
        setSqlQuery('SELECT * FROM dataset LIMIT 10;');
    }
  };

  return (
    <div className="space-y-6">
      {!dataset ? (
        <div className="text-center py-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
            <CommandLineIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No dataset loaded</h3>
          <p className="mt-2 text-gray-500">
            Please upload a dataset to run SQL queries.
          </p>
        </div>
      ) : (
        <>
          {/* SQL Editor Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <CommandLineIcon className="h-5 w-5 mr-2 text-yellow-500" />
                SQL Query Editor
              </h2>
              <div className="flex space-x-3">
                <button
                  onClick={() => loadSampleQuery('basic')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded-lg"
                >
                  Basic
                </button>
                <button
                  onClick={() => loadSampleQuery('aggregate')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded-lg"
                >
                  Aggregate
                </button>
                <button
                  onClick={() => loadSampleQuery('filter')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded-lg"
                >
                  Filter
                </button>
                <button
                  onClick={() => loadSampleQuery('sort')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-800 py-1 px-3 rounded-lg"
                >
                  Sort
                </button>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Dataset Schema</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 max-h-40 overflow-y-auto p-2 border border-gray-200 rounded-lg bg-gray-50">
                {availableColumns.map((col) => (
                  <div 
                    key={col.name} 
                    className="text-xs p-2 bg-white border border-gray-200 rounded-md"
                    title={`${col.name}: ${col.type}`}
                  >
                    <div className="font-medium text-gray-900 truncate">{col.name}</div>
                    <div className="text-gray-500">{col.type}</div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">SQL Query</label>
              <textarea
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                rows={8}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your SQL query here..."
                disabled={isLoading}
              />
            </div>
            
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-500">
                Use <code className="bg-gray-100 px-1.5 py-0.5 rounded">dataset</code> as the table name
              </div>
              <button
                onClick={executeQuery}
                disabled={isLoading}
                className={`flex items-center px-6 py-2 border border-transparent text-base font-medium rounded-lg shadow-sm text-white ${
                  isLoading ? 'bg-yellow-400 cursor-not-allowed' : 'bg-yellow-600 hover:bg-yellow-700'
                }`}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Executing...
                  </>
                ) : (
                  <>
                    <ArrowPathIcon className="h-4 w-4 mr-2" />
                    Execute Query
                  </>
                )}
              </button>
            </div>
          </motion.div>

          {/* Query Results */}
          {queryResult && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center">
                  <TableCellsIcon className="h-5 w-5 mr-2 text-green-500" />
                  Query Results
                </h2>
                <div className="flex items-center text-sm">
                  <span className="text-gray-500 mr-4">{queryResult.row_count} rows</span>
                  {executionTime && (
                    <span className="text-gray-500">Execution time: {executionTime}</span>
                  )}
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      {queryResult.columns.map((col, index) => (
                        <th key={index}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {queryResult.data.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {queryResult.columns.map((col, colIndex) => (
                          <td key={colIndex} className="text-gray-900">{row[col]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-4 flex justify-end">
                <button className="flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium">
                  <DocumentTextIcon className="h-4 w-4 mr-1" />
                  Export Results
                </button>
              </div>
            </motion.div>
          )}

          {/* Query History */}
          {queryHistory.length > 0 && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Queries</h2>
              
              <div className="space-y-3">
                {queryHistory.map((item) => (
                  <div 
                    key={item.id} 
                    className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSqlQuery(item.query)}
                  >
                    <div className="flex justify-between">
                      <code className="text-sm text-gray-800 font-mono truncate max-w-xs sm:max-w-md md:max-w-lg lg:max-w-xl">
                        {item.query}
                      </code>
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
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

export default SqlTab;