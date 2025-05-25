/**
 * Handle marker cluster chunk processing progress
 * Shows and updates a progress bar for long-running marker processing
 * @param {number} processed - Number of markers processed
 * @param {number} total - Total number of markers to process
 * @param {number} elapsed - Time elapsed in milliseconds
 * @param {Array<L.Layer>} layersArray - Array of layers being processed
 */
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