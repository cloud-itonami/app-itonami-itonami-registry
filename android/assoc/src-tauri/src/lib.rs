use tauri::WebviewWindowBuilder;
use tauri_plugin_opener::OpenerExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let config = &app.config().app.windows[0];
            let handle = app.handle().clone();
            WebviewWindowBuilder::from_config(app, config)?
                .on_navigation(move |url| {
                    if url.scheme() == "https"
                        && url.host_str() == Some("tauri.localhost")
                        && url.port().is_none()
                    {
                        return true;
                    }
                    if matches!(url.scheme(), "http" | "https")
                        && url.host_str().is_some()
                        && url.username().is_empty()
                        && url.password().is_none()
                    {
                        if let Err(error) = handle.opener().open_url(url.as_str(), None::<&str>) {
                            eprintln!("Could not open the citation browser: {error}");
                        }
                    }
                    false
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("failed to start the Itonami Registry");
}
