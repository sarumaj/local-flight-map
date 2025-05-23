(feature, latlng) => {
  // Only create markers for point features
  if (feature.geometry.type !== 'Point') {
    return null;
  }

  // Calculate marker size based on altitude
  function calculateMarkerSize(props) {
    const altitude = props.baro_altitude || props.geo_altitude;
    if (!altitude || typeof altitude !== 'number' || isNaN(altitude)) return 48; // default size if no valid altitude available

    // Define reasonable altitude bounds for aircraft (in feet)
    const minAlt = -1000;  // Allow for some negative altitude (below sea level)
    const maxAlt = 60000;  // Maximum typical cruising altitude for commercial aircraft

    // Clamp altitude to reasonable bounds
    const boundedAltitude = Math.min(Math.max(altitude, minAlt), maxAlt);

    // Normalize altitude to size between 20 and 80
    const normalizedSize = ((boundedAltitude - minAlt) / (maxAlt - minAlt)) * (80 - 20) + 20;
    return Math.min(Math.max(normalizedSize, 20), 80);
  }

  const markerSize = calculateMarkerSize(feature.properties);

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

  var icon = L.divIcon({
    className: 'rotated-icon',
    html: `
      <div style="position: relative; width: ${markerSize}px; height: ${markerSize}px; cursor: pointer;">
        <img src="${selectedIcon.src}" 
          data-initial-rotation="${selectedIcon.initial_rotation}"
          style="
            width:${markerSize}px;
            height:${markerSize}px;
            transform:rotate(${(feature.properties.track_angle || 0) - selectedIcon.initial_rotation}deg);
            transform-origin: center center;
          ">
        <div style="
          position: absolute;
          top: -16px;
          left: -16px;
          right: -16px;
          bottom: -16px;
          z-index: 1000;
          cursor: pointer;
        ">
      </div>
    `,
    iconSize: [markerSize, markerSize],
    iconAnchor: [markerSize / 2, markerSize / 2]
  });

  var marker = L.marker(latlng, {
    icon: icon,
    interactive: true,
    riseOnHover: true,
    autoPanOnFocus: true,
    keyboard: true,
    title: feature.properties.icao24_code || 'Aircraft'
  });
  marker.tags = (feature.properties.tags || []).filter(tag => tag.trim());

  // Create popup content function to avoid recreating HTML
  function createPopupContent(props) {
    const tags = (props["tags"] || []).filter(tag => tag.trim());
    var content = `
      <div class="aircraft-info" style="max-height: 300px; overflow-y: auto;">
        <h3 style="
          margin: 0 0 10px 0;
          padding: 5px;
          background: #f8f9fa;
          position: sticky;
          top: 0;
        ">Aircraft Information</h3>
        <div style="margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 5px;">
          ${tags.map(tag => {
      const [key, value] = tag.split(':');
      return `
              <span style="
                display: inline-block;
                padding: 4px 8px;
                background: #e9ecef;
                border-radius: 16px;
                font-size: 12px;
                color: #495057;
                border: 1px solid #dee2e6;
                white-space: nowrap;
              ">
                <span style="color: #6c757d; font-weight: 500;">${key}</span>
                <span style="color: #495057; margin-left: 4px;">${value}</span>
              </span>
            `;
    }).join('')}
        </div>
        <table style="width: 100%; border-collapse: collapse;">
          <tbody>`;
    for (var key in props) {
      if (key === "tags") continue;
      content += `
        <tr style="border-bottom: 1px solid #eee;">
          <th style="text-align: left; padding: 5px; background: #f8f9fa;">${key}</th>
          <td style="padding: 5px;">${props[key]}</td>
        </tr>`;
    }
    content += `
          </tbody>
        </table>
      </div>`;
    return content;
  }

  var popup = L.popup({
    maxWidth: 500,
    closeButton: false,
    autoClose: true,
    closeOnEscapeKey: true,
    closeOnClick: true,
    closeButton: true
  });

  // Store the popup content function and scroll position on the marker
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

  // Add click handler to both the marker and the clickable div
  marker.on('click', function (e) {
    e.originalEvent.stopPropagation();
    if (!popup.isOpen()) {
      popup.openOn(marker);
    }
  });

  // Add click handler to the clickable div
  icon.options.html = icon.options.html.replace('</div>',
    `< div style = "
position: absolute;
top: -16px;
left: -16px;
right: -16px;
bottom: -16px;
z - index: 1000;
cursor: pointer;
" onclick="this.parentElement.parentElement._leaflet_events.click[0].fn(event)"></div></div>`
  );

  return marker;
}