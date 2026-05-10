import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  TableCellsIcon, 
  WrenchScrewdriverIcon, 
  ChartBarIcon, 
  ChatBubbleLeftRightIcon, 
  Cog6ToothIcon, 
  ArrowDownTrayIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Review', href: '/review', icon: TableCellsIcon },
  { name: 'Cleaning', href: '/cleaning', icon: WrenchScrewdriverIcon },
  { name: 'Charts', href: '/charts', icon: ChartBarIcon },
  { name: 'Chatbot', href: '/chatbot', icon: ChatBubbleLeftRightIcon },
  { name: 'Model', href: '/model', icon: Cog6ToothIcon },
  { name: 'Export', href: '/export', icon: ArrowDownTrayIcon },
  { name: 'SQL', href: '/sql', icon: CommandLineIcon },
];

const Sidebar = ({ isOpen, setIsOpen, activeTab, setActiveTab }) => {
  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <motion.aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-gray-900 pt-16 transition-transform duration-300 ease-in-out transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:static lg:inset-0`}
        initial={false}
        animate={{ x: isOpen ? 0 : -256 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex flex-col h-full">
          <nav className="mt-5 flex-1 px-2 pb-4 space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `${
                    isActive || activeTab === item.name.toLowerCase()
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  } group flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors duration-200`
                }
                onClick={() => setActiveTab(item.name.toLowerCase())}
              >
                <item.icon
                  className={`${
                    activeTab === item.name.toLowerCase() ? 'text-white' : 'text-gray-400 group-hover:text-gray-300'
                  } mr-3 h-6 w-6 flex-shrink-0`}
                  aria-hidden="true"
                />
                <span className="truncate">{item.name}</span>
              </NavLink>
            ))}
          </nav>
          
          {/* Sidebar footer */}
          <div className="p-4 border-t border-gray-800">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-2 rounded-lg">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-xs text-gray-400">Performance</p>
                <p className="text-sm font-medium text-white">Optimized</p>
              </div>
            </div>
          </div>
        </div>
      </motion.aside>
    </>
  );
};

export default Sidebar;