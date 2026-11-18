import {
  applyOfflineClientPolicy,
  createClientConsentHost,
  createClientOperationBroker,
} from './kotoba-client-runtime.mjs';

try {
  const runtime = JSON.parse(document.getElementById('assoc-client-runtime').textContent);
  const consentHost = createClientConsentHost();
  const broker = createClientOperationBroker({runtime, consentHost});
  if (broker.operations.length !== 0) {
    throw new Error('Association viewer unexpectedly has external operations');
  }
  applyOfflineClientPolicy();

  // Android WebView does not support Tauri's new-window callback. Let a
  // reader's link activate the native navigation delegate in this window.
  document.addEventListener('click', (event) => {
    if (!event.isTrusted || !(event.target instanceof Element)) return;
    const anchor = event.target.closest('a[target="_blank"]');
    if (anchor && anchor.origin !== location.origin) {
      anchor.target = '_self';
    }
  }, {capture: true});
  await import('./assoc.js');
} catch (error) {
  document.getElementById('status').textContent = '業界団体カタログを起動できませんでした。';
  console.error(error);
}
