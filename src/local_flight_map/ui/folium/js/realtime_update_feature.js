/**
 * Update a feature's layer with new data
 * Handles different geometry types and animates position changes
 * @param {Object} feature - The new feature data
 * @param {Object} feature.geometry - The geometry object
 * @param {string} feature.geometry.type - The geometry type
 * @param {Array} feature.geometry.coordinates - The geometry coordinates
 * @param {Object} feature.properties - The feature properties
 * @param {number} feature.properties.track_angle - The aircraft's track angle
 * @param {L.Layer} oldLayer - The existing layer to update
 * @returns {L.Layer|null} The updated layer or null if no update was performed
 */
(feature, oldLayer) => {

  if (!oldLayer) {
    return;
  }

  // Freeze layer when popup is open
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

      // Get config using global cache
      window.getConfig().then(config => {
        if (currentLatLng) {
          // Custom smooth animation
          var duration = config.interval / 1000; // Convert ms to seconds
          var startTime = null;
          var startLat = currentLatLng.lat;
          var startLng = currentLatLng.lng;
          var endLat = newLatLng.lat;
          var endLng = newLatLng.lng;
          var isAnimating = true;

          /**
           * Cubic easing function for smooth animation
           * @param {number} t - Progress value between 0 and 1
           * @returns {number} Eased progress value
           */
          function easeInOutCubic(t) {
            return t < 0.5
              ? 4 * t * t * t
              : 1 - Math.pow(-2 * t + 2, 3) / 2;
          }

          // Pause animation on interaction
          oldLayer.on('mouseover mousedown touchstart', function () {
            isAnimating = false;
          });

          /**
           * Animation frame function
           * Updates layer position based on eased progress
           * @param {number} timestamp - Current animation timestamp
           */
          function animate(timestamp) {
            if (!startTime) {
              startTime = timestamp;
            }

            if (!isAnimating) {
              return;
            }

            var progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
            var easedProgress = easeInOutCubic(progress);

            var currentLat = startLat + (endLat - startLat) * easedProgress;
            var currentLng = startLng + (endLng - startLng) * easedProgress;

            oldLayer.setLatLng([currentLat, currentLng]);

            if (progress < 1) {
              requestAnimationFrame(animate);
            } else {
              isAnimating = false;
            }
          }

          requestAnimationFrame(animate);
        } else {
          oldLayer.setLatLng(newLatLng);
        }
      });

      // Update icon rotation if needed
      if (feature.properties.track_angle) {
        var icon = oldLayer.getIcon();
        var imgElement = icon.options.html.match(/<img[^>]+>/)[0];
        var initialRotation = parseInt(imgElement.match(/data-initial-rotation="(\d+)"/)[1]);

        const markerSize = calculateMarkerSize(feature.properties);

        // Update both rotation and flight info in one go
        let updatedHtml = window.addIconShadow(icon.options.html
          // Update rotation
          .replace(/transform:rotate\([^)]+\)/,
            `transform:rotate(${feature.properties.track_angle - initialRotation}deg)`)
          // Update flight info
          .replace(/<div style="[^"]*position: absolute;[^"]*top: -[^"]*">.*?<\/div>/s,
            generateFlightInfoHtml(feature.properties, markerSize)));

        var newIcon = L.divIcon({
          className: 'rotated-icon',
          html: updatedHtml,
          iconSize: [markerSize, markerSize],
          iconAnchor: [markerSize / 2, markerSize / 2]
        });
        oldLayer.setIcon(newIcon);
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