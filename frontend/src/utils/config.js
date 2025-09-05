/**
 * Blacksmith Atlas - Frontend Configuration Utility
 * ==============================================
 * 
 * Manages configuration loading and caching for the frontend.
 * Fetches configuration from the backend API and provides easy access.
 * 
 * @author Blacksmith VFX
 * @version 1.0
 */

import { useState, useEffect } from 'react';

class AtlasConfig {
  constructor() {
    this._config = null;
    this._loading = false;
    this._loadPromise = null;
  }

  /**
   * Get the backend API URL from environment or default
   */
  get backendUrl() {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Load configuration from backend API
   */
  async load(force = false) {
    // Return cached config if available and not forcing reload
    if (this._config && !force) {
      return this._config;
    }

    // If already loading, return the existing promise
    if (this._loading && this._loadPromise) {
      return this._loadPromise;
    }

    this._loading = true;
    this._loadPromise = this._fetchConfig();

    try {
      const config = await this._loadPromise;
      this._config = config;
      this._loading = false;
      console.log('✅ Atlas configuration loaded:', config);
      return config;
    } catch (error) {
      this._loading = false;
      this._loadPromise = null;
      console.error('❌ Failed to load Atlas configuration:', error);
      
      // Return fallback configuration
      return this._getFallbackConfig();
    }
  }

  /**
   * Fetch configuration from backend API
   */
  async _fetchConfig() {
    const response = await fetch(`${this.backendUrl}/api/v1/config`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch config: ${response.status} ${response.statusText}`);
    }
    
    const config = await response.json();
    return config;
  }

  /**
   * Get fallback configuration if API is unavailable
   */
  _getFallbackConfig() {
    console.warn('⚠️ Using fallback Atlas configuration');
    return {
      paths: {
        asset_library_root: '/net/library/atlaslib',
        asset_library_3d: '/net/library/atlaslib/3D',
        asset_library_2d: '/net/library/atlaslib/2D',
        thumbnails: '/net/library/atlaslib/thumbnails'
      },
      api: {
        backend_url: this.backendUrl,
        frontend_url: 'http://localhost:3011'
      },
      asset_structure: {
        categories: {
          '3D': {
            Assets: ['Blacksmith Asset', 'Megascans', 'Kitbash'],
            FX: ['Blacksmith FX', 'Atmosphere', 'FLIP', 'Pyro'],
            Materials: ['Blacksmith Materials', 'Redshift', 'Karma'],
            HDAs: ['Blacksmith HDAs']
          },
          '2D': {
            Textures: ['Studio Textures', 'Stock Photos', 'Generated'],
            References: ['Character Refs', 'Environment Refs', 'Prop Refs'],
            UI: ['Icons', 'Logos', 'Interface Elements']
          }
        }
      },
      render_settings: {
        default_engine: 'Redshift',
        supported_engines: ['Redshift', 'Karma', 'Arnold', 'Mantra'],
        thumbnail_size: [512, 512],
        thumbnail_format: 'png'
      },
      version: '1.0.0'
    };
  }

  /**
   * Get specific configuration value using dot notation
   */
  get(keyPath, defaultValue = null) {
    if (!this._config) {
      console.warn('⚠️ Configuration not loaded, use await config.load() first');
      return defaultValue;
    }

    const keys = keyPath.split('.');
    let value = this._config;

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return defaultValue;
      }
    }

    return value;
  }

  /**
   * Convenience getters for commonly used paths
   */
  get assetLibraryRoot() {
    return this.get('paths.asset_library_root', '/net/library/atlaslib');
  }

  get assetLibrary3D() {
    return this.get('paths.asset_library_3d', '/net/library/atlaslib/3D');
  }

  get assetLibrary2D() {
    return this.get('paths.asset_library_2d', '/net/library/atlaslib/2D');
  }

  get thumbnailsPath() {
    return this.get('paths.thumbnails', '/net/library/atlaslib/thumbnails');
  }

  get supportedEngines() {
    return this.get('render_settings.supported_engines', ['Redshift', 'Karma']);
  }

  get defaultEngine() {
    return this.get('render_settings.default_engine', 'Redshift');
  }

  get categories3D() {
    return this.get('asset_structure.categories.3D', {});
  }

  get categories2D() {
    return this.get('asset_structure.categories.2D', {});
  }

  /**
   * Reload configuration from backend
   */
  async reload() {
    console.log('🔄 Reloading Atlas configuration...');
    return this.load(true);
  }

  /**
   * Validate current configuration
   */
  async validate() {
    try {
      const response = await fetch(`${this.backendUrl}/api/v1/config/validate`);
      
      if (!response.ok) {
        throw new Error(`Validation failed: ${response.status} ${response.statusText}`);
      }
      
      const validation = await response.json();
      console.log('✅ Configuration validation:', validation);
      return validation;
    } catch (error) {
      console.error('❌ Failed to validate configuration:', error);
      throw error;
    }
  }

  /**
   * Get configuration status info
   */
  getStatus() {
    return {
      loaded: this._config !== null,
      loading: this._loading,
      backendUrl: this.backendUrl,
      version: this.get('version', 'unknown')
    };
  }
}

// Create global instance
const config = new AtlasConfig();

export default config;

// Export convenience functions
export const getConfig = (keyPath, defaultValue = null) => config.get(keyPath, defaultValue);
export const loadConfig = (force = false) => config.load(force);
export const reloadConfig = () => config.reload();
export const validateConfig = () => config.validate();

// React hook for using configuration in components

export const useAtlasConfig = () => {
  const [configData, setConfigData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadConfiguration = async () => {
      try {
        setLoading(true);
        const config = await loadConfig();
        setConfigData(config);
        setError(null);
      } catch (err) {
        setError(err);
        console.error('Failed to load config in hook:', err);
      } finally {
        setLoading(false);
      }
    };

    loadConfiguration();
  }, []);

  return {
    config: configData,
    loading,
    error,
    reload: reloadConfig,
    validate: validateConfig
  };
};