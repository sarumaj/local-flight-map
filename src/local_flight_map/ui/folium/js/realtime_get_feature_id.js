/**
 * Get the unique identifier for a feature
 * @param {Object} feature - The feature object containing aircraft data
 * @param {Object} feature.properties - Properties of the feature
 * @param {string} feature.properties.icao24_code - The ICAO24 code of the aircraft
 * @returns {string} The ICAO24 code of the aircraft
 */
(feature) => { return feature.properties.icao24_code }