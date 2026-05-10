import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  ArrowsRightLeftIcon,
  FunnelIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import Plot from 'react-plotly.js';

const ChartsTab = ({ dataset }) => {
  const [chartType, setChartType] = useState('bar');
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [chartData, setChartData] = useState(null);
  const [availableColumns, setAvailableColumns] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Mock available columns for demonstration
  useEffect(() => {
    if (dataset) {
      setAvailableColumns([
        { name: 'id', type: 'int64', suggest_as: ['x_axis'] },
        { name: 'name', type: 'object', suggest_as: ['x_axis', 'group_by'] },
        { name: 'age', type: 'int64', suggest_as: ['x_axis', 'y_axis'] },
        { name: 'income', type: 'float64', suggest_as: ['x_axis', 'y_axis'] },
        { name: 'category', type: 'object', suggest_as: ['x_axis', 'group_by'] }
      ]);
      
      // Set defaults
      setXAxis('category');
      setYAxis('income');
    }
  }, [dataset]);

  const generateChart = () => {
    setIsLoading(true);
    
    // Simulate API call to generate chart
    setTimeout(() => {
      // Mock chart data based on type
      let data;
      switch(chartType) {
        case 'bar':
          data = {
            type: 'bar',
            x: ['Tech', 'Finance', 'Healthcare', 'Retail', 'Manufacturing'],
            y: [20, 14, 23, 18, 12],
            marker: { color: '#3b82f6' }
          };
          break;
        case 'line':
          data = {
            type: 'scatter',
            mode: 'lines+markers',
            x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            y: [10, 15, 13, 17, 19, 22],
            line: { color: '#10b981' }
          };
          break;
        case 'pie':
          data = {
            type: 'pie',
            labels: ['Tech', 'Finance', 'Healthcare', 'Retail'],
            values: [25, 30, 20, 25],
          };
          break;
        case 'scatter':
          data = {
            type: 'scatter',
            mode: 'markers',
            x: [1, 2, 3, 4, 5],
            y: [10, 11, 12, 13, 14],
            marker: { size: 12, color: '#8b5cf6' }
          };
          break;
        default:
          data = {
            type: 'bar',
            x: ['A', 'B', 'C'],
            y: [1, 3, 2],
            marker: { color: '#3b82f6' }
          };
      }
      
      setChartData({
        data: [data],
        layout: {
          title: `${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart`,
          autosize: true,
          margin: { t: 30, l: 50, r: 50, b: 50 }
        }
      });
      
      setIsLoading(false);
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {!dataset ? (
        <div className="text-center py-12">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-blue-100">
            <PhotoIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No dataset loaded</h3>
          <p className="mt-2 text-gray-500">
            Please upload a dataset to create charts and visualizations.
          </p>
        </div>
      ) : (
        <>
          {/* Chart Controls Card */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <ChartBarIcon className="h-5 w-5 mr-2 text-indigo-500" />
              Chart Builder
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chart Type</label>
                <select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white py-2 px-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bar">Bar Chart</option>
                  <option value="line">Line Chart</option>
                  <option value="pie">Pie Chart</option>
                  <option value="scatter">Scatter Plot</option>
                  <option value="histogram">Histogram</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">X-Axis</label>
                <select
                  value={xAxis}
                  onChange={(e) => setXAxis(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white py-2 px-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select column</option>
                  {availableColumns.map((col) => (
                    <option key={`x-${col.name}`} value={col.name}>{col.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Y-Axis</label>
                <select
                  value={yAxis}
                  onChange={(e) => setYAxis(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white py-2 px-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select column</option>
                  {availableColumns
                    .filter(col => col.type.includes('int') || col.type.includes('float'))
                    .map((col) => (
                      <option key={`y-${col.name}`} value={col.name}>{col.name}</option>
                    ))}
                </select>
              </div>
              
              <div className="flex items-end">
                <button
                  onClick={generateChart}
                  disabled={isLoading || !xAxis}
                  className={`w-full ${!xAxis ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'} text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center`}
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating...
                    </>
                  ) : (
                    <>
                      <FunnelIcon className="h-4 w-4 mr-2" />
                      Generate Chart
                    </>
                  )}
                </button>
              </div>
            </div>
            
            <div className="flex items-center text-sm text-gray-500">
              <ArrowsRightLeftIcon className="h-4 w-4 mr-1" />
              <span>Select columns and chart type, then click "Generate Chart"</span>
            </div>
          </motion.div>

          {/* Chart Visualization */}
          {chartData && (
            <motion.div 
              className="card p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h2 className="text-xl font-bold text-gray-900 mb-4">Visualization</h2>
              <div className="bg-white rounded-lg p-2">
                <Plot
                  data={chartData.data}
                  layout={chartData.layout}
                  config={{ displayModeBar: true, responsive: true }}
                  style={{ width: '100%', height: '500px' }}
                />
              </div>
            </motion.div>
          )}

          {/* Empty state when no chart generated */}
          {!chartData && !isLoading && (
            <motion.div 
              className="card p-12 text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-indigo-100">
                <ChartBarIcon className="h-8 w-8 text-indigo-600" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">No chart generated</h3>
              <p className="mt-2 text-gray-500 max-w-xl mx-auto">
                Select your chart parameters and click "Generate Chart" to visualize your data.
              </p>
              <div className="mt-6">
                <button
                  onClick={generateChart}
                  disabled={!xAxis}
                  className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${!xAxis ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                >
                  Generate Sample Chart
                </button>
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  );
};

export default ChartsTab;