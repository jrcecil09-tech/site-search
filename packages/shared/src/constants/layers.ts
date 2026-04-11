import type { LayerType } from '../types/layers.js';

export const LAYER_COLORS: Record<LayerType, string> = {
  parcel:      '#F59E0B',
  zoning:      '#8B5CF6',
  flood:       '#3B82F6',
  wetland:     '#10B981',
  soil:        '#92400E',
  aerial:      '#6B7280',
  topographic: '#D97706',
  utility:     '#EF4444',
  cultural:    '#EC4899',
  custom:      '#64748B',
};

export const LAYER_FILL_OPACITY: Record<LayerType, number> = {
  parcel:      0.1,
  zoning:      0.2,
  flood:       0.3,
  wetland:     0.25,
  soil:        0.2,
  aerial:      1.0,
  topographic: 0.15,
  utility:     0.0,
  cultural:    0.1,
  custom:      0.15,
};

export const LAYER_CATEGORIES: Record<string, LayerType[]> = {
  'Environmental': ['flood', 'wetland', 'soil'],
  'Land Use':      ['parcel', 'zoning'],
  'Imagery':       ['aerial', 'topographic'],
  'Infrastructure':['utility'],
  'Cultural':      ['cultural'],
  'Custom':        ['custom'],
};

export const LAYER_DISPLAY_NAMES: Record<LayerType, string> = {
  parcel:      'Parcel Boundaries',
  zoning:      'Zoning Districts',
  flood:       'FEMA Flood Zones',
  wetland:     'NWI Wetlands',
  soil:        'NRCS Soils',
  aerial:      'Aerial Imagery',
  topographic: 'Topographic',
  utility:     'Utilities',
  cultural:    'Cultural Resources',
  custom:      'Custom Layer',
};
