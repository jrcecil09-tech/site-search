/**
 * Observation categories used across field data collection.
 */

export const OBSERVATION_CATEGORIES = [
  {
    id: 'environmental-hazard',
    name: 'Environmental Hazard',
    description: 'Potential contamination, spills, or hazardous materials',
    color: '#e74c3c',
    icon: 'warning',
    sortOrder: 1,
  },
  {
    id: 'wetland-indicator',
    name: 'Wetland Indicator',
    description: 'Hydric soils, hydrophytic vegetation, or wetland hydrology',
    color: '#27ae60',
    icon: 'water',
    sortOrder: 2,
  },
  {
    id: 'cultural-resource',
    name: 'Cultural Resource',
    description: 'Archaeological sites, historic structures, or artifacts',
    color: '#8e44ad',
    icon: 'landmark',
    sortOrder: 3,
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure',
    description: 'Utilities, roads, drainage, or site improvements',
    color: '#3498db',
    icon: 'build',
    sortOrder: 4,
  },
  {
    id: 'vegetation',
    name: 'Vegetation',
    description: 'Plant species, invasive plants, or land cover',
    color: '#2ecc71',
    icon: 'nature',
    sortOrder: 5,
  },
  {
    id: 'wildlife',
    name: 'Wildlife',
    description: 'Wildlife sightings, habitat, or species of concern',
    color: '#f39c12',
    icon: 'pets',
    sortOrder: 6,
  },
  {
    id: 'soil',
    name: 'Soil Condition',
    description: 'Soil type, erosion, compaction, or contamination',
    color: '#795548',
    icon: 'terrain',
    sortOrder: 7,
  },
  {
    id: 'general',
    name: 'General',
    description: 'General site notes and observations',
    color: '#95a5a6',
    icon: 'note',
    sortOrder: 8,
  },
] as const;

export type ObservationCategoryId = (typeof OBSERVATION_CATEGORIES)[number]['id'];
