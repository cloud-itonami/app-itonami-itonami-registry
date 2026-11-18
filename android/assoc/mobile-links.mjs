// Android WebView lacks Tauri's new-window and download callbacks.
document.addEventListener('click', (event) => {
  if (!event.isTrusted || !(event.target instanceof Element)) return;
  const anchor = event.target.closest('a[href]');
  if (!anchor) return;

  if (anchor.origin !== location.origin) {
    if (anchor.target === '_blank') anchor.target = '_self';
    return;
  }
  if (anchor.hasAttribute('download') &&
      /^\/assoc\/source\/[a-z0-9-]+\/datascript-tx\.edn$/.test(anchor.pathname)) {
    anchor.removeAttribute('download');
    anchor.pathname += '.html';
  }
}, {capture: true});
