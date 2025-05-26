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
      throw new Error('Invalid map instance');
    }
    if (!initialBounds || !initialBounds.getNorth) {
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
    this.rectangle = L.rectangle(this.bounds, {
      color: 'red',
      weight: 2,
      opacity: 0.7,
      fillOpacity: 0.1,
      className: 'draggable-rectangle',
      pane: 'shadowPane' // Use shadowPane for background elements
    }).addTo(this.map);

    const path = this.rectangle.getElement();
    if (path) {
      path.setAttribute('pointer-events', 'all');
      path.style.cursor = 'move';
    }

    this.rectangle.on('mousedown', this.boundEvents.mousedown);
    this.map.on('mousemove', this.boundEvents.mousemove);
    this.map.on('mouseup', this.boundEvents.mouseup);

    this.initializeRadarBeam();
  }

  /**
   * Initialize the radar beam overlay
   */
  initializeRadarBeam() {
    const center = this.bounds.getCenter();

    // Create the radar icon
    this.radarIcon = L.divIcon({
      className: 'radar-icon',
      html: `<img src="/ui/static/icons/radar.png" style="width: 32px; height: 32px;">`,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    this.radarMarker = L.marker(center, {
      icon: this.radarIcon,
      interactive: false,
      pane: 'shadowPane' // Use shadowPane for background elements
    }).addTo(this.map);

    // Create the beam line
    this.beamLine = L.polyline([center, center], {
      color: 'rgba(0, 255, 0, 0.5)',
      weight: 2,
      opacity: 0.7,
      className: 'radar-beam-line',
      interactive: false, // Make the line non-interactive
      pane: 'shadowPane' // Use shadowPane for background elements
    }).addTo(this.map);

    // Ensure the rectangle stays on top and is interactive
    this.rectangle.bringToFront();
    const path = this.rectangle.getElement();
    if (path) {
      path.setAttribute('pointer-events', 'all');
      path.style.cursor = 'move';
    }

    this.startRadarAnimation();
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

    // Calculate the intersection point
    const endLat = center.lat + dy * minDist;
    const endLng = center.lng + dx * minDist;

    return L.latLng(endLat, endLng);
  }

  /**
   * Calculate the current angle based on elapsed time
   * @returns {number} The current angle in radians
   */
  getCurrentAngle() {
    const elapsedTime = (Date.now() - this.animationStartTime) / 1000;
    const angle = (-elapsedTime * this.rotationSpeed) % 360;
    return (angle * Math.PI) / 180;
  }

  /**
   * Update the beam position
   * @param {L.LatLngBounds} bounds - The current bounds
   */
  updateBeamPosition(bounds) {
    if (!this.beamLine || !this.radarMarker) return;

    const center = bounds.getCenter();
    const angleRad = this.getCurrentAngle();
    const endPoint = this.calculateIntersectionPoint(center, angleRad, bounds);
    
    // Update both the beam line and radar icon position
    this.beamLine.setLatLngs([center, endPoint]);
    this.radarMarker.setLatLng(center);
  }

  /**
   * Update the radar beam position
   */
  updateRadarBeam() {
    if (!this.rectangle) return;
    this.updateBeamPosition(this.rectangle.getBounds());
  }

  /**
   * Clean up resources and remove event listeners
   */
  destroy() {
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
    if (this.rectangle) {
      this.rectangle.setBounds(this.initialBounds);
      this.map.setMaxBounds(this.initialBounds);
      this.map.fitBounds(this.initialBounds, {
        animate: true,
        duration: 0.5,
        easeLinearity: 0.5,
        maxZoom: this.map.getZoom()
      });
      await this.updateServerBounds(this.initialBounds);
    }
  }

  /**
   * Handle mouse down event
   * @param {L.LeafletMouseEvent} e - The mouse event
   */
  onMouseDown(e) {
    if (e.originalEvent.target !== this.rectangle.getElement()) return;

    this.isDragging = true;
    this.startPoint = e.latlng;
    this.offset = {
      lat: e.latlng.lat - this.rectangle.getBounds().getCenter().lat,
      lng: e.latlng.lng - this.rectangle.getBounds().getCenter().lng
    };

    this.map.dragging.disable();
  }

  /**
   * Handle mouse move event
   * @param {L.LeafletMouseEvent} e - The mouse event
   */
  onMouseMove(e) {
    if (!this.isDragging) return;

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
  }

  /**
   * Handle mouse up event
   */
  onMouseUp() {
    if (!this.isDragging) return;

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
  }
}

/**
 * Initialize the draggable bounding box when the map is ready
 */
window.addEventListener('mapReady', async (e) => {
  const map = e.detail.map;
  if (!map || !map.getBounds) {
    console.error('Invalid map instance');
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