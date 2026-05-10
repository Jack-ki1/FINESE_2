import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowDownTrayIcon, 
  DocumentTextIcon, 
  ChartBarIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';

const ExportTab = ({ dataset }) => {
  const [exportFormat, setExportFormat] = useState('csv');
  const [includeVisualizations, setIncludeVisualizations] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [exportHistory, setExportHistory] = useState([
    { id: 1, format: 'CSV', fileName: 'dataset_export.csv', date: '2023-10-15', size: '2.4 MB' },
    { id: 2, format: 'Excel', fileName: 'dataset_analysis.xlsx', date: '2023-10-14', size: '3.1 MB' },
  ]);

  const exportFormats = [
    { id: 'csv', name: 'CSV', description: 'Comma-separated values' },
    { id: 'excel', name: 'Excel', description: 'Microsoft Excel spreadsheet' },
    { id: 'json', name: 'JSON', description: 'JavaScript Object Notation' },
    { id: 'parquet', name: 'Parquet', description: 'Column-oriented data format' },
  ];

  const exportDataset = () => {
    setIsExporting(true);
    
    // Simulate export process
    setTimeout(() => {
      // Create a mock export history item
      const newExport = {
        id: exportHistory.length + 1,
        format: exportFormat.toUpperCase(),
        fileName: `dataset_export_${Date.now()}.${exportFormat}`,
        date: new Date().toISOString().split('T')[0],
        size: `${(Math.random() * 5).toFixed(1)} MB`
      };
      
      setExportHistory([newExport, ...exportHistory]);
      setIsExporting(false);
      
      alert(`Dataset exported as ${exportFormat.toUpperCase()} format!`);
    }, 2000);
  };

  const exportReport = () => {
    setIsExporting(true);
    
    // Simulate report export
    setTimeout(() => {
      const newExport = {
        id: exportHistory.length + 1,
        format: 'REPORT',
        fileName: `analysis_report_${Date.now()}.pdf`,
        date: new Date().toISOString().split('T')[0],
        size: '1.2 MB'
      };
      
      setExportHistory([newExport, ...exportHistory]);
      setIsExporting(false);
      
      alert('Analysis report exported successfully!');
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {!dataset ? (
        <div className="text-center py-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
            <ArrowDownTrayIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No dataset loaded</h3>
          <p className="mt-2 text-gray-500">
            Please upload a dataset to export.
          </p>
        </div>
      ) : (
        <>
          {/* Export Options Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <ArrowDownTrayIcon className="h-5 w-5 mr-2 text-green-500" />
              Export Options
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Dataset Export</h3>
                
                <div className="space-y-4">
                  {exportFormats.map((format) => (
                    <div 
                      key={format.id}
                      className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                        exportFormat === format.id
                          ? 'border-green-500 bg-green-50 ring-2 ring-green-200'
                          : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setExportFormat(format.id)}
                    >
                      <div className="flex items-start">
                        <input
                          type="radio"
                          checked={exportFormat === format.id}
                          onChange={() => setExportFormat(format.id)}
                          className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500"
                        />
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-gray-900">{format.name}</h4>
                          <p className="text-sm text-gray-500">{format.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <div className="flex items-center pt-2">
                    <input
                      type="checkbox"
                      id="includeViz"
                      checked={includeVisualizations}
                      onChange={(e) => setIncludeVisualizations(e.target.checked)}
                      className="h-4 w-4 text-green-600 rounded focus:ring-green-500"
                    />
                    <label htmlFor="includeViz" className="ml-2 text-sm text-gray-700">
                      Include visualizations in report
                    </label>
                  </div>
                </div>
                
                <div className="mt-6 flex space-x-4">
                  <button
                    onClick={exportDataset}
                    disabled={isExporting}
                    className={`flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white ${
                      isExporting ? 'bg-green-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {isExporting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Exporting...
                      </>
                    ) : (
                      <>
                        <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                        Export Dataset
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={exportReport}
                    disabled={isExporting}
                    className={`flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white ${
                      isExporting ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
                    }`}
                  >
                    {isExporting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Exporting...
                      </>
                    ) : (
                      <>
                        <DocumentTextIcon className="h-5 w-5 mr-2" />
                        Export Report
                      </>
                    )}
                  </button>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Export Bundle</h3>
                
                <div className="border border-gray-200 rounded-lg p-5 bg-gray-50">
                  <div className="flex items-center mb-4">
                    <ArchiveBoxIcon className="h-6 w-6 text-gray-500 mr-3" />
                    <h4 className="font-medium text-gray-900">Multi-format Bundle</h4>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-4">
                    Export your dataset in multiple formats plus a comprehensive analysis report in a single ZIP file.
                  </p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm">
                      <input type="checkbox" className="h-4 w-4 text-blue-600 rounded mr-2" defaultChecked />
                      <span>CSV Format</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <input type="checkbox" className="h-4 w-4 text-blue-600 rounded mr-2" defaultChecked />
                      <span>Excel Format</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <input type="checkbox" className="h-4 w-4 text-blue-600 rounded mr-2" />
                      <span>JSON Format</span>
                    </div>
                    <div className="flex items-center text-sm">
                      <input type="checkbox" className="h-4 w-4 text-blue-600 rounded mr-2" defaultChecked />
                      <span>Analysis Report</span>
                    </div>
                  </div>
                  
                  <button className="w-full py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Create Bundle
                  </button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Export History Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <ChartBarIcon className="h-5 w-5 mr-2 text-blue-500" />
              Export History
            </h2>
            
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Format</th>
                    <th>File Name</th>
                    <th>Date</th>
                    <th>Size</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {exportHistory.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                          {item.format}
                        </span>
                      </td>
                      <td className="font-medium text-gray-900">{item.fileName}</td>
                      <td>{item.date}</td>
                      <td>{item.size}</td>
                      <td>
                        <button className="text-sm text-blue-600 hover:text-blue-900 font-medium">
                          Download
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
};

export default ExportTab;