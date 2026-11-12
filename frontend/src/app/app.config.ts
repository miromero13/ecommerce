import { ApplicationConfig, isDevMode, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';
import { provideNativeDateAdapter } from '@spartan-ng/brain/date-time';

import { routes } from './app.routes';
import { authInterceptor } from './features/shared/interceptors/auth.interceptor';
import { assetUrlInterceptor } from './core/interceptors/asset-url.interceptor';
import { catalogCacheInterceptor } from './core/interceptors/catalog-cache.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor, assetUrlInterceptor, catalogCacheInterceptor])),
    provideNativeDateAdapter(),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
};
