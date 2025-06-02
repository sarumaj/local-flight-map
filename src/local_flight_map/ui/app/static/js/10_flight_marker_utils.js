/**
 * Utility functions for handling flight markers on the map
 * Provides methods for calculating marker sizes, generating flight info HTML,
 * and managing vertical speed indicators
 */
const FlightMarkerUtils = {
  /**
   * Calculate the size of a marker based on aircraft altitude
   * @param {Object} props - Aircraft properties
   * @param {number} props.baro_altitude - Barometric altitude
   * @param {number} props.geom_altitude - Geometric altitude
   * @returns {number} Marker size in pixels (20-80)
   */
  calculateMarkerSize(props) {
    if (!props) {
      console.warn('No properties provided for marker size calculation');
      return 48;
    }

    const altitude = props.baro_altitude || props.geom_altitude || 0;
    if (altitude === 'ground' || altitude === 0) return 20;
    if (!altitude || typeof altitude !== 'number' || isNaN(altitude)) {
      console.warn('Invalid altitude value for marker size:', altitude);
      return 48;
    }

    const minAlt = -1000;
    const maxAlt = 60000;
    const boundedAltitude = Math.min(Math.max(altitude, minAlt), maxAlt);
    const normalizedSize = ((boundedAltitude - minAlt) / (maxAlt - minAlt)) * (80 - 20) + 20;
    return Math.min(Math.max(normalizedSize, 20), 80);
  },

  /**
   * Calculate vertical speed indicator properties
   * @param {Object} props - Aircraft properties
   * @param {number} props.baro_rate_of_climb_descent - Barometric rate of climb/descent
   * @param {number} props.geom_rate_of_climb_descent - Geometric rate of climb/descent
   * @returns {Object} Object containing vsColor and vsSymbol
   */
  calculateVerticalSpeedIndicator(props) {
    if (!props) {
      console.warn('No properties provided for vertical speed calculation');
      return { vsColor: '#a0a0a0', vsSymbol: '→' };
    }

    const vs = props.baro_rate_of_climb_descent || props.geom_rate_of_climb_descent || 0;
    if (typeof vs !== 'number' || isNaN(vs)) {
      console.warn('Invalid vertical speed value:', vs);
      return { vsColor: '#a0a0a0', vsSymbol: '→' };
    }

    const vsColor = Math.abs(vs) < 100 ? '#a0a0a0' : (vs > 0 ? '#4caf50' : '#f44336');
    const vsSymbol = Math.abs(vs) < 100 ? '→' : (vs > 0 ? '↑' : '↓');
    return { vsColor, vsSymbol };
  },

  /**
   * CSS styles for flight information display
   */
  flightInfoStyles: {
    container: `
            position: absolute;
            top: -{markerSize}px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(33, 37, 41, 0.7);
            color: #fff;
            padding: 3px 6px;
            border-radius: 6px;
            font-size: 11px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            white-space: nowrap;
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(4px);
        `,
    value: `
            background: rgba(255, 255, 255, 0.15);
            padding: 1px 4px;
            border-radius: 3px;
            font-weight: 500;
        `,
    vsIndicator: `
            background: rgba(255, 255, 255, 0.15);
            padding: 1px 4px;
            border-radius: 3px;
            font-weight: 500;
            font-size: 12px;
            font-weight: bold;
        `
  },

  /**
   * Generate HTML for flight information display
   * @param {Object} props - Aircraft properties
   * @param {number} markerSize - Size of the marker in pixels
   * @returns {string} HTML string for flight information
   */
  generateFlightInfoHtml(props, markerSize) {
    if (!props) {
      console.warn('No properties provided for flight info generation');
      return '';
    }

    if (!markerSize || typeof markerSize !== 'number' || isNaN(markerSize)) {
      console.warn('Invalid marker size for flight info:', markerSize);
      markerSize = 48; // Default size
    }

    const altitude = props.baro_altitude || props.geom_altitude || 0;
    const groundSpeed = props.ground_speed || props.velocity || 0;
    const { vsColor, vsSymbol } = this.calculateVerticalSpeedIndicator(props);
    const flightLevel = altitude === 'ground' ? 0 : Math.round(altitude / 100);

    return `
      <div class="flight-info" style="top: -${markerSize}px;">
        <span class="flight-info-value">FL${flightLevel}</span>
        <span class="flight-info-value">${Math.round(groundSpeed)}kt</span>
        <span class="flight-info-vs" style="color: ${vsColor};">${vsSymbol}</span>
      </div>
    `;
  },

  /**
   * Add shadow effect to marker icon
   * @param {string} html - Original HTML string
   * @returns {string} HTML string with shadow effect
   */
  addIconShadow(html) {
    if (!html) {
      console.warn('No HTML provided for icon shadow');
      return '';
    }
    return html.replace(
      /<img([^>]+)style="([^"]+)"/,
      '<img$1style="$2; filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.5));"'
    );
  }
};

