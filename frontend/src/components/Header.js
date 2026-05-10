import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bars3Icon, MagnifyingGlassIcon, BellIcon, UserCircleIcon, UploadIcon } from '@heroicons/react/24/outline';

const Header = ({ sidebarOpen, setSidebarOpen, dataset, setDataset }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileName, setFileName] = useState('');

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 95) {
          clearInterval(interval);
          return 95;
        }
        return prev + 5;
      });
    }, 200);

    // Simulate API call to upload dataset
    setTimeout(() => {
      clearInterval(interval);
      setUploadProgress(100);
      
      // Simulate setting the dataset
      setDataset({
        id: `ds_${Date.now()}`,
        name: file.name,
        rows: Math.floor(Math.random() * 10000) + 1000,
        columns: Math.floor(Math.random() * 50) + 5,
        size: (file.size / (1024 * 1024)).toFixed(2)
      });
      
      setIsUploading(false);
      
      // Reset after showing completion
      setTimeout(() => {
        setUploadProgress(0);
        setFileName('');
      }, 2000);
    }, 3000);
  };

  return (
    <motion.header 
      className="sticky top-0 z-10 bg-white shadow-sm"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center">
          <button
            type="button"
            className="mr-3 text-gray-500 hover:text-gray-700 focus:outline-none lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex items-center">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-2 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-3">
              <h1 className="text-xl font-bold text-gray-900">FINESE</h1>
              <p className="text-xs text-gray-500">Smart Data Explorer Pro</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search..."
            />
          </div>
          
          <button className="p-1 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100">
            <BellIcon className="h-6 w-6" />
          </button>
          
          {/* File Upload */}
          <div className="relative group">
            <label className="flex items-center cursor-pointer">
              <input 
                type="file" 
                className="hidden" 
                accept=".csv,.xlsx,.xls,.json"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
              <div className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200">
                <UploadIcon className="h-5 w-5 mr-1" />
                <span className="text-sm font-medium">Upload</span>
              </div>
            </label>
            
            {/* Progress bar - shown during upload */}
            {isUploading && (
              <motion.div 
                className="absolute bottom-full left-0 right-0 mb-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="text-xs text-gray-600 mb-1 text-center">{fileName}</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </motion.div>
            )}
          </div>
          
          <div className="flex items-center">
            <UserCircleIcon className="h-8 w-8 text-gray-500" />
            <span className="ml-2 text-sm font-medium text-gray-700 hidden md:block">Admin</span>
          </div>
        </div>
      </div>
      
      {/* Status Bar */}
      <div className="px-4 pb-2 sm:px-6">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full ${dataset ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
              {dataset ? `Dataset: ${dataset.name}` : 'No Dataset Loaded'}
            </span>
            {dataset && (
              <span className="text-gray-500">{dataset.rows.toLocaleString()} rows × {dataset.columns} cols</span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">Status:</span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-green-100 text-green-800">
              Operational
            </span>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;