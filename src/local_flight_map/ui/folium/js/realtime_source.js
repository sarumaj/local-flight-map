(responseHandler, errorHandler) => {
  var url = '/aircrafts';

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      return data;
    })
    .then(responseHandler)
    .catch(errorHandler);
}