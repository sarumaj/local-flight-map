// Draggable bounding box implementation
class DraggableBBox {
  constructor(map, initialBounds) {
    this.map = map;
    this.bounds = initialBounds;
    this.rectangle = null;
    this.isDragging = false;
    this.startPoint = null;
    this.offset = null;
    this.boundEvents = {
      mousedown: this.onMouseDown.bind(this),
      mousemove: this.onMouseMove.bind(this),
      mouseup: this.onMouseUp.bind(this)
    };

    this.initialize();
  }

  initialize() {
    // Create the rectangle
    this.rectangle = L.rectangle(this.bounds, {
      color: 'red',
      weight: 2,
      opacity: 0.7,
      fillOpacity: 0.05,
      className: 'draggable-rectangle'
    }).addTo(this.map);

    // Ensure the rectangle has the correct SVG properties
    const path = this.rectangle.getElement();
    if (path) {
      path.setAttribute('pointer-events', 'all');
      path.style.cursor = 'move';
    }

    // Add event listeners
    this.rectangle.on('mousedown', this.boundEvents.mousedown);
    this.map.on('mousemove', this.boundEvents.mousemove);
    this.map.on('mouseup', this.boundEvents.mouseup);
  }

  destroy() {
    if (this.rectangle) {
      this.rectangle.off('mousedown', this.boundEvents.mousedown);
      this.map.off('mousemove', this.boundEvents.mousemove);
      this.map.off('mouseup', this.boundEvents.mouseup);
      this.rectangle.remove();
    }
  }

  onMouseDown(e) {
    if (e.originalEvent.target !== this.rectangle.getElement()) return;

    this.isDragging = true;
    this.startPoint = e.latlng;
    this.offset = {
      lat: e.latlng.lat - this.rectangle.getBounds().getCenter().lat,
      lng: e.latlng.lng - this.rectangle.getBounds().getCenter().lng
    };

    // Prevent map dragging while moving the rectangle
    this.map.dragging.disable();
  }

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
  }

  onMouseUp() {
    if (!this.isDragging) return;

    this.isDragging = false;
    this.map.dragging.enable();
    this.updateMapBounds();
  }

  async updateMapBounds() {
    const bounds = this.rectangle.getBounds();
    this.map.setMaxBounds(bounds);

    try {
      const response = await fetch('/ui/bbox', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          bounds: {
            north: bounds.getNorth(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            west: bounds.getWest()
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Center the map on the new bounds
      this.map.fitBounds(bounds, {
        animate: true,     // Animate the transition
        duration: 0.5      // Animation duration in seconds
      });

      window.dispatchEvent(new CustomEvent('boundsUpdated', {
        detail: { bounds: bounds }
      }));
    } catch (error) {
      console.error('Error updating bounding box:', error);
      // Revert the map bounds on error
      this.map.setMaxBounds(null);
    }
  }
}

// Initialize draggable bbox when the map is ready
window.addEventListener('mapReady', async (e) => {
  const map = e.detail.map;
  if (!map || !map.getBounds) {
    console.error('Invalid map instance');
    return;
  }

  // Get initial bounds from the configuration endpoint
  let initialBounds;
  try {
    const response = await fetch('/ui/config');
    if (!response.ok) {
      throw new Error('Failed to fetch configuration');
    }
    const config = await response.json();

    if (config.bounds) {
      initialBounds = L.latLngBounds(
        L.latLng(config.bounds.south, config.bounds.west),
        L.latLng(config.bounds.north, config.bounds.east)
      );
    } else {
      throw new Error('No bounds in configuration');
    }
  } catch (error) {
    console.error('Error getting configuration:', error);
    // Fallback to default bounds if we can't get the configuration
    initialBounds = L.latLngBounds(
      L.latLng(-90, -180),
      L.latLng(90, 180)
    );
  }

  try {
    window.draggableBBox = new DraggableBBox(map, initialBounds);
  } catch (error) {
    console.error('Failed to initialize draggable bounding box:', error);
  }
}); 