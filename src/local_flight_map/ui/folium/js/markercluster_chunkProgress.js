(processed, total, elapsed, layersArray) => {
  if (elapsed > 1000) {
    // if it takes more than a second to load, display the progress bar
    var progress = document.getElementById('progress');
    var progressBar = document.getElementById('progress-bar');
    if (progress && progressBar) {
      progress.style.display = 'block';
      progressBar.style.width = Math.round(processed / total * 100) + '%';
    }
    console.log(progress, progressBar);
  }
  if (processed === total) {
    // all markers processed - hide the progress bar
    var progress = document.getElementById('progress');
    if (progress) {
      progress.style.display = 'none';
    }
  }
}