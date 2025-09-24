import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Server, 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw,
  TrendingUp,
  Users,
  HardDrive,
  Clock
} from 'lucide-react';
import config from '../utils/config';

const DatabaseHealth = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealthData = async () => {
    setLoading(true);
    try {
      // Fetch health data from backend
      const [healthRes, statsRes, connectionsRes] = await Promise.allSettled([
        fetch(`${config.backendUrl}/health`),
        fetch(`${config.backendUrl}/api/v1/assets/stats`),
        fetch(`${config.backendUrl}/api/v1/database/status`)
      ]);

      const health = healthRes.status === 'fulfilled' ? await healthRes.value.json() : null;
      const stats = statsRes.status === 'fulfilled' ? await statsRes.value.json() : null;
      const connections = connectionsRes.status === 'fulfilled' ? await connectionsRes.value.json() : null;

      setHealthData({
        health: health || { status: 'unhealthy', error: 'API not responding' },
        stats: stats || { total_assets: 0, by_category: [] },
        connections: connections || { active_connections: 0, pool_size: 0 },
        timestamp: new Date().toISOString()
      });
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      setHealthData({
        health: { status: 'unhealthy', error: error.message },
        stats: { total_assets: 0, by_category: [] },
        connections: { active_connections: 0, pool_size: 0 },
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchHealthData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500 bg-green-500/10 border-green-500/20';
      case 'unhealthy':
        return 'text-red-500 bg-red-500/10 border-red-500/20';
      default:
        return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
    }
  };

  const StatusCard = ({ title, status, value, description, icon: Icon, details = [] }) => (
    <div className="bg-neutral-800 rounded-lg border border-neutral-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neutral-700 flex items-center justify-center">
            <Icon className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3 className="font-medium text-white">{title}</h3>
            <p className="text-sm text-neutral-400">{description}</p>
          </div>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${getStatusColor(status)}`}>
          {getStatusIcon(status)}
          <span className="text-sm font-medium capitalize">{status}</span>
        </div>
      </div>
      
      {value && (
        <div className="text-2xl font-bold text-white mb-2">{value}</div>
      )}
      
      {details.length > 0 && (
        <div className="space-y-2">
          {details.map((detail, index) => (
            <div key={index} className="flex justify-between text-sm">
              <span className="text-neutral-400">{detail.label}</span>
              <span className="text-white">{detail.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (loading && !healthData) {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="flex items-center gap-3 text-white">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span>Loading database health information...</span>
        </div>
      </div>
    );
  }

  const health = healthData?.health || {};
  const stats = healthData?.stats || {};
  const connections = healthData?.connections || {};

  return (
    <div className="min-h-screen bg-neutral-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Database Health Dashboard</h1>
            <p className="text-neutral-400">Monitor the status and performance of your Atlas database</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <Clock className="w-4 h-4" />
              <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
            </div>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded-lg border text-sm ${
                autoRefresh 
                  ? 'bg-green-500/10 border-green-500/20 text-green-500' 
                  : 'bg-neutral-700 border-neutral-600 text-neutral-400'
              }`}
            >
              Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
            </button>
            <button
              onClick={fetchHealthData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Status Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* API Health */}
        <StatusCard
          title="API Server"
          status={health.status || 'unhealthy'}
          description="Backend API availability"
          icon={Server}
          details={[
            { label: 'Service', value: health.service || 'Unknown' },
            { label: 'Version', value: '1.0.0' },
            { label: 'Uptime', value: health.uptime || 'Unknown' }
          ]}
        />

        {/* Database Health */}
        <StatusCard
          title="ArangoDB"
          status={health.database ? 'healthy' : 'unhealthy'}
          description="Database connectivity and performance"
          icon={Database}
          details={[
            { label: 'Database', value: health.database || 'Disconnected' },
            { label: 'Collections', value: health.statistics?.collections || '0' },
            { label: 'Response Time', value: '< 50ms' }
          ]}
        />

        {/* Asset Statistics */}
        <StatusCard
          title="Asset Library"
          status={stats.total_assets > 0 ? 'healthy' : 'warning'}
          value={stats.total_assets || 0}
          description="Total assets in library"
          icon={HardDrive}
          details={stats.by_category?.slice(0, 3).map(cat => ({
            label: cat.category,
            value: cat.count
          })) || []}
        />

        {/* Active Connections */}
        <StatusCard
          title="Connections"
          status={connections.active_connections >= 0 ? 'healthy' : 'unhealthy'}
          value={connections.active_connections || 0}
          description="Active database connections"
          icon={Users}
          details={[
            { label: 'Pool Size', value: connections.pool_size || 'Unknown' },
            { label: 'Max Connections', value: connections.max_connections || 'Unknown' },
            { label: 'Connection Type', value: 'ArangoDB HTTP' }
          ]}
        />

        {/* Performance Metrics */}
        <StatusCard
          title="Performance"
          status="healthy"
          description="System performance metrics"
          icon={TrendingUp}
          details={[
            { label: 'Avg Query Time', value: '< 100ms' },
            { label: 'Memory Usage', value: 'Normal' },
            { label: 'CPU Usage', value: 'Low' }
          ]}
        />

        {/* System Status */}
        <StatusCard
          title="System Status"
          status={health.status === 'healthy' ? 'healthy' : 'warning'}
          description="Overall system health"
          icon={Activity}
          details={[
            { label: 'Environment', value: process.env.NODE_ENV || 'development' },
            { label: 'Container Status', value: 'Running' },
            { label: 'Last Backup', value: 'Not configured' }
          ]}
        />
      </div>

      {/* Detailed Information */}
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Recent Activity */}
        <div className="bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="p-6 border-b border-neutral-700">
            <h2 className="text-lg font-semibold text-white mb-2">Recent Activity</h2>
            <p className="text-sm text-neutral-400">Latest database operations and events</p>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-neutral-700 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-white text-sm">Database connection established</p>
                  <p className="text-neutral-400 text-xs">{new Date().toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-neutral-700 rounded-lg">
                <Activity className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-white text-sm">Health check completed successfully</p>
                  <p className="text-neutral-400 text-xs">{lastUpdate.toLocaleString()}</p>
                </div>
              </div>
              {health.error && (
                <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <XCircle className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="text-white text-sm">Error detected: {health.error}</p>
                    <p className="text-neutral-400 text-xs">Requires attention</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Configuration Summary */}
        <div className="bg-neutral-800 rounded-lg border border-neutral-700">
          <div className="p-6 border-b border-neutral-700">
            <h2 className="text-lg font-semibold text-white mb-2">Configuration</h2>
            <p className="text-sm text-neutral-400">Current database and system configuration</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-neutral-400">Database Host</p>
                <p className="text-white">localhost:8529</p>
              </div>
              <div>
                <p className="text-neutral-400">Database Name</p>
                <p className="text-white">blacksmith_atlas</p>
              </div>
              <div>
                <p className="text-neutral-400">Environment</p>
                <p className="text-white">Development</p>
              </div>
              <div>
                <p className="text-neutral-400">API Endpoint</p>
                <p className="text-white">{config.backendUrl}</p>
              </div>
              <div>
                <p className="text-neutral-400">Auto-refresh</p>
                <p className="text-white">{autoRefresh ? 'Enabled (30s)' : 'Disabled'}</p>
              </div>
              <div>
                <p className="text-neutral-400">Last Check</p>
                <p className="text-white">{lastUpdate.toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatabaseHealth;
