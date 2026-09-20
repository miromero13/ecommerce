type RuntimeConfig = {
  apiBaseUrl?: string;
  decartApiKey?: string;
  stripePublishableKey?: string;
};

declare global {
  interface Window {
    __runtimeConfig?: RuntimeConfig;
  }
}

const runtimeConfig = window.__runtimeConfig ?? {};

export const environment = {
  apiBaseUrl: runtimeConfig.apiBaseUrl || 'http://localhost:8000/api',
  decartApiKey: runtimeConfig.decartApiKey || '',
  stripePublishableKey: runtimeConfig.stripePublishableKey || '',
};
