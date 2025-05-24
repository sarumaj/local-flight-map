(responseHandler, errorHandler) => {
  var url = '/aircrafts';

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

  fetchData();
}