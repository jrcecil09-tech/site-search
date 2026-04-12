export interface ObservationCategory {
  id: string;
  label: string;
  subcategories: string[];
  defaultSeverity: 'info' | 'low' | 'moderate' | 'high' | 'critical';
}

export const OBSERVATION_CATEGORIES: ObservationCategory[] = [
  {
    id: 'hazmat',
    label: 'Hazardous Materials',
    defaultSeverity: 'high',
    subcategories: [
      'AST / UST',
      'Drums / Containers',
      'Staining / Discoloration',
      'Odors',
      'PCBs',
      'Asbestos-Containing Materials',
      'Lead Paint',
    ],
  },
  {
    id: 'wetland',
    label: 'Wetlands & Waters',
    defaultSeverity: 'moderate',
    subcategories: [
      'Potential Wetland Indicator',
      'Ordinary High Water Mark',
      'Isolated Water Feature',
      'Hydric Soils',
      'Hydrophytic Vegetation',
    ],
  },
  {
    id: 'cultural',
    label: 'Cultural Resources',
    defaultSeverity: 'moderate',
    subcategories: [
      'Historic Structure',
      'Archaeological Feature',
      'Human Remains',
      'Native American Cultural Site',
    ],
  },
  {
    id: 'biological',
    label: 'Biological',
    defaultSeverity: 'moderate',
    subcategories: [
      'Listed Species Habitat',
      'Invasive Species',
      'Critical Habitat',
      'Nesting Activity',
    ],
  },
  {
    id: 'access',
    label: 'Site Access & Conditions',
    defaultSeverity: 'info',
    subcategories: [
      'Access Issue',
      'Fencing / Security',
      'Vegetation Obstruction',
      'Flooding / Ponding',
    ],
  },
  {
    id: 'utilities',
    label: 'Utilities',
    defaultSeverity: 'low',
    subcategories: [
      'Overhead Power Lines',
      'Underground Utilities',
      'Utility Vault / Box',
      'Active Well',
    ],
  },
  {
    id: 'general',
    label: 'General',
    defaultSeverity: 'info',
    subcategories: ['Note', 'Photo Documentation', 'Measurement', 'Other'],
  },
];

export const CATEGORY_IDS = OBSERVATION_CATEGORIES.map((c) => c.id);
