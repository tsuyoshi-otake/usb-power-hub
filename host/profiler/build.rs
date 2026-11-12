// Embeds app.manifest (Common Controls 6 visual styles, UTF-8 code page) with the MSVC linker
// itself, so no resource compiler and no build dependency is needed.
fn main() {
    let dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    println!("cargo:rerun-if-changed=app.manifest");
    println!("cargo:rustc-link-arg-bins=/MANIFEST:EMBED");
    println!("cargo:rustc-link-arg-bins=/MANIFESTINPUT:{dir}\\app.manifest");
}
