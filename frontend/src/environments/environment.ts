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
  decartApiKey: runtimeConfig.decartApiKey || 'dct_ecommerce_QZtgfQYtsNcdcedjtHBqrfDMqkUMCFVEwKSzqdzTkVTgSPLlqGPwlOzXrDoxQFyX',
  stripePublishableKey: runtimeConfig.stripePublishableKey || 'pk_test_51PwuiM08hp2qIPTJ9P4c108993LSovebHw9lQQeABXF3zkN71Upef4jMuPMgLPjJDWOpL5N2I94cMtze0nOxg9IP00Jo5RqrJ7',
};
