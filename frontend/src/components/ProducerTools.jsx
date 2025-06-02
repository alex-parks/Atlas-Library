import React from 'react';
import { Calculator, Calendar, Users, TrendingUp, FileText, Clock } from 'lucide-react';

const ProducerTools = () => {
  return (
    <div className="p-6 bg-gray-900 min-h-full">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Producer Tools</h1>
        <p className="text-gray-400">Project management and analysis tools for VFX production</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-3 rounded-lg">
              <Calculator className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Active Projects</h3>
              <p className="text-2xl font-bold text-blue-400">12</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="bg-green-600 p-3 rounded-lg">
              <Users className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Team Members</h3>
              <p className="text-2xl font-bold text-green-400">45</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="bg-purple-600 p-3 rounded-lg">
              <TrendingUp className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Revenue (Q1)</h3>
              <p className="text-2xl font-bold text-purple-400">$2.4M</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="bg-orange-600 p-3 rounded-lg">
              <Clock className="text-white" size={24} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Avg. Delivery</h3>
              <p className="text-2xl font-bold text-orange-400">14 days</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Bid Analysis */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-blue-600 p-2 rounded-lg">
              <FileText className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Bid Analysis</h3>
          </div>
          <p className="text-gray-400 mb-4">AI-powered analysis of project bids and proposals</p>
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>

        {/* Project Estimator */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-green-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-600 p-2 rounded-lg">
              <Calculator className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Project Estimator</h3>
          </div>
          <p className="text-gray-400 mb-4">Calculate project timelines, costs, and resource requirements</p>
          <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>

        {/* Team Scheduler */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-purple-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-purple-600 p-2 rounded-lg">
              <Calendar className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Team Scheduler</h3>
          </div>
          <p className="text-gray-400 mb-4">Manage team schedules and project assignments</p>
          <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>

        {/* Revenue Analytics */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-orange-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-orange-600 p-2 rounded-lg">
              <TrendingUp className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Revenue Analytics</h3>
          </div>
          <p className="text-gray-400 mb-4">Track financial performance and project profitability</p>
          <button className="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>

        {/* Client Portal */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-indigo-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Users className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Client Portal</h3>
          </div>
          <p className="text-gray-400 mb-4">Manage client relationships and project communications</p>
          <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>

        {/* Reports Generator */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-red-500 transition-colors cursor-pointer">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-red-600 p-2 rounded-lg">
              <FileText className="text-white" size={20} />
            </div>
            <h3 className="text-lg font-semibold text-white">Reports Generator</h3>
          </div>
          <p className="text-gray-400 mb-4">Generate detailed project and financial reports</p>
          <button className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg transition-colors">
            Launch Tool
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        <div className="bg-gray-800 border border-gray-700 rounded-lg">
          <div className="p-4 space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-400">2 hours ago</span>
              <span className="text-white">Project "Cosmic Dawn" budget approved - $450K</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-gray-400">4 hours ago</span>
              <span className="text-white">New bid submitted for "City Chase" sequence</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <span className="text-gray-400">1 day ago</span>
              <span className="text-white">Team capacity updated: 3 new artists onboarded</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProducerTools;