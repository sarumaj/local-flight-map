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
                    console.log("separator", separator);
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

// Call the function
hideLeafletOverlayControls();
