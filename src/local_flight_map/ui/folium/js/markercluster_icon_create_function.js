/**
 * Create a custom icon for marker clusters
 * Generates a cloud icon with the number of markers in the cluster
 * @param {L.MarkerCluster} cluster - The marker cluster to create an icon for
 * @returns {L.DivIcon} A div icon containing the cluster visualization
 */
(cluster) => {
  var count = cluster.getChildCount();
  var size = Math.min(40 + (count * 2), 160);

  return L.divIcon({
    html: `
      <div class="marker-cluster" style="width: ${size}px; height: ${size}px;">
        <img src="/ui/static/icons/clouds.png" class="marker-cluster-icon" />
        <div class="marker-cluster-count" style="font-size: ${Math.min(16 + (count * 0.5), 24)}px;">${count}</div>
      </div>
    `,
    className: 'custom-cluster',
    iconSize: L.point(size, size)
  });
}