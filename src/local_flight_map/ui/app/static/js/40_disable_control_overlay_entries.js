/**
 * Hide the overlay controls in the Leaflet map.
 * @param {void}
 * @returns {void}
 */
function hideLeafletOverlayControls() {
    // Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        // First find the layers list
        const layersList = document.querySelector('.leaflet-control-layers-list');
        if (layersList) {
            // Find the overlay controls within the list
            const overlayControls = layersList.querySelector('.leaflet-control-layers-overlays');
            if (overlayControls) {
                // Hide the overlay controls
                overlayControls.style.display = 'none';
                
                // Check if separator is the last visible child
                const separator = layersList.querySelector('.leaflet-control-layers-separator');
                if (separator) {
                    // Get all direct children of the list
                    const children = Array.from(layersList.children);
                    // Filter out hidden elements
                    const visibleChildren = children.filter(child => 
                        window.getComputedStyle(child).display !== 'none'
                    );
                    
                    // Check if separator is the last visible child
                    const lastVisibleChild = visibleChildren[visibleChildren.length - 1];
                    if (lastVisibleChild === separator) {
                        separator.style.display = 'none';
                    }
                }
            }
        }
    });
}

function disableControlOverlayEntries() {
  try {
    // Get all control overlay entries
    const entries = document.querySelectorAll('.leaflet-control-layers-overlays label');
    if (!entries || entries.length === 0) {
      console.warn('No control overlay entries found');
      return;
    }

    // Disable each entry
    entries.forEach(entry => {
      try {
        if (!entry) {
          console.warn('Invalid entry element');
          return;
        }

        // Disable the checkbox
        const checkbox = entry.querySelector('input[type="checkbox"]');
        if (!checkbox) {
          console.warn('No checkbox found in entry:', entry);
          return;
        }
        checkbox.disabled = true;

        // Add disabled style
        entry.style.opacity = '0.5';
        entry.style.cursor = 'not-allowed';
      } catch (error) {
        console.error('Error processing entry:', error);
      }
    });
  } catch (error) {
    console.error('Error disabling control overlay entries:', error);
  }
}

// Call the function
hideLeafletOverlayControls();

// Export the function
window.disableControlOverlayEntries = disableControlOverlayEntries;
