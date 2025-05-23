(feature, oldLayer) => {

  if (!oldLayer) {
    return;
  }

  var popup = oldLayer.getPopup();
  if (popup && popup.isOpen()) {
    return oldLayer;
  }

  // Update the layer position with animation
  var type = feature.geometry && feature.geometry.type;
  var coordinates = feature.geometry && feature.geometry.coordinates;
  switch (type) {
    case 'Point':
      var newLatLng = L.GeoJSON.coordsToLatLng(coordinates);
      var currentLatLng = oldLayer.getLatLng();

      // Animate the marker movement
      if (currentLatLng) {
        var duration = 100; // 100ms animation
        var startTime = null;
        var startLat = currentLatLng.lat;
        var startLng = currentLatLng.lng;
        var endLat = newLatLng.lat;
        var endLng = newLatLng.lng;

        function animate(timestamp) {
          if (!startTime) startTime = timestamp;
          var progress = Math.min((timestamp - startTime) / duration, 1);

          // Easing function for smooth animation
          progress = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;

          var currentLat = startLat + (endLat - startLat) * progress;
          var currentLng = startLng + (endLng - startLng) * progress;

          oldLayer.setLatLng([currentLat, currentLng]);

          // Update icon rotation
          var icon = oldLayer.getIcon();
          if (icon && feature.properties.track_angle) {
            var imgElement = icon.options.html.match(/<img[^>]+>/)[0];
            var initialRotation = parseInt(imgElement.match(/data-initial-rotation="(\d+)"/)[1]);
            var newIcon = L.divIcon({
              className: 'rotated-icon',
              html: imgElement.replace(/transform:[^;]+/,
                `transform:rotate(${feature.properties.track_angle - initialRotation}deg)`),
              iconSize: icon.options.iconSize,
              iconAnchor: icon.options.iconAnchor
            });
            oldLayer.setIcon(newIcon);
          }

          if (progress < 1) {
            requestAnimationFrame(animate);
          }
        }

        requestAnimationFrame(animate);
      } else {
        oldLayer.setLatLng(newLatLng);
      }
      break;
    case 'LineString':
    case 'MultiLineString':
      oldLayer.setLatLngs(L.GeoJSON.coordsToLatLngs(coordinates, type === 'LineString' ? 0 : 1));
      break;
    case 'Polygon':
    case 'MultiPolygon':
      oldLayer.setLatLngs(L.GeoJSON.coordsToLatLngs(coordinates, type === 'Polygon' ? 1 : 2));
      break;
    default:
      return null;
  }

  return oldLayer;
}