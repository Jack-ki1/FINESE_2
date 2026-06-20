/**
 * FINESE2 Dashboard - API Client
 * Handles all communication with the Flask backend
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.currentDataset = null;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options
        };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: response.statusText }));
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // ===== DATA ENDPOINTS =====
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.request('/api/data/upload', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }

    async getDataInfo() {
        return this.request('/api/data/info');
    }

    async getDataSample(n = 100) {
        // Use /api/data/info which returns preview data
        return this.request('/api/data/info');
    }

    async loadSampleDataset(name) {
        return this.request(`/api/data/sample-dataset/${name}`, { method: 'POST' });
    }

    async exportData(format = 'csv') {
        // Direct navigation for file download
        window.location.href = `/api/data/export/${format}`;
        return null;
    }

    // ===== EDA ENDPOINTS =====
    async getProfile() {
        return this.request('/api/eda/profile');
    }

    async getDistribution(column) {
        return this.request(`/api/eda/distribution/${encodeURIComponent(column)}`);
    }

    async getCorrelation(method = 'pearson') {
        return this.request(`/api/eda/correlation?method=${method}`);
    }

    async getMissingValues() {
        return this.request('/api/eda/missing');
    }

    // ===== CLEANING ENDPOINTS =====
    async getCleaningRecommendations() {
        return this.request('/api/cleaning/recommendations');
    }

    async handleMissing(strategy, columns) {
        return this.request('/api/cleaning/missing', {
            method: 'POST',
            body: JSON.stringify({ strategy, columns })
        });
    }

    async handleOutliers(method, columns) {
        return this.request('/api/cleaning/outliers', {
            method: 'POST',
            body: JSON.stringify({ method, columns })
        });
    }

    async autoClean(aggressive = false) {
        return this.request('/api/cleaning/auto', {
            method: 'POST',
            body: JSON.stringify({ aggressive })
        });
    }

    // ===== VISUALIZATION ENDPOINTS =====
    async createChart(chartType, config) {
        return this.request(`/api/viz/${chartType}`, {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    // ===== ANALYSIS ENDPOINTS =====
    async getSummaryStats() {
        return this.request('/api/analysis/summary');
    }

    async hypothesisTest(testType, config) {
        return this.request('/api/analysis/hypothesis-test', {
            method: 'POST',
            body: JSON.stringify({ test_type: testType, ...config })
        });
    }

    async correlationAnalysis(columns, method) {
        return this.request('/api/analysis/correlation', {
            method: 'POST',
            body: JSON.stringify({ columns, method })
        });
    }

    async regressionAnalysis(dependent, independent) {
        return this.request('/api/analysis/regression', {
            method: 'POST',
            body: JSON.stringify({ dependent, independent })
        });
    }

    // ===== MODELING ENDPOINTS =====
    async trainModels(targetCol, problemType, models) {
        return this.request('/api/modeling/train', {
            method: 'POST',
            body: JSON.stringify({ target_col: targetCol, problem_type: problemType, models })
        });
    }

    async performClustering(features, algorithm, nClusters) {
        return this.request('/api/modeling/cluster', {
            method: 'POST',
            body: JSON.stringify({ features, algorithm, n_clusters: nClusters })
        });
    }

    // ===== MLOPS ENDPOINTS =====
    async getExperiments() {
        return this.request('/api/mlops/experiments');
    }

    async getLeaderboard(problemType) {
        return this.request(`/api/mlops/leaderboard?problem_type=${problemType || ''}`);
    }

    async getModelRegistry() {
        return this.request('/api/mlops/models');
    }

    async compareRuns(runIds) {
        return this.request('/api/mlops/compare', {
            method: 'POST',
            body: JSON.stringify({ run_ids: runIds })
        });
    }

    // ===== REPORT ENDPOINTS =====
    async generateReport(format, title) {
        return this.request(`/api/reports/generate/${format}`, {
            method: 'POST',
            body: JSON.stringify({ title })
        });
    }

    // ===== AI ENDPOINTS =====
    async configureAI(config) {
        return this.request('/api/ai/config', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    async chatWithAI(message, history) {
        return this.request('/api/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message, history })
        });
    }

    async validateAIConfig(config) {
        return this.request('/api/ai/validate', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    // ===== UTILITY =====
    async getStatus() {
        return this.request('/api/system/status');
    }
}

// Global API instance
const api = new APIClient();
