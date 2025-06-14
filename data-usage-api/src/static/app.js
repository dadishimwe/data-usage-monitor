// Data Usage Monitor Dashboard JavaScript

class DataUsageMonitor {
    constructor() {
        this.apiBase = '/api';
        this.currentTab = 'dashboard';
        this.trendsChart = null;
        this.locations = [];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadLocations();
        await this.loadDashboard();
        this.showLoading(false);
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Header actions
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshCurrentTab();
        });

        document.getElementById('backupBtn').addEventListener('click', () => {
            this.createBackup();
        });

        // Dashboard controls
        document.getElementById('trendDays').addEventListener('change', (e) => {
            this.loadUsageTrends(parseInt(e.target.value));
        });

        // Data usage controls
        document.getElementById('filterBtn').addEventListener('click', () => {
            this.loadDailyUsage();
        });

        document.getElementById('addUsageBtn').addEventListener('click', () => {
            this.showModal('addUsageModal');
        });

        // Monthly summary controls
        document.getElementById('addMonthlyBtn').addEventListener('click', () => {
            this.showModal('addMonthlyModal');
        });

        // System controls
        document.getElementById('createBackupBtn').addEventListener('click', () => {
            this.createBackup();
        });

        document.getElementById('refreshBackupsBtn').addEventListener('click', () => {
            this.loadBackups();
        });

        // Modal controls
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.closeModal(modal.id);
            });
        });

        // Form submissions
        document.getElementById('addUsageForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addDailyUsage();
        });

        document.getElementById('addMonthlyForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addMonthlySummary();
        });

        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }

    async apiCall(endpoint, options = {}) {
        try {
            this.showLoading(true);
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            this.showToast('API call failed: ' + error.message, 'error');
            throw error;
        } finally {
            this.showLoading(false);
        }
    }

    async loadLocations() {
        try {
            this.locations = await this.apiCall('/data/locations');
            this.populateLocationSelects();
        } catch (error) {
            console.error('Failed to load locations:', error);
        }
    }

    populateLocationSelects() {
        const selects = [
            'locationFilter',
            'monthlyLocationFilter',
            'usageLocation',
            'monthlyLocation'
        ];

        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                // Clear existing options (except first one for filters)
                const isFilter = selectId.includes('Filter');
                select.innerHTML = isFilter ? '<option value="">All Locations</option>' : '<option value="">Select Location</option>';
                
                this.locations.forEach(location => {
                    const option = document.createElement('option');
                    option.value = location.id;
                    option.textContent = location.display_name;
                    select.appendChild(option);
                });
            }
        });
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update active content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;
        this.loadTabContent(tabName);
    }

    async loadTabContent(tabName) {
        switch (tabName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'data-usage':
                await this.loadDailyUsage();
                break;
            case 'monthly':
                await this.loadMonthlySummaries();
                break;
            case 'system':
                await this.loadSystemStatus();
                break;
        }
    }

    async loadDashboard() {
        try {
            const overview = await this.apiCall('/dashboard/overview');
            this.updateOverview(overview);

            const trends = await this.apiCall('/dashboard/usage-trends?days=30');
            this.updateTrendsChart(trends);

            this.updateTopLocations(overview.top_locations);
            
            const recentUpdates = await this.apiCall('/dashboard/recent-updates?limit=5');
            this.updateRecentUpdates(recentUpdates);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateOverview(data) {
        document.getElementById('totalLocations').textContent = data.total_locations;
        document.getElementById('totalRecords').textContent = data.total_records.toLocaleString();
        document.getElementById('recentActivity').textContent = data.recent_activity;
        
        const dateRange = data.date_range;
        if (dateRange.start && dateRange.end) {
            document.getElementById('dateRange').textContent = `${dateRange.start} to ${dateRange.end}`;
        } else {
            document.getElementById('dateRange').textContent = 'No data';
        }
    }

    updateTrendsChart(data) {
        const ctx = document.getElementById('trendsChart').getContext('2d');
        
        if (this.trendsChart) {
            this.trendsChart.destroy();
        }

        // Process data for chart
        const dates = [...new Set(data.map(item => item.date))].sort();
        const locations = [...new Set(data.map(item => item.display_name))];
        
        const datasets = locations.map((location, index) => {
            const locationData = dates.map(date => {
                const item = data.find(d => d.date === date && d.display_name === location);
                return item ? item.daily_total : 0;
            });

            return {
                label: location,
                data: locationData,
                borderColor: this.getChartColor(index),
                backgroundColor: this.getChartColor(index, 0.1),
                tension: 0.4,
                fill: false
            };
        });

        this.trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Usage (GB)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }

    getChartColor(index, alpha = 1) {
        const colors = [
            `rgba(37, 99, 235, ${alpha})`,
            `rgba(5, 150, 105, ${alpha})`,
            `rgba(217, 119, 6, ${alpha})`,
            `rgba(220, 38, 38, ${alpha})`,
            `rgba(147, 51, 234, ${alpha})`,
            `rgba(236, 72, 153, ${alpha})`,
            `rgba(6, 182, 212, ${alpha})`,
            `rgba(34, 197, 94, ${alpha})`
        ];
        return colors[index % colors.length];
    }

    updateTopLocations(locations) {
        const container = document.getElementById('topLocations');
        container.innerHTML = '';

        if (locations.length === 0) {
            container.innerHTML = '<p class="text-secondary">No recent data available</p>';
            return;
        }

        locations.forEach(location => {
            const item = document.createElement('div');
            item.className = 'location-item';
            item.innerHTML = `
                <div class="location-name">${location.display_name}</div>
                <div class="location-usage">${location.total_usage.toFixed(1)} GB</div>
            `;
            container.appendChild(item);
        });
    }

    updateRecentUpdates(updates) {
        const container = document.getElementById('recentUpdates');
        container.innerHTML = '';

        if (updates.length === 0) {
            container.innerHTML = '<p class="text-secondary">No recent updates</p>';
            return;
        }

        updates.forEach(update => {
            const item = document.createElement('div');
            item.className = 'update-item';
            item.innerHTML = `
                <div>
                    <div class="update-location">${update.display_name}</div>
                    <div class="update-date">${update.date} - ${update.usage_gb} GB</div>
                </div>
                <div class="update-time">${new Date(update.updated_at).toLocaleString()}</div>
            `;
            container.appendChild(item);
        });
    }

    async loadUsageTrends(days = 30) {
        try {
            const trends = await this.apiCall(`/dashboard/usage-trends?days=${days}`);
            this.updateTrendsChart(trends);
        } catch (error) {
            console.error('Failed to load usage trends:', error);
        }
    }

    async loadDailyUsage() {
        try {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const locationId = document.getElementById('locationFilter').value;

            let url = '/data/daily-usage';
            const params = new URLSearchParams();
            
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            if (locationId) params.append('location_id', locationId);
            
            if (params.toString()) {
                url += '?' + params.toString();
            }

            const data = await this.apiCall(url);
            this.updateUsageTable(data);
        } catch (error) {
            console.error('Failed to load daily usage:', error);
        }
    }

    updateUsageTable(data) {
        const tbody = document.querySelector('#usageTable tbody');
        tbody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.date}</td>
                <td>${item.display_name}</td>
                <td>${item.usage_gb}</td>
                <td>${new Date(item.updated_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="monitor.deleteUsage(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadMonthlySummaries() {
        try {
            const locationId = document.getElementById('monthlyLocationFilter').value;
            let url = '/data/monthly-summary';
            
            if (locationId) {
                url += `?location_id=${locationId}`;
            }

            const data = await this.apiCall(url);
            this.updateMonthlySummaryTable(data);
        } catch (error) {
            console.error('Failed to load monthly summaries:', error);
        }
    }

    updateMonthlySummaryTable(data) {
        const tbody = document.querySelector('#monthlyTable tbody');
        tbody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.period_start} to ${item.period_end}</td>
                <td>${item.display_name}</td>
                <td>${item.total_usage_gb}</td>
                <td>${item.manual_entry ? 'Yes' : 'No'}</td>
                <td>${new Date(item.updated_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="monitor.deleteMonthlySummary(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadSystemStatus() {
        try {
            const status = await this.apiCall('/system/status');
            this.updateSystemStatus(status);

            const dbInfo = await this.apiCall('/system/database-info');
            this.updateDatabaseInfo(dbInfo);

            await this.loadBackups();
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }

    updateSystemStatus(status) {
        document.getElementById('cpuUsage').textContent = `${status.cpu_percent}%`;
        document.getElementById('memoryUsage').textContent = `${status.memory.percent}% (${status.memory.available_gb}/${status.memory.total_gb} GB)`;
        document.getElementById('diskUsage').textContent = `${status.disk.percent}% (${status.disk.free_gb}/${status.disk.total_gb} GB free)`;
        document.getElementById('temperature').textContent = `${status.temperature_c}°C`;
        document.getElementById('uptime').textContent = `${status.uptime_days}d ${status.uptime_hours}h`;
        document.getElementById('dbSize').textContent = `${status.database_size_mb} MB`;
    }

    updateDatabaseInfo(info) {
        const container = document.getElementById('databaseInfo');
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${info.table_counts.locations}</div>
                    <div class="stat-label">Locations</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${info.table_counts.daily_usage.toLocaleString()}</div>
                    <div class="stat-label">Daily Records</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${info.table_counts.monthly_summaries}</div>
                    <div class="stat-label">Monthly Summaries</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${info.database_file.size_mb} MB</div>
                    <div class="stat-label">Database Size</div>
                </div>
            </div>
        `;
    }

    async loadBackups() {
        try {
            const data = await this.apiCall('/system/backups');
            this.updateBackupsList(data.backups);
        } catch (error) {
            console.error('Failed to load backups:', error);
        }
    }

    updateBackupsList(backups) {
        const container = document.getElementById('backupsList');
        container.innerHTML = '';

        if (backups.length === 0) {
            container.innerHTML = '<p class="text-secondary">No backups found</p>';
            return;
        }

        backups.forEach(backup => {
            const item = document.createElement('div');
            item.className = 'backup-item';
            item.innerHTML = `
                <div>
                    <div class="backup-name">${backup.filename}</div>
                    <div class="backup-size">${backup.size_mb} MB - ${new Date(backup.created).toLocaleString()}</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    async addDailyUsage() {
        try {
            const formData = {
                date: document.getElementById('usageDate').value,
                location_id: parseInt(document.getElementById('usageLocation').value),
                usage_gb: parseFloat(document.getElementById('usageAmount').value)
            };

            await this.apiCall('/data/daily-usage', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showToast('Daily usage added successfully', 'success');
            this.closeModal('addUsageModal');
            document.getElementById('addUsageForm').reset();
            
            if (this.currentTab === 'data-usage') {
                await this.loadDailyUsage();
            }
        } catch (error) {
            console.error('Failed to add daily usage:', error);
        }
    }

    async addMonthlySummary() {
        try {
            const formData = {
                period_start: document.getElementById('monthlyPeriodStart').value,
                period_end: document.getElementById('monthlyPeriodEnd').value,
                location_id: parseInt(document.getElementById('monthlyLocation').value),
                total_usage_gb: parseFloat(document.getElementById('monthlyTotal').value)
            };

            await this.apiCall('/data/monthly-summary', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            this.showToast('Monthly summary added successfully', 'success');
            this.closeModal('addMonthlyModal');
            document.getElementById('addMonthlyForm').reset();
            
            if (this.currentTab === 'monthly') {
                await this.loadMonthlySummaries();
            }
        } catch (error) {
            console.error('Failed to add monthly summary:', error);
        }
    }

    async deleteUsage(id) {
        if (!confirm('Are you sure you want to delete this usage record?')) {
            return;
        }

        try {
            await this.apiCall(`/data/daily-usage/${id}`, {
                method: 'DELETE'
            });

            this.showToast('Usage record deleted successfully', 'success');
            await this.loadDailyUsage();
        } catch (error) {
            console.error('Failed to delete usage record:', error);
        }
    }

    async deleteMonthlySummary(id) {
        if (!confirm('Are you sure you want to delete this monthly summary?')) {
            return;
        }

        try {
            await this.apiCall(`/data/monthly-summary/${id}`, {
                method: 'DELETE'
            });

            this.showToast('Monthly summary deleted successfully', 'success');
            await this.loadMonthlySummaries();
        } catch (error) {
            console.error('Failed to delete monthly summary:', error);
        }
    }

    async createBackup() {
        try {
            const result = await this.apiCall('/system/backup', {
                method: 'POST'
            });

            this.showToast(`Backup created successfully: ${result.backup_file}`, 'success');
            
            if (this.currentTab === 'system') {
                await this.loadBackups();
            }
        } catch (error) {
            console.error('Failed to create backup:', error);
        }
    }

    refreshCurrentTab() {
        this.loadTabContent(this.currentTab);
    }

    showModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }

    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'block' : 'none';
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div>${message}</div>
        `;

        document.getElementById('toastContainer').appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize the application
const monitor = new DataUsageMonitor();

// Make functions available globally for onclick handlers
window.monitor = monitor;

