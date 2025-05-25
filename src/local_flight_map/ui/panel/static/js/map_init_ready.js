// Map initialization script
window.addEventListener('mapElementReady', (e) => {
  const mapId = e.detail.mapId;
  let checkInterval;

  const cleanup = () => {
    if (checkInterval) {
      clearInterval(checkInterval);
    }
  };

  // Wait for Leaflet to initialize
  checkInterval = setInterval(function () {
    try {
      const map = window[mapId];
      if (map) {
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