/**
 * Map initialization script that waits for Leaflet to be ready
 * This script listens for the 'mapElementReady' event and checks for the map's availability
 * Once the map is found, it dispatches a 'mapReady' event with the map instance
 */
window.addEventListener('mapElementReady', (e) => {
  const mapId = e.detail.mapId;
  let checkInterval;

  /**
   * Cleanup function to clear the interval
   */
  const cleanup = () => {
    if (checkInterval) {
      clearInterval(checkInterval);
    }
  };

  // Wait for Leaflet and Bokeh to initialize
  checkInterval = setInterval(function () {
    try {
      const map = window[mapId];
      if (map && typeof L !== 'undefined' && L.Map && map instanceof L.Map) {
        cleanup();
        window.dispatchEvent(new CustomEvent("mapReady", { detail: { map: map } }));
      }
    } catch (error) {
      console.error('Error checking map initialization:', error);
      cleanup();
    }
  }, 100);

  // Clear interval after 30 seconds if map is not found
  setTimeout(cleanup, 30000);
});