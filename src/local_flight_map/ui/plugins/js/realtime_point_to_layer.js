/**
 * Convert a GeoJSON point feature to a Leaflet marker
 * Creates a marker with an aircraft icon, flight information, and popup
 * @param {Object} feature - The GeoJSON feature to convert
 * @param {string} feature.geometry.type - The geometry type (must be 'Point')
 * @param {Object} feature.properties - Properties of the aircraft
 * @param {number} feature.properties.track_angle - The aircraft's track angle
 * @param {string} feature.properties.icao24_code - The ICAO24 code of the aircraft
 * @param {Array<string>} feature.properties.tags - Array of tags for the aircraft
 * @param {L.LatLng} latlng - The latitude/longitude coordinates for the marker
 * @returns {L.Marker|null} A Leaflet marker or null if the feature is not a point
 */
(feature, latlng) => {
  // Only create markers for point features
  if (feature.geometry.type !== 'Point') {
    console.warn('Skipping non-point feature:', feature.geometry.type);
    return null;
  }

  const markerSize = calculateMarkerSize(feature.properties);
  if (!markerSize) {
    console.warn('Invalid marker size calculated for feature:', feature.properties);
  }

  /**
   * Available aircraft icons with their properties
   * @type {Array<{src: string, initial_rotation: number, weight: number, view_angle: number}>}
   */
  const icons = [
    { src: '/ui/static/icons/civil_helicopter.png', initial_rotation: 135, weight: 1, view_angle: 45 },
    { src: '/ui/static/icons/civil_plane_1.png', initial_rotation: 45, weight: 8, view_angle: 90 },
    { src: '/ui/static/icons/civil_plane_2.png', initial_rotation: 135, weight: 8, view_angle: 45 },
    { src: '/ui/static/icons/civil_plane_3.png', initial_rotation: 45, weight: 8, view_angle: 90 },
    { src: '/ui/static/icons/mil_plane_1.png', initial_rotation: 45, weight: 1, view_angle: 90 },
    { src: '/ui/static/icons/mil_plane_2.png', initial_rotation: 0, weight: 1, view_angle: 90 },
    { src: '/ui/static/icons/police_helicopter.png', initial_rotation: 135, weight: 1, view_angle: 45 },
  ]

  // Calculate total weight
  const totalWeight = icons.reduce((sum, icon) => sum + icon.weight, 0);

  // Generate random number between 0 and total weight
  let random = Math.random() * totalWeight;

  // Select icon based on weight
  let selectedIcon = icons[0];
  for (const icon of icons) {
    random -= icon.weight;
    if (random <= 0) {
      selectedIcon = icon;
      break;
    }
  }

  /**
   * Create a div icon for the marker
   * @type {L.DivIcon}
   */
  var icon = L.divIcon({
    className: 'rotated-icon',
    html: window.addIconShadow(`
      <div class="aircraft-marker" style="width: ${markerSize}px; height: ${markerSize}px;">
        <img class="aircraft-icon" src="${selectedIcon.src}" 
          data-initial-rotation="${selectedIcon.initial_rotation}"
          style="
            width:${markerSize}px;
            height:${markerSize}px;
            transform:rotate(${(feature.properties.track_angle || 0) - selectedIcon.initial_rotation}deg);
          ">
        <div class="clickable-overlay"></div>
        ${generateFlightInfoHtml(feature.properties, markerSize)}
      </div>
    `),
    iconSize: [markerSize, markerSize],
    iconAnchor: [markerSize / 2, markerSize / 2]
  });

  /**
   * Create the marker with the icon
   * @type {L.Marker}
   */
  var marker = L.marker(latlng, {
    icon: icon,
    interactive: true,
    riseOnHover: true,
    autoPanOnFocus: true,
    keyboard: true,
    title: feature.properties.icao24_code || 'Aircraft'
  });
  marker.tags = (feature.properties.tags || []).filter(tag => tag.trim());

  // Create distance line
  var distanceLine = L.polyline([], {
    color: 'rgba(255, 255, 255, 0.9)',
    weight: 3,
    opacity: 0.9,
    dashArray: '5, 10',
    interactive: false,
    className: 'distance-line'
  });

  // Create distance label
  var distanceLabel = L.divIcon({
    className: 'distance-label',
    html: `<div><span class="distance-text"></span></div>`,
    iconSize: [150, 20],
    iconAnchor: [75, 10]
  });

  var distanceMarker = L.marker([0, 0], {
    icon: distanceLabel,
    interactive: false
  });

  /**
   * Update distance line and label
   * @param {L.LatLng} markerLatLng - The marker's position
   * @param {L.Map} map - The map instance
   */
  async function updateDistanceLine(markerLatLng, map) {
    if (!markerLatLng) {
      console.warn('No marker position provided for distance line');
      return;
    }
    if (!map) {
      console.warn('No map instance provided for distance line');
      return;
    }

    try {
      // Get the current radar center from the draggable bbox
      let radarPosition;
      if (window.draggableBBox && window.draggableBBox.rectangle) {
        const bounds = window.draggableBBox.rectangle.getBounds();
        if (bounds) {
          radarPosition = bounds.getCenter();
        }
      }

      // Fallback to config bounds if draggable bbox is not available
      if (!radarPosition) {
        const config = await window.getConfig();
        if (!config || !config.bounds) {
          console.warn('Failed to get radar position');
          return;
        }
        radarPosition = L.latLng(
          (config.bounds.north + config.bounds.south) / 2,
          (config.bounds.east + config.bounds.west) / 2
        );
      }

      // Calculate distance in meters
      const distanceM = markerLatLng.distanceTo(radarPosition);
      const distanceNm = distanceM * 0.000539957; // Convert meters to nautical miles

      try {
        // Update line
        distanceLine.setLatLngs([radarPosition, markerLatLng]);
        if (!map.hasLayer(distanceLine)) {
          distanceLine.addTo(map);
        }

        // Update label
        const labelHtml = `${(Math.round(distanceM) / 1000).toFixed(1)}km (${distanceNm.toFixed(1)} NM)`;

        // Update popup distance info if open
        if (popup.isOpen()) {
          const popupElement = popup.getElement();
          if (popupElement) {
            const distanceInfo = popupElement.querySelector('.distance-info');
            if (distanceInfo) {
              distanceInfo.textContent = `${(Math.round(distanceM) / 1000).toFixed(1)} km (${distanceNm.toFixed(1)} NM)`;
            }
          }
        }

        // Ensure marker is added to map before trying to access its element
        if (!map.hasLayer(distanceMarker)) {
          distanceMarker.addTo(map);
        }

        const labelElement = distanceMarker.getElement();
        if (!labelElement) {
          console.warn('Failed to get label element for distance marker - recreating marker');
          // Recreate the marker if element is not available
          distanceMarker = L.marker([0, 0], {
            icon: distanceLabel,
            interactive: false
          }).addTo(map);
        }

        const textSpan = labelElement?.querySelector('.distance-text');
        if (!textSpan) {
          console.warn('Failed to find distance text span in label element');
          return;
        }
        textSpan.textContent = labelHtml;

        // Position label at midpoint
        const midLat = (radarPosition.lat + markerLatLng.lat) / 2;
        const midLng = (radarPosition.lng + markerLatLng.lng) / 2;
        distanceMarker.setLatLng([midLat, midLng]);
      } catch (layerError) {
        console.error('Error updating distance layers:', layerError);
        // Try to recreate the line if it's broken
        if (!(distanceLine instanceof L.Polyline)) {
          console.warn('Recreating broken distance line');
          distanceLine = L.polyline([], {
            color: 'rgba(255, 255, 255, 0.9)',
            weight: 3,
            opacity: 0.9,
            dashArray: '5, 10',
            interactive: false,
            className: 'distance-line'
          });
          distanceLine.setLatLngs([radarPosition, markerLatLng]);
          distanceLine.addTo(map);
        }
      }

      // Update the distance line periodically
      const config = await window.getConfig();
      if (config && config.interval) {
        setTimeout(() => {
          if (popup.isOpen()) {
            updateDistanceLine(marker.getLatLng(), map);
          }
        }, config.interval);
      }
    } catch (error) {
      console.error('Error updating distance line:', error);
    }
  }

  /**
   * Convert snake case to title case with spaces
   * @param {string} str - The string to convert
   * @returns {string} The converted string
   */
  function snakeToTitleCase(str) {
    return str
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  /**
   * Create popup content for the marker
   * @param {Object} props - Aircraft properties
   * @returns {string} HTML content for the popup
   */
  function createPopupContent(props) {
    const tags = (props["tags"] || []).filter(tag => tag.trim());
    var content = `
      <div class="aircraft-info">
        <h3>Aircraft Information</h3>
        <div class="tag-container">
          ${tags.map(tag => {
      const [key, value] = tag.split(':');
      return `
              <span class="tag">
                <span class="tag-key">${snakeToTitleCase(key)}</span>
                <span class="tag-value">${value}</span>
              </span>
            `;
    }).join('')}
        </div>
        <div class="section-title">Position & Distance</div>
        <table>
          <tbody>
            <tr>
              <th>Latitude</th>
              <td>${props.latitude?.toFixed(6) || 'N/A'}</td>
            </tr>
            <tr>
              <th>Longitude</th>
              <td>${props.longitude?.toFixed(6) || 'N/A'}</td>
            </tr>
            <tr>
              <th>Distance</th>
              <td class="distance-info"></td>
            </tr>
          </tbody>
        </table>`;

    // Add origin section if there are origin properties
    const originProps = Object.entries(props).filter(([key]) => key.startsWith('origin_'));
    if (originProps.length > 0) {
      content += `
        <div class="section-title">Origin</div>
        <table>
          <tbody>`;
      for (const [key, value] of originProps) {
        const displayKey = snakeToTitleCase(key.replace('origin_', ''));
        const displayValue = typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : value;
        content += `
            <tr>
              <th>${displayKey}</th>
              <td>${displayValue}</td>
            </tr>`;
      }
      content += `
          </tbody>
        </table>`;
    }

    // Add destination section if there are destination properties
    const destinationProps = Object.entries(props).filter(([key]) => key.startsWith('destination_'));
    if (destinationProps.length > 0) {
      content += `
        <div class="section-title">Destination</div>
        <table>
          <tbody>`;
      for (const [key, value] of destinationProps) {
        const displayKey = snakeToTitleCase(key.replace('destination_', ''));
        const displayValue = typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : value;
        content += `
            <tr>
              <th>${displayKey}</th>
              <td>${displayValue}</td>
            </tr>`;
      }
      content += `
          </tbody>
        </table>`;
    }

    // Add remaining properties section
    const remainingProps = Object.entries(props).filter(([key]) =>
      !key.startsWith('origin_') &&
      !key.startsWith('destination_') &&
      key !== 'tags' &&
      key !== 'latitude' &&
      key !== 'longitude'
    );

    if (remainingProps.length > 0) {
      content += `
        <div class="section-title">Properties</div>
        <table>
          <tbody>`;
      for (const [key, value] of remainingProps) {
        const displayKey = snakeToTitleCase(key);
        const displayValue = typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : value;
        content += `
            <tr>
              <th>${displayKey}</th>
              <td>${displayValue}</td>
            </tr>`;
      }
      content += `
          </tbody>
        </table>`;
    }

    content += `
      </div>`;
    return content;
  }

  /**
   * Create a popup for the marker
   * @type {L.Popup}
   */
  var popup = L.popup({
    maxWidth: 500,
    closeButton: false,
    autoClose: true,
    closeOnEscapeKey: true,
    closeOnClick: true,
    closeButton: true
  });

  /**
   * Update the popup content while preserving scroll position
   * @param {Object} props - New aircraft properties
   */
  marker._updatePopupContent = function (props) {
    var popupElement = popup.getElement();
    var scrollPosition = 0;
    if (popupElement) {
      var scrollContainer = popupElement.querySelector('.aircraft-info');
      if (scrollContainer) {
        scrollPosition = scrollContainer.scrollTop;
      }
    }
    popup.setContent(createPopupContent(props));
    if (popupElement) {
      var newScrollContainer = popupElement.querySelector('.aircraft-info');
      if (newScrollContainer) {
        newScrollContainer.scrollTop = scrollPosition;
      }
    }
  };

  // Initial popup content
  marker._updatePopupContent(feature.properties);
  marker.bindPopup(popup);

  // Add popup open/close handlers
  popup.on('add', async function () {
    // Get the map from the popup's target (marker)
    const map = popup._source._map;
    if (!map) {
      console.warn('No map instance found for popup source');
      return;
    }
    await updateDistanceLine(marker.getLatLng(), map);
  });

  popup.on('remove', function () {
    try {
      const map = popup._source._map;
      if (!map) {
        console.warn('No map instance found for popup source');
        return;
      }
      if (distanceLine && map.hasLayer(distanceLine)) {
        distanceLine.remove();
      }
      if (distanceMarker && map.hasLayer(distanceMarker)) {
        distanceMarker.remove();
      }
    } catch (error) {
      console.error('Error removing distance layers:', error);
    }
  });

  // Add click handler to both the marker and the clickable div
  marker.on('click', function (e) {
    e.originalEvent.stopPropagation();
    if (!popup.isOpen()) {
      popup.openOn(marker);
    }
  });

  // Add click handler to the clickable div
  icon.options.html = icon.options.html.replace('</div>',
    `<div class="clickable-overlay" onclick="this.parentElement.parentElement._leaflet_events.click[0].fn(event)"></div></div>`
  );

  return marker;
}