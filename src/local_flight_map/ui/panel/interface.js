(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const mapElement = document.querySelector(".folium-map");
    if (mapElement) {
      window.dispatchEvent(new CustomEvent("mapElementReady", {
        detail: { mapId: mapElement.id }
      }));
    }
  });
})();
