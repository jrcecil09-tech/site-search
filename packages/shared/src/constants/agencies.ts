export interface FederalAgency {
  acronym: string;
  name: string;
  url: string;
  relevantPrograms: string[];
}

export const FEDERAL_AGENCIES: FederalAgency[] = [
  {
    acronym: 'EPA',
    name: 'U.S. Environmental Protection Agency',
    url: 'https://www.epa.gov',
    relevantPrograms: ['CERCLA / Superfund', 'RCRA', 'TSCA', 'Clean Water Act', 'ECHO'],
  },
  {
    acronym: 'USACE',
    name: 'U.S. Army Corps of Engineers',
    url: 'https://www.usace.army.mil',
    relevantPrograms: ['Section 404 Wetlands', 'Section 10 Navigable Waters', 'NWP'],
  },
  {
    acronym: 'USFWS',
    name: 'U.S. Fish and Wildlife Service',
    url: 'https://www.fws.gov',
    relevantPrograms: ['ESA Section 7', 'NWI Wetlands', 'IPaC'],
  },
  {
    acronym: 'FEMA',
    name: 'Federal Emergency Management Agency',
    url: 'https://www.fema.gov',
    relevantPrograms: ['NFIP', 'FIRM Flood Maps', 'Floodplain Management'],
  },
  {
    acronym: 'NRCS',
    name: 'Natural Resources Conservation Service',
    url: 'https://www.nrcs.usda.gov',
    relevantPrograms: ['Web Soil Survey', 'Hydric Soils', 'Wetland Determination'],
  },
  {
    acronym: 'SHPO',
    name: 'State Historic Preservation Office',
    url: 'https://ncshpo.org',
    relevantPrograms: ['Section 106', 'NHPA', 'National Register of Historic Places'],
  },
  {
    acronym: 'BLM',
    name: 'Bureau of Land Management',
    url: 'https://www.blm.gov',
    relevantPrograms: ['NEPA', 'Cultural Resources', 'Land Use Planning'],
  },
  {
    acronym: 'NPS',
    name: 'National Park Service',
    url: 'https://www.nps.gov',
    relevantPrograms: ['NHPA', 'National Register', 'Historic Tax Credits'],
  },
  {
    acronym: 'NOAA',
    name: 'National Oceanic and Atmospheric Administration',
    url: 'https://www.noaa.gov',
    relevantPrograms: ['Coastal Zone Management', 'Essential Fish Habitat', 'CZMA'],
  },
];

export const AGENCY_ACRONYMS = FEDERAL_AGENCIES.map((a) => a.acronym);

export const AGENCIES_BY_ACRONYM: Record<string, FederalAgency> = Object.fromEntries(
  FEDERAL_AGENCIES.map((a) => [a.acronym, a]),
);
