import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion } from 'framer-motion';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ReviewTab from './tabs/ReviewTab';
import CleaningTab from './tabs/CleaningTab';
import ChartsTab from './tabs/ChartsTab';
import ChatbotTab from './tabs/ChatbotTab';
import ModelTab from './tabs/ModelTab';
import ExportTab from './tabs/ExportTab';
import SqlTab from './tabs/SqlTab';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('review');
  const [dataset, setDataset] = useState(null);

  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen} 
          setIsOpen={setSidebarOpen} 
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />
        
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <Header 
            sidebarOpen={sidebarOpen} 
            setSidebarOpen={setSidebarOpen}
            dataset={dataset}
            setDataset={setDataset}
          />
          
          {/* Main Content */}
          <motion.main 
            className="flex-1 overflow-y-auto p-4 md:p-6 bg-gradient-to-br from-gray-50 to-gray-100"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Routes>
              <Route path="/" element={<ReviewTab dataset={dataset} />} />
              <Route path="/review" element={<ReviewTab dataset={dataset} />} />
              <Route path="/cleaning" element={<CleaningTab dataset={dataset} setDataset={setDataset} />} />
              <Route path="/charts" element={<ChartsTab dataset={dataset} />} />
              <Route path="/chatbot" element={<ChatbotTab dataset={dataset} />} />
              <Route path="/model" element={<ModelTab dataset={dataset} />} />
              <Route path="/export" element={<ExportTab dataset={dataset} />} />
              <Route path="/sql" element={<SqlTab dataset={dataset} />} />
            </Routes>
          </motion.main>
        </div>
      </div>
    </Router>
  );
}

export default App;