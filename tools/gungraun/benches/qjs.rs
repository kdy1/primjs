use gungraun::prelude::*;

#[binary_benchmark]
#[bench::arithmetic("arithmetic")]
#[bench::objects("objects")]
#[bench::strings("strings")]
fn qjs(case: &str) -> gungraun::Command {
    let binary = std::env::var("PRIMJS_QJS").expect("PRIMJS_QJS must name an absolute qjs path");
    assert!(std::path::Path::new(&binary).is_absolute());
    gungraun::Command::new(binary)
        .arg(format!("{}/fixtures/{case}.js", env!("CARGO_MANIFEST_DIR")))
        .build()
}

binary_benchmark_group!(name = engine; benchmarks = qjs);
main!(binary_benchmark_groups = engine);
