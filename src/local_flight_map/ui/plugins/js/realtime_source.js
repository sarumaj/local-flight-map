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
   * Show error message overlay
   * @param {string} message - The error message to display
   */
  function showErrorOverlay(message) {
    // Remove existing error overlay if present
    const existingError = document.querySelector('.error-overlay');
    if (existingError) {
      existingError.remove();
    }

    // Create error overlay
    const errorOverlay = document.createElement('div');
    errorOverlay.className = 'error-overlay';

    const errorContent = document.createElement('div');
    errorContent.className = 'error-content';

    const errorIcon = document.createElement('div');
    errorIcon.className = 'error-icon';
    errorIcon.innerHTML = '⚠️';

    const errorTitle = document.createElement('h2');
    errorTitle.className = 'error-title';
    errorTitle.textContent = 'Service Unavailable';

    const errorMessage = document.createElement('p');
    errorMessage.className = 'error-message';
    errorMessage.textContent = message;

    const errorButtons = document.createElement('div');
    errorButtons.className = 'error-buttons';

    const retryButton = document.createElement('button');
    retryButton.className = 'error-button retry';
    retryButton.textContent = 'Retry';

    const closeButton = document.createElement('button');
    closeButton.className = 'error-button close';
    closeButton.textContent = 'Close';

    const githubButton = document.createElement('button');
    githubButton.className = 'error-button github';
    githubButton.textContent = 'Open GitHub Issue';
    githubButton.onclick = () => {
      window.open('https://github.com/sarumaj/local-flight-map/issues', '_blank');
    };

    retryButton.onclick = () => {
      errorOverlay.remove();
      fetchData();
    };

    closeButton.onclick = () => {
      errorOverlay.remove();
    };

    errorButtons.appendChild(retryButton);
    errorButtons.appendChild(closeButton);
    errorButtons.appendChild(githubButton);
    errorContent.appendChild(errorIcon);
    errorContent.appendChild(errorTitle);
    errorContent.appendChild(errorMessage);
    errorContent.appendChild(errorButtons);
    errorOverlay.appendChild(errorContent);
    document.body.appendChild(errorOverlay);
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
        // Check for X-Status-Code header first
        const statusCode = response.headers.get('X-Status-Code');

        if (statusCode === '500') {
          throw new Error('BACKEND_SERVICE_UNAVAILABLE');
        }

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

        // Handle specific backend service unavailable error
        if (error.message === 'BACKEND_SERVICE_UNAVAILABLE') {
          showErrorOverlay('The backend service providing the real-time data is not available. Please try again later or contact the developer by opening an issue on GitHub if the problem persists.');
        } else {
          errorHandler(error);
        }
      });
  }

  // Listen for bounds updates
  window.addEventListener('boundsUpdated', function (event) {
    fetchData();
  });

  // Initial fetch
  fetchData();
}