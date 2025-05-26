/**
 * Draggable bounding box implementation for the flight map
 */
class DraggableBBox {
  /**
   * Create a new draggable bounding box
   * @param {L.Map} map - The Leaflet map instance
   * @param {L.LatLngBounds} initialBounds - The initial bounds for the box
   */
  constructor(map, initialBounds) {
    if (!map || !map.getBounds) {
      console.error('Invalid map instance provided to DraggableBBox');
      throw new Error('Invalid map instance');
    }
    if (!initialBounds || !initialBounds.getNorth) {
      console.error('Invalid initial bounds provided to DraggableBBox');
      throw new Error('Invalid initial bounds');
    }

    this.map = map;
    this.bounds = initialBounds;
    this.initialBounds = initialBounds;
    this.rectangle = null;
    this.isDragging = false;
    this.startPoint = null;
    this.offset = null;
    this.radarBeam = null;
    this.animationInterval = null;
    this.animationStartTime = null;
    this.rotationSpeed = 60; // degrees per second
    this.config = null; // Will store the config from /ui/config

    // Bind event handlers
    this.boundEvents = {
      mousedown: this.onMouseDown.bind(this),
      mousemove: this.onMouseMove.bind(this),
      mouseup: this.onMouseUp.bind(this)
    };

    this.initialize();
  }

  /**
   * Initialize the draggable rectangle and radar beam
   */
  initialize() {
    try {
      this.rectangle = L.rectangle(this.bounds, {
        color: 'red',
        weight: 2,
        opacity: 0.7,
        fillOpacity: 0.1,
        className: 'draggable-rectangle',
        pane: 'shadowPane' // Use shadowPane for background elements
      }).addTo(this.map);

      const path = this.rectangle.getElement();
      if (!path) {
        console.warn('Failed to get rectangle element');
        return;
      }

      path.setAttribute('pointer-events', 'all');
      path.style.cursor = 'move';

      this.rectangle.on('mousedown', this.boundEvents.mousedown);
      this.map.on('mousemove', this.boundEvents.mousemove);
      this.map.on('mouseup', this.boundEvents.mouseup);

      this.initializeRadarBeam();
    } catch (error) {
      console.error('Error initializing draggable bbox:', error);
    }
  }

  /**
   * Initialize the radar beam overlay
   */
  initializeRadarBeam() {
    try {
      const center = this.bounds.getCenter();
      if (!center) {
        console.warn('Failed to get bounds center for radar beam');
        return;
      }

      // Create the radar icon
      this.radarIcon = L.divIcon({
        className: 'radar-icon',
        html: `<img src="/ui/static/icons/radar.png" style="width: 32px; height: 32px; cursor: pointer;">`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      this.radarMarker = L.marker(center, {
        icon: this.radarIcon,
        interactive: true,
        riseOnHover: true,
        autoPanOnFocus: false,
        keyboard: true,
        title: 'Radar Information',
        pane: 'shadowPane'
      }).addTo(this.map);

      // Create the beam line
      this.beamLine = L.polyline([center, center], {
        color: 'rgba(0, 255, 0, 0.5)',
        weight: 2,
        opacity: 0.7,
        className: 'radar-beam-line',
        interactive: false,
        pane: 'shadowPane'
      }).addTo(this.map);

      // Create popup for radar information
      this.radarPopup = L.popup({
        maxWidth: 300,
        closeButton: true,
        autoClose: true,
        closeOnEscapeKey: true,
        closeOnClick: true
      });

      // Bind popup to radar marker
      this.radarMarker.bindPopup(this.radarPopup);
      this.updateRadarPopupContent();

      // Add click handler to the radar marker with proper event handling
      this.radarMarker.on('click', (e) => {
        // Only handle click if we're not currently dragging
        if (!this.isDragging) {
          e.originalEvent.stopPropagation();
          if (!this.radarPopup.isOpen()) {
            this.radarPopup.openOn(this.radarMarker);
          }
        }
      });

      // Ensure the rectangle stays on top and is interactive
      this.rectangle.bringToFront();
      const path = this.rectangle.getElement();
      if (path) {
        path.setAttribute('pointer-events', 'all');
        path.style.cursor = 'move';
      }

      this.startRadarAnimation();
    } catch (error) {
      console.error('Error initializing radar beam:', error);
    }
  }

  /**
   * Create popup content for radar information
   * @returns {string} HTML content for the popup
   */
  createRadarPopupContent() {
    const center = this.rectangle.getBounds().getCenter();
    const bounds = this.rectangle.getBounds();
    
    // Calculate radius in kilometers and nautical miles
    const radiusKm = this.calculateRadius(bounds);
    const radiusNm = radiusKm * 0.539957; // Convert km to nautical miles

    // Count markers in the marker pane including clustered markers
    let markerCount = 0;
    try {
      const markerPane = document.querySelector('.leaflet-marker-pane');
      if (markerPane) {
        // Count individual markers
        const individualMarkers = Array.from(markerPane.children)
          .filter(child => (child.classList.contains('leaflet-marker-icon') && !child.classList.contains('custom-cluster')))
          .length;
        
        // Count markers in clusters
        const clusterMarkers = Array.from(markerPane.children)
          .filter(child => child.classList.contains('custom-cluster'))
          .reduce((total, cluster) => {
            // Extract count from the cluster's div content
            const countDiv = cluster.querySelector('div > div');
            if (countDiv) {
              const count = parseInt(countDiv.textContent, 10);
              return total + (isNaN(count) ? 0 : count);
            }
            return total;
          }, 0);

        markerCount = individualMarkers + clusterMarkers;
      }
    } catch (error) {
      console.error('Error counting markers:', error);
    }
    
    return `
      <div class="radar-info" style="max-height: 300px; overflow-y: auto;">
        <h3 style="
          margin: 0 0 10px 0;
          padding: 5px;
          background: #f8f9fa;
          position: sticky;
          top: 0;
        ">Radar Information</h3>
        <table style="width: 100%; border-collapse: collapse;">
          <tbody>
            <tr style="border-bottom: 1px solid #eee;">
              <th style="text-align: left; padding: 5px; background: #f8f9fa;">Center Point</th>
              <td style="padding: 5px;">${center.lat.toFixed(6)}, ${center.lng.toFixed(6)}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <th style="text-align: left; padding: 5px; background: #f8f9fa;">Radius</th>
              <td style="padding: 5px;">${radiusKm.toFixed(1)} km (${radiusNm.toFixed(1)} NM)</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <th style="text-align: left; padding: 5px; background: #f8f9fa;">Objects in Area</th>
              <td style="padding: 5px;">${markerCount} objects</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <th style="text-align: left; padding: 5px; background: #f8f9fa;">Update Interval</th>
              <td style="padding: 5px;">${this.config?.interval || 200} ms</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <th style="text-align: left; padding: 5px; background: #f8f9fa;">Rotation Speed</th>
              <td style="padding: 5px;">${this.rotationSpeed}°/s</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  /**
   * Calculate the radius of the radar coverage in kilometers
   * @param {L.LatLngBounds} bounds - The bounding box
   * @returns {number} The radius in kilometers
   */
  calculateRadius(bounds) {
    const center = bounds.getCenter();
    
    // Calculate horizontal radius (east-west)
    const eastPoint = L.latLng(center.lat, bounds.getEast());
    const horizontalRadius = center.distanceTo(eastPoint) / 1000; // Convert meters to kilometers
    
    // Calculate vertical radius (north-south)
    const northPoint = L.latLng(bounds.getNorth(), center.lng);
    const verticalRadius = center.distanceTo(northPoint) / 1000; // Convert meters to kilometers
    
    // Return the maximum radius
    return Math.max(horizontalRadius, verticalRadius);
  }

  /**
   * Update the radar popup content
   */
  updateRadarPopupContent() {
    if (this.radarPopup) {
      this.radarPopup.setContent(this.createRadarPopupContent());
    }
  }

  /**
   * Start the radar beam animation
   */
  async startRadarAnimation() {
    try {
      const interval = 16; // Fixed interval for smooth animation (~60fps)

      this.animationStartTime = Date.now();
      this.animationInterval = setInterval(() => {
        this.updateRadarBeam();
      }, interval);
    } catch (error) {
      console.error('Failed to start radar animation:', error);
    }
  }

  /**
   * Calculate the intersection point of a line with the bounding box
   * @param {L.LatLng} center - The center point
   * @param {number} angleRad - The angle in radians
   * @param {L.LatLngBounds} bounds - The bounding box
   * @returns {L.LatLng} The intersection point
   */
  calculateIntersectionPoint(center, angleRad, bounds) {
    if (!center || !bounds) {
      console.warn('Invalid parameters for intersection calculation');
      return center;
    }

    try {
      // Calculate the direction vector
      const dx = Math.cos(angleRad);
      const dy = Math.sin(angleRad);

      // Calculate the distances to each boundary
      const distToNorth = (bounds.getNorth() - center.lat) / dy;
      const distToSouth = (bounds.getSouth() - center.lat) / dy;
      const distToEast = (bounds.getEast() - center.lng) / dx;
      const distToWest = (bounds.getWest() - center.lng) / dx;

      // Find the minimum positive distance
      let minDist = Infinity;
      if (distToNorth > 0) minDist = Math.min(minDist, distToNorth);
      if (distToSouth > 0) minDist = Math.min(minDist, distToSouth);
      if (distToEast > 0) minDist = Math.min(minDist, distToEast);
      if (distToWest > 0) minDist = Math.min(minDist, distToWest);

      if (minDist === Infinity) {
        console.warn('No valid intersection point found');
        return center;
      }

      // Calculate the intersection point
      const endLat = center.lat + dy * minDist;
      const endLng = center.lng + dx * minDist;

      return L.latLng(endLat, endLng);
    } catch (error) {
      console.error('Error calculating intersection point:', error);
      return center;
    }
  }

  /**
   * Calculate the current angle based on elapsed time
   * @returns {number} The current angle in radians
   */
  getCurrentAngle() {
    if (!this.animationStartTime) {
      console.warn('Animation start time not set');
      return 0;
    }

    const elapsedTime = (Date.now() - this.animationStartTime) / 1000;
    const angle = (-elapsedTime * this.rotationSpeed) % 360;
    return (angle * Math.PI) / 180;
  }

  /**
   * Update the beam position
   * @param {L.LatLngBounds} bounds - The current bounds
   */
  updateBeamPosition(bounds) {
    if (!this.beamLine || !this.radarMarker) {
      console.warn('Beam line or radar marker not initialized');
      return;
    }

    try {
      const center = bounds.getCenter();
      if (!center) {
        console.warn('Failed to get bounds center for beam update');
        return;
      }

      const angleRad = this.getCurrentAngle();
      const endPoint = this.calculateIntersectionPoint(center, angleRad, bounds);
      
      // Update both the beam line and radar icon position
      this.beamLine.setLatLngs([center, endPoint]);
      this.radarMarker.setLatLng(center);
      
      // Update popup content if it's open
      if (this.radarPopup && this.radarPopup.isOpen()) {
        this.updateRadarPopupContent();
      }
    } catch (error) {
      console.error('Error updating beam position:', error);
    }
  }

  /**
   * Update the radar beam position
   */
  updateRadarBeam() {
    if (!this.rectangle) {
      console.warn('Rectangle not initialized for radar beam update');
      return;
    }
    this.updateBeamPosition(this.rectangle.getBounds());
  }

  /**
   * Clean up resources and remove event listeners
   */
  destroy() {
    try {
      if (this.rectangle) {
        this.rectangle.off('mousedown', this.boundEvents.mousedown);
        this.map.off('mousemove', this.boundEvents.mousemove);
        this.map.off('mouseup', this.boundEvents.mouseup);
        this.rectangle.remove();
        this.map.setMaxBounds(null);
        this.map.setView([0, 0], 2);
      }

      if (this.animationInterval) {
        clearInterval(this.animationInterval);
        this.animationInterval = null;
      }

      if (this.beamLine) {
        this.beamLine.remove();
        this.beamLine = null;
      }

      if (this.radarMarker) {
        this.radarMarker.remove();
        this.radarMarker = null;
      }
    } catch (error) {
      console.error('Error destroying draggable bbox:', error);
    }
  }

  /**
   * Get bounds object for API calls
   * @param {L.LatLngBounds} bounds - The bounds to convert
   * @returns {Object} The bounds object for API calls
   */
  getBoundsObject(bounds) {
    return {
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest()
    };
  }

  /**
   * Update bounds on the server
   * @param {L.LatLngBounds} bounds - The bounds to update
   */
  async updateServerBounds(bounds) {
    try {
      const boundsObject = this.getBoundsObject(bounds);
      const response = await fetch('/ui/bbox', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bounds: boundsObject })
      });

      if (!response.ok) {
        const content = await response.text();
        console.error('Server response:', content);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      window.dispatchEvent(new CustomEvent('boundsUpdated', {
        detail: { bounds: this.getBoundsObject(bounds) }
      }));
    } catch (error) {
      console.error('Error updating bounding box:', error);
      this.map.setMaxBounds(null);
    }
  }

  /**
   * Reset the bounding box to its initial position
   */
  async reset() {
    if (!this.rectangle) {
      console.warn('Rectangle not initialized for reset');
      return;
    }

    try {
      this.rectangle.setBounds(this.initialBounds);
      this.map.setMaxBounds(this.initialBounds);
      this.map.fitBounds(this.initialBounds, {
        animate: true,
        duration: 0.5,
        easeLinearity: 0.5,
        maxZoom: this.map.getZoom()
      });
      await this.updateServerBounds(this.initialBounds);
    } catch (error) {
      console.error('Error resetting bounds:', error);
    }
  }

  /**
   * Handle mouse down event
   * @param {L.LeafletMouseEvent} e - The mouse event
   */
  onMouseDown(e) {
    if (!e.originalEvent || e.originalEvent.target !== this.rectangle.getElement()) {
      return;
    }

    try {
      // Prevent event propagation to avoid triggering radar marker events
      e.originalEvent.stopPropagation();
      e.originalEvent.preventDefault();

      this.isDragging = true;
      this.startPoint = e.latlng;
      this.offset = {
        lat: e.latlng.lat - this.rectangle.getBounds().getCenter().lat,
        lng: e.latlng.lng - this.rectangle.getBounds().getCenter().lng
      };

      this.map.dragging.disable();
    } catch (error) {
      console.error('Error in mouse down handler:', error);
      this.isDragging = false;
      this.map.dragging.enable();
    }
  }

  /**
   * Handle mouse move event
   * @param {L.LeafletMouseEvent} e - The mouse event
   */
  onMouseMove(e) {
    if (!this.isDragging) {
      return;
    }

    try {
      // Prevent event propagation during dragging
      e.originalEvent.stopPropagation();
      e.originalEvent.preventDefault();

      const newCenter = e.latlng;
      const bounds = this.rectangle.getBounds();
      const size = {
        lat: bounds.getNorth() - bounds.getSouth(),
        lng: bounds.getEast() - bounds.getWest()
      };

      const newBounds = L.latLngBounds(
        L.latLng(newCenter.lat - size.lat / 2, newCenter.lng - size.lng / 2),
        L.latLng(newCenter.lat + size.lat / 2, newCenter.lng + size.lng / 2)
      );

      this.rectangle.setBounds(newBounds);
      this.updateBeamPosition(newBounds);
    } catch (error) {
      console.error('Error in mouse move handler:', error);
      this.isDragging = false;
      this.map.dragging.enable();
    }
  }

  /**
   * Handle mouse up event
   */
  onMouseUp(e) {
    if (!this.isDragging) {
      return;
    }

    try {
      // Prevent event propagation when ending drag
      e.originalEvent.stopPropagation();
      e.originalEvent.preventDefault();

      this.isDragging = false;
      this.map.dragging.enable();

      const newBounds = this.rectangle.getBounds();
      this.map.setMaxBounds(newBounds);
      this.map.fitBounds(newBounds, {
        animate: true,
        duration: 0.5,
        easeLinearity: 0.5,
        maxZoom: this.map.getZoom()
      });
      this.updateServerBounds(newBounds);
      this.updateBeamPosition(newBounds);
    } catch (error) {
      console.error('Error in mouse up handler:', error);
      this.isDragging = false;
      this.map.dragging.enable();
    }
  }
}

/**
 * Initialize the draggable bounding box when the map is ready
 */
window.addEventListener('mapReady', async (e) => {
  const map = e.detail.map;
  if (!map || !map.getBounds) {
    console.error('Invalid map instance in mapReady event');
    return;
  }

  if (window.draggableBBox) {
    window.draggableBBox.destroy();
    window.draggableBBox = null;
  }

  try {
    const response = await fetch('/ui/config');
    if (!response.ok) {
      throw new Error('Failed to fetch configuration');
    }
    const config = await response.json();

    if (!config.bounds) {
      throw new Error('No bounds in configuration');
    }

    const initialBounds = L.latLngBounds(
      L.latLng(49.31666666666666, 7.016168165393562),
      L.latLng(50.983333333333334, 9.61716523460644)
    );

    window.draggableBBox = new DraggableBBox(map, initialBounds);
    window.draggableBBox.config = config; // Store the config
    await window.draggableBBox.reset();
  } catch (error) {
    console.error('Failed to initialize draggable bounding box:', error);
  }
});

// Add reset handler for page refresh
window.addEventListener('beforeunload', function () {
  if (window.draggableBBox) {
    window.draggableBBox.reset();
  }
}); 