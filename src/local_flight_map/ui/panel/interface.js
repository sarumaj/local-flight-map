/**
 * Main interface initialization script
 * This script handles the initial setup of the map interface and cleanup on page unload
 * It uses an IIFE (Immediately Invoked Function Expression) to avoid polluting the global scope
 */
(function () {
  /**
   * Initialize the map interface when the DOM is ready
   * Dispatches a 'mapElementReady' event with the map element ID
   */
  document.addEventListener("DOMContentLoaded", function () {
    const mapElement = document.querySelector(".folium-map");
    if (mapElement) {
      window.dispatchEvent(new CustomEvent("mapElementReady", {
        detail: { mapId: mapElement.id }
      }));
    }
  });

  /**
   * Cleanup handler for page refresh/reload
   * Ensures proper cleanup of the draggable bounding box before page unload
   */
  window.addEventListener("beforeunload", function () {
    if (window.draggableBBox) {
      window.draggableBBox.destroy();
    }
  });
})();
