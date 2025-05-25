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
    if (!props) return 48;

    const altitude = props.baro_altitude || props.geom_altitude || 0;
    if (altitude === 'ground') return 20;
    if (!altitude || typeof altitude !== 'number' || isNaN(altitude)) return 48;

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
    if (!props) return { vsColor: '#a0a0a0', vsSymbol: '→' };

    const vs = props.baro_rate_of_climb_descent || props.geom_rate_of_climb_descent || 0;
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
    if (!props) return '';

    const altitude = props.baro_altitude || props.geom_altitude || 0;
    const groundSpeed = props.ground_speed || 0;
    const { vsColor, vsSymbol } = this.calculateVerticalSpeedIndicator(props);
    const flightLevel = altitude === 'ground' ? 0 : Math.round(altitude / 100);

    return `
            <div style="${this.flightInfoStyles.container.replace('{markerSize}', markerSize)}">
                <span style="${this.flightInfoStyles.value}">FL${flightLevel}</span>
                <span style="${this.flightInfoStyles.value}">${Math.round(groundSpeed)}kt</span>
                <span style="${this.flightInfoStyles.vsIndicator}; color: ${vsColor};">${vsSymbol}</span>
            </div>
        `;
  },

  /**
   * Add shadow effect to marker icon
   * @param {string} html - Original HTML string
   * @returns {string} HTML string with shadow effect
   */
  addIconShadow(html) {
    if (!html) return '';
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
  lastFetch: 0,
  fetchPromise: null
};

/**
 * Get configuration with caching
 * @returns {Promise<Object>} Configuration object with interval
 */
async function getConfig() {
  const now = Date.now();
  const cacheDuration = 60000; // Cache for 1 minute

  // Return cached value if it's still valid
  if (configCache.interval && (now - configCache.lastFetch) < cacheDuration) {
    return configCache;
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
      configCache.interval = config.interval;
      configCache.lastFetch = now;
      configCache.fetchPromise = null;
      return configCache;
    })
    .catch(error => {
      console.error('Error fetching config:', error);
      configCache.fetchPromise = null;
      // Return default value if fetch fails
      return { interval: 200 };
    });

  return configCache.fetchPromise;
}

// Exports
window.calculateMarkerSize = FlightMarkerUtils.calculateMarkerSize;
window.calculateVerticalSpeedIndicator = FlightMarkerUtils.calculateVerticalSpeedIndicator;
window.generateFlightInfoHtml = FlightMarkerUtils.generateFlightInfoHtml.bind(FlightMarkerUtils);
window.addIconShadow = FlightMarkerUtils.addIconShadow;
window.getConfig = getConfig; 