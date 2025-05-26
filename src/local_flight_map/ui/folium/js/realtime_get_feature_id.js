/**
 * Get the unique identifier for a feature
 * @param {Object} feature - The feature object containing aircraft data
 * @param {Object} feature.properties - Properties of the feature
 * @param {string} feature.properties.icao24_code - The ICAO24 code of the aircraft
 * @returns {string} The ICAO24 code of the aircraft
 */
(feature) => {
  if (!feature) {
    console.warn('No feature provided to getFeatureId');
    return null;
  }

  try {
    if (!feature.properties) {
      console.warn('Feature has no properties');
      return null;
    }

    const id = feature.properties.icao24_code;
    if (!id) {
      console.warn('Feature has no icao24_code property');
      return null;
    }

    return id;
  } catch (error) {
    console.error('Error getting feature ID:', error);
    return null;
  }
}