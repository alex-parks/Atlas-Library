import React, { useState } from 'react';
import { Bot, Image, Wand2, Sparkles, Upload, Download, Play, Pause, Settings } from 'lucide-react';

const AITools = () => {
  const [activeJobs, setActiveJobs] = useState([
    { id: 1, name: "Background Extension", progress: 75, status: "processing" },
    { id: 2, name: "Character Removal", progress: 100, status: "completed" },
    { id: 3, name: "Style Transfer", progress: 45, status: "processing" }
  ]);

  return (
    <div className="p-6 bg-neutral-900 min-h-full">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">AI Tools</h1>
        <p className="text-neutral-400">Powered by ComfyUI - Advanced AI workflows for VFX production</p>
      </div>

      {/* AI Status Bar */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-4 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-400 font-medium">ComfyUI Connected</span>
            </div>
            <div className="text-neutral-400">|</div>
            <div className="text-neutral-400">GPU Usage: 34%</div>
            <div className="text-neutral-400">|</div>
            <div className="text-neutral-400">Queue: 3 jobs</div>
          </div>
          <button className="bg-neutral-700 hover:bg-neutral-600 px-4 py-2 rounded-lg flex items-center gap-2 text-white">
            <Settings size={18} />
            Configure
          </button>
        </div>
      </div>

      {/* AI Tool Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Image Processing Tools */}
        <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Image className="text-white" size={20} />
            </div>
            <h3 className="text-xl font-semibold text-white">Image Processing</h3>
          </div>

          <div className="space-y-4">
            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Background Extension</h4>
                <div className="text-blue-400 text-sm">Stable Diffusion</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Extend backgrounds seamlessly using AI inpainting</p>
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>

            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Object Removal</h4>
                <div className="text-green-400 text-sm">LaMa</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Remove unwanted objects from footage</p>
              <button className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>

            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Upscaling</h4>
                <div className="text-purple-400 text-sm">Real-ESRGAN</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Enhance image resolution with AI upscaling</p>
              <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>
          </div>
        </div>

        {/* Creative Tools */}
        <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-purple-600 p-2 rounded-lg">
              <Wand2 className="text-white" size={20} />
            </div>
            <h3 className="text-xl font-semibold text-white">Creative Tools</h3>
          </div>

          <div className="space-y-4">
            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Style Transfer</h4>
                <div className="text-orange-400 text-sm">ControlNet</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Apply artistic styles to images and footage</p>
              <button className="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>

            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Concept Generation</h4>
                <div className="text-pink-400 text-sm">SDXL</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Generate concept art and mood boards</p>
              <button className="w-full bg-pink-600 hover:bg-pink-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>

            <div className="bg-neutral-700 rounded-lg p-4 hover:bg-neutral-600 transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white font-medium">Texture Synthesis</h4>
                <div className="text-cyan-400 text-sm">Custom</div>
              </div>
              <p className="text-neutral-400 text-sm mb-3">Create seamless textures from samples</p>
              <button className="w-full bg-cyan-600 hover:bg-cyan-700 text-white py-2 rounded text-sm">
                Launch Tool
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Job Queue */}
      <div className="bg-neutral-800 border border-neutral-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-white">Job Queue</h3>
          <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 text-white">
            <Upload size={18} />
            New Job
          </button>
        </div>

        <div className="space-y-4">
          {activeJobs.map((job) => (
            <div key={job.id} className="bg-neutral-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    job.status === 'completed' ? 'bg-green-500' : 
                    job.status === 'processing' ? 'bg-blue-500 animate-pulse' : 
                    'bg-neutral-500'
                  }`}></div>
                  <h4 className="text-white font-medium">{job.name}</h4>
                </div>
                <div className="flex items-center gap-2">
                  {job.status === 'processing' && (
                    <button className="text-orange-400 hover:text-orange-300">
                      <Pause size={16} />
                    </button>
                  )}
                  {job.status === 'completed' && (
                    <button className="text-green-400 hover:text-green-300">
                      <Download size={16} />
                    </button>
                  )}
                </div>
              </div>

              <div className="w-full bg-neutral-600 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    job.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${job.progress}%` }}
                ></div>
              </div>

              <div className="flex justify-between text-sm text-neutral-400">
                <span>{job.status === 'completed' ? 'Completed' : 'Processing...'}</span>
                <span>{job.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AITools;