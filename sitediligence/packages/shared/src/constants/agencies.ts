/**
 * Federal agency names, acronyms, and reference URLs.
 */

export interface Agency {
  id: string;
  acronym: string;
  name: string;
  url: string;
  dataPortalUrl?: string;
  description?: string;
}

export const FEDERAL_AGENCIES: Agency[] = [
  {
    id: 'epa',
    acronym: 'EPA',
    name: 'U.S. Environmental Protection Agency',
    url: 'https://www.epa.gov',
    dataPortalUrl: 'https://www.epa.gov/enviro',
    description: 'Environmental regulations, cleanup sites, and permits',
  },
  {
    id: 'usace',
    acronym: 'USACE',
    name: 'U.S. Army Corps of Engineers',
    url: 'https://www.usace.army.mil',
    dataPortalUrl: 'https://permits.ops.usace.army.mil',
    description: 'Section 404 wetland permits and navigable waters',
  },
  {
    id: 'usfws',
    acronym: 'USFWS',
    name: 'U.S. Fish and Wildlife Service',
    url: 'https://www.fws.gov',
    dataPortalUrl: 'https://ecos.fws.gov/ecp',
    description: 'Endangered species, wetlands (NWI), and critical habitat',
  },
  {
    id: 'fema',
    acronym: 'FEMA',
    name: 'Federal Emergency Management Agency',
    url: 'https://www.fema.gov',
    dataPortalUrl: 'https://msc.fema.gov',
    description: 'Flood insurance rate maps and floodplain management',
  },
  {
    id: 'blm',
    acronym: 'BLM',
    name: 'Bureau of Land Management',
    url: 'https://www.blm.gov',
    dataPortalUrl: 'https://gis.blm.gov/arcgis/rest/services',
    description: 'Federal land ownership and mineral rights',
  },
  {
    id: 'usfs',
    acronym: 'USFS',
    name: 'U.S. Forest Service',
    url: 'https://www.fs.usda.gov',
    dataPortalUrl: 'https://data.fs.usda.gov/geodata',
    description: 'National forests and grasslands',
  },
  {
    id: 'nps',
    acronym: 'NPS',
    name: 'National Park Service',
    url: 'https://www.nps.gov',
    dataPortalUrl: 'https://irma.nps.gov/DataStore',
    description: 'National parks, monuments, and historic sites',
  },
  {
    id: 'nrcs',
    acronym: 'NRCS',
    name: 'Natural Resources Conservation Service',
    url: 'https://www.nrcs.usda.gov',
    dataPortalUrl: 'https://websoilsurvey.sc.egov.usda.gov',
    description: 'Soils data, hydric soils, and conservation programs',
  },
  {
    id: 'shpo',
    acronym: 'SHPO',
    name: 'State Historic Preservation Office',
    url: 'https://www.ncshpo.org',
    description: 'Section 106 review, historic properties, and archaeology',
  },
] as const;

export const AGENCY_BY_ID = Object.fromEntries(
  FEDERAL_AGENCIES.map((a) => [a.id, a])
) as Record<string, Agency>;