/**
 * Configuration cache for managing API requests
 */
const configCache = {
  interval: null,
  bounds: null,
  center: null,
  radius: null,
  lastFetch: 0,
  fetchPromise: null
};

/**
 * Clear the configuration cache
 */
function clearConfigCache() {
  configCache.interval = null;
  configCache.bounds = null;
  configCache.center = null;
  configCache.radius = null;
  configCache.lastFetch = 0;
  configCache.fetchPromise = null;
}

/**
 * Get configuration with caching
 * @returns {Promise<Object>} Configuration object with interval, bounds, center, and radius
 */
async function getConfig() {
  const now = Date.now();
  const cacheDuration = 60000; // Cache for 1 minute

  // Force a fresh fetch if any required property is missing
  if (!configCache.bounds || !configCache.interval || !configCache.center || !configCache.radius) {
    configCache.lastFetch = 0; // Force cache miss
  }

  // Return cached value if it's still valid
  if (configCache.interval && configCache.bounds && configCache.center && configCache.radius &&
    (now - configCache.lastFetch) < cacheDuration) {
    return {
      interval: configCache.interval,
      bounds: configCache.bounds,
      center: configCache.center,
      radius: configCache.radius
    };
  }

  // If there's an ongoing fetch, return its promise
  if (configCache.fetchPromise) {
    return configCache.fetchPromise;
  }

  // Start new fetch
  configCache.fetchPromise = fetch('/ui/config')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(config => {
      // Check if all required properties are present
      if (!config.bounds || !config.interval || !config.center || !config.radius) {
        console.warn('Received incomplete config:', config);
        configCache.lastFetch = 0; // Force another fetch
        return getConfig(); // Recursively try again
      }

      // Update all config properties
      configCache.interval = config.interval;
      configCache.bounds = config.bounds;
      configCache.center = config.center;
      configCache.radius = config.radius;
      configCache.lastFetch = now;
      configCache.fetchPromise = null;
      return {
        interval: config.interval,
        bounds: config.bounds,
        center: config.center,
        radius: config.radius
      };
    })
    .catch(error => {
      console.error('Error fetching config:', error);
      configCache.fetchPromise = null;
      // Return default values if fetch fails
      return {
        interval: 200,
        bounds: null,
        center: null,
        radius: null
      };
    });

  return configCache.fetchPromise;
}

// Clear cache on page load
window.addEventListener('load', clearConfigCache);

// Exports
window.calculateMarkerSize = FlightMarkerUtils.calculateMarkerSize;
window.calculateVerticalSpeedIndicator = FlightMarkerUtils.calculateVerticalSpeedIndicator;
window.generateFlightInfoHtml = FlightMarkerUtils.generateFlightInfoHtml.bind(FlightMarkerUtils);
window.addIconShadow = FlightMarkerUtils.addIconShadow;
window.getConfig = getConfig;
window.clearConfigCache = clearConfigCache; 