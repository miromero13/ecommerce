import { getCountryDataList } from 'countries-list';

export interface CountryOption {
  name: string;
  code: string;
  currency: string;
}

export const COUNTRIES_LIST: CountryOption[] = getCountryDataList()
  .map((c) => ({
    name: c.name,
    code: c.iso2,
    currency: c.currency?.[0] || 'USD',
  }))
  .sort((a, b) => a.name.localeCompare(b.name));

export const CURRENCIES_LIST: string[] = Array.from(
  new Set(COUNTRIES_LIST.map((c) => c.currency).filter(Boolean)),
).sort();
