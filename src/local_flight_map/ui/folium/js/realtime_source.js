/**
 * Real-time data source for aircraft positions
 * This script handles fetching aircraft data and responding to bounds updates
 * @param {Function} responseHandler - Callback function to handle successful responses
 * @param {Function} errorHandler - Callback function to handle errors
 * @returns {void}
 */
(responseHandler, errorHandler) => {
  var url = '/aircrafts';

  /**
   * Fetch aircraft data from the server
   * Makes a GET request to the /aircrafts endpoint and processes the response
   */
  function fetchData() {
    fetch(url, {
      credentials: 'include'
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        responseHandler(data);
      })
      .catch((error) => {
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