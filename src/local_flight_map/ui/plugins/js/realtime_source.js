/**
 * Real-time data source for aircraft positions
 * This script handles fetching aircraft data and responding to bounds updates
 * @param {Function} responseHandler - Callback function to handle successful responses
 * @param {Function} errorHandler - Callback function to handle errors
 * @returns {void}
 */
(responseHandler, errorHandler) => {
  // Create loading overlay and spinner elements only once
  let overlay = document.querySelector('.loading-overlay');
  let spinner = document.querySelector('.loading-spinner');

  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    document.body.appendChild(overlay);
  }

  if (!spinner) {
    spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    document.body.appendChild(spinner);
  }

  // Add spinner animation if not already added
  if (!document.querySelector('#spinner-animation')) {
    const style = document.createElement('style');
    style.id = 'spinner-animation';
    style.textContent = `
      @keyframes spin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }

  let spinnerTimeout = null;
  let fetchStartTime = null;
  let isSpinnerVisible = false;

  /**
   * Show the loading spinner
   */
  function showSpinner() {
    // Don't show spinner if cookie consent modal is visible or if already visible
    if (document.getElementById('cookie-consent-modal') || isSpinnerVisible) {
      return;
    }
    overlay.style.display = 'block';
    spinner.style.display = 'block';
    isSpinnerVisible = true;
  }

  /**
   * Hide the loading spinner
   */
  function hideSpinner() {
    if (spinnerTimeout) {
      clearTimeout(spinnerTimeout);
      spinnerTimeout = null;
    }
    overlay.style.display = 'none';
    spinner.style.display = 'none';
    isSpinnerVisible = false;
    fetchStartTime = null;
  }

  /**
   * Fetch aircraft data from the server
   * Makes a GET request to the /service/aircrafts endpoint and processes the response
   */
  function fetchData() {
    // Clear any existing timeout and hide spinner
    hideSpinner();

    // Record fetch start time
    fetchStartTime = Date.now();

    // Get the current config to determine the interval
    window.getConfig().then(config => {
      if (!config || !config.interval) {
        console.warn('Invalid config for spinner timeout:', config);
        return;
      }

      // Set a timeout to show the spinner if loading takes longer than the interval
      spinnerTimeout = setTimeout(() => {
        // Only show spinner if the fetch is still ongoing
        if (fetchStartTime) {
          showSpinner();
        }
      }, config.interval);
    }).catch(error => {
      console.error('Error getting config for spinner timeout:', error);
    });

    fetch('/service/aircrafts', {
      credentials: 'include'
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        // Only hide spinner if it was shown (meaning fetch took longer than interval)
        if (spinnerTimeout) {
          hideSpinner();
        }
        responseHandler(data);
      })
      .catch((error) => {
        // Only hide spinner if it was shown (meaning fetch took longer than interval)
        if (spinnerTimeout) {
          hideSpinner();
        }
        errorHandler(error);
      });
  }

  // Listen for bounds updates
  window.addEventListener('boundsUpdated', function (event) {
    fetchData();
  });

  // Initial fetch
  fetchData();
}