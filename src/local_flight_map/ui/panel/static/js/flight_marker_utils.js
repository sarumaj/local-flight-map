// Flight marker utilities
window.calculateMarkerSize = function (props) {
  const altitude = props.baro_altitude || props.geom_altitude;
  if (!altitude || typeof altitude !== 'number' || isNaN(altitude)) return 48;

  const minAlt = -1000;
  const maxAlt = 60000;

  const boundedAltitude = Math.min(Math.max(altitude, minAlt), maxAlt);
  const normalizedSize = ((boundedAltitude - minAlt) / (maxAlt - minAlt)) * (80 - 20) + 20;
  return Math.min(Math.max(normalizedSize, 20), 80);
};

window.calculateVerticalSpeedIndicator = function (props) {
  const vs = props.baro_rate_of_climb_descent || props.geom_rate_of_climb_descent || 0;
  const vsColor = Math.abs(vs) < 100 ? '#a0a0a0' : (vs > 0 ? '#4caf50' : '#f44336');
  const vsSymbol = Math.abs(vs) < 100 ? '→' : (vs > 0 ? '↑' : '↓');
  return { vsColor, vsSymbol };
};

window.flightInfoStyles = {
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
};

window.generateFlightInfoHtml = function (props, markerSize) {
  const altitude = props.baro_altitude || props.geom_altitude || 0;
  const groundSpeed = props.ground_speed || 0;
  const { vsColor, vsSymbol } = window.calculateVerticalSpeedIndicator(props);

  return `
    <div style="${window.flightInfoStyles.container.replace('{markerSize}', markerSize)}">
      <span style="${window.flightInfoStyles.value}">FL${Math.round(altitude / 100)}</span>
      <span style="${window.flightInfoStyles.value}">${Math.round(groundSpeed)}kt</span>
      <span style="${window.flightInfoStyles.vsIndicator}; color: ${vsColor};">${vsSymbol}</span>
    </div>
  `;
};

// Add shadow filter to the icon
window.addIconShadow = function (html) {
  return html.replace(
    /<img([^>]+)style="([^"]+)"/,
    '<img$1style="$2; filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.5));"'
  );
}; 