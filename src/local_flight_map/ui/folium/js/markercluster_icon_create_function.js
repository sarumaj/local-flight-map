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
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size}px;
      ">
        <img src="/ui/static/icons/clouds.png" 
          style="
            width: 100%;
            height: 100%;
            opacity: 0.8;
            filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8));
          "
        />
        <div style="
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: ${Math.min(16 + (count * 0.5), 24)}px;
          font-weight: bold;
          color: #333;
          text-shadow: 
            0 0 3px white,
            0 0 6px rgba(255, 255, 255, 0.8),
            0 0 9px rgba(255, 255, 255, 0.6);
        ">${count}</div>
      </div>
    `,
    className: 'custom-cluster',
    iconSize: L.point(size, size)
  });
}