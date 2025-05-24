(responseHandler, errorHandler) => {
  var url = '/aircrafts';

  function fetchData() {
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        responseHandler(data);
      })
      .catch((error) => {
        errorHandler(error);
      });
  }

  fetchData();
}