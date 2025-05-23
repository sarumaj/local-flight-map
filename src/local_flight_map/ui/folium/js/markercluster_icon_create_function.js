(cluster) => {
  var count = cluster.getChildCount();
  var size = Math.min(40 + (count * 2), 80);

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
          text-shadow: 0 0 3px white;
        ">${count}</div>
      </div>
    `,
    className: 'custom-cluster',
    iconSize: L.point(size, size)
  });
}