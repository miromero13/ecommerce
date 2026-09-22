const defaultFirebaseConfig = {
  apiKey: 'AIzaSyCT2Zw540aDdCnnJKu15KvzuvqRhY66mC8',
  authDomain: 'universidad-app-3b08b.firebaseapp.com',
  projectId: 'universidad-app-3b08b',
  storageBucket: 'universidad-app-3b08b.firebasestorage.app',
  messagingSenderId: '652934622748',
  appId: '1:652934622748:web:4e1c1d3da90245010ef9d9',
};

const configFromUrl = new URL(self.location.href).searchParams;
const firebaseConfig = Object.fromEntries(
  Object.keys(defaultFirebaseConfig).map((key) => [key, configFromUrl.get(key) || defaultFirebaseConfig[key]]),
);

importScripts(
  'https://www.gstatic.com/firebasejs/12.19.0/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/12.19.0/firebase-messaging-compat.js',
);

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

function safeRoute(data) {
  const route = typeof data.route === 'string' ? data.route : '';
  if (/^\/app\/(notifications|cliente\/orders|cliente\/my-reservations|admin\/inventory|encargado\/inventory)$/.test(route)) {
    return route;
  }

  const id = typeof data.product_id === 'string' && /^[A-Za-z0-9_-]+$/.test(data.product_id)
    ? data.product_id
    : null;
  if (data.destination === 'product' && id) return `/app/cliente/products/${id}`;
  if (data.destination === 'orders') return '/app/cliente/orders';
  if (data.destination === 'reservations') return '/app/cliente/my-reservations';
  if (data.destination === 'inventory') return '/app/notifications';
  return '/notifications';
}

messaging.onBackgroundMessage((payload) => {
  const notification = payload.notification || {};
  const data = { ...(payload.data || {}) };
  self.registration.showNotification(
    notification.title || data.title || 'Notificación',
    {
      body: notification.body || data.body || '',
      data: { ...data, route: safeRoute(data) },
    },
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const route = safeRoute(event.notification.data || {});
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (clients) => {
      const client = clients.find((item) => 'focus' in item);
      if (client) {
        await client.focus();
        await client.navigate(route);
        return;
      }
      await self.clients.openWindow(route);
    }),
  );
});
