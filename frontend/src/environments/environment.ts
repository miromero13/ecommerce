type FirebaseConfig = {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
};

type RuntimeConfig = {
  apiBaseUrl?: string;
  decartApiKey?: string;
  stripePublishableKey?: string;
  firebase?: Partial<FirebaseConfig>;
  firebaseVapidKey?: string;
};

declare global {
  interface Window {
    __runtimeConfig?: RuntimeConfig;
  }
}

const runtimeConfig = window.__runtimeConfig ?? {};

const defaultFirebaseConfig: FirebaseConfig = {
  apiKey: 'AIzaSyCT2Zw540aDdCnnJKu15KvzuvqRhY66mC8',
  authDomain: 'universidad-app-3b08b.firebaseapp.com',
  projectId: 'universidad-app-3b08b',
  storageBucket: 'universidad-app-3b08b.firebasestorage.app',
  messagingSenderId: '652934622748',
  appId: '1:652934622748:web:4e1c1d3da90245010ef9d9',
};

export const environment = {
  apiBaseUrl: runtimeConfig.apiBaseUrl || 'http://localhost:8000/api',
  decartApiKey: runtimeConfig.decartApiKey || 'dct_ecommerce_QZtgfQYtsNcdcedjtHBqrfDMqkUMCFVEwKSzqdzTkVTgSPLlqGPwlOzXrDoxQFyX',
  stripePublishableKey: runtimeConfig.stripePublishableKey || 'pk_test_51PwuiM08hp2qIPTJ9P4c108993LSovebHw9lQQeABXF3zkN71Upef4jMuPMgLPjJDWOpL5N2I94cMtze0nOxg9IP00Jo5RqrJ7',
  firebase: { ...defaultFirebaseConfig, ...runtimeConfig.firebase },
  firebaseVapidKey:
    runtimeConfig.firebaseVapidKey ||
    'BEdsfVaDFcWM77gFckoEXc8hKJAce1UGViKnvX7zehZEOrACIf6ILsRKIxg6ze7550wwI8guRHQ6EmhWmoPjqSE',
};
