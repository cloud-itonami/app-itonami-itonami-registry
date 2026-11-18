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

  await import('../mobile-links.mjs');
  await import('./assoc.js');
} catch (error) {
  document.getElementById('status').textContent = '業界団体カタログを起動できませんでした。';
  console.error(error);
}
