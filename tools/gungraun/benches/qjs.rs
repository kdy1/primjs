use gungraun::prelude::*;
use gungraun::{Bench, BinaryBenchmark};

binary_benchmark_group!(
    name = engine;
    benchmarks = |group: &mut BinaryBenchmarkGroup| {
        let binary = std::env::var("PRIMJS_QJS")
            .expect("PRIMJS_QJS must name an absolute qjs path");
        assert!(std::path::Path::new(&binary).is_absolute());
        let manifest = std::env::var("PRIMJS_WORKLOADS")
            .expect("PRIMJS_WORKLOADS must name the workload manifest");
        let manifest = std::fs::read_to_string(manifest).expect("Cannot read workload manifest");
        let mut benchmark = BinaryBenchmark::new("qjs");
        assert!(!manifest.is_empty(), "No JavaScript workloads found");
        for line in manifest.lines() {
            let (case, path) = line.split_once('\t').expect("Expected ID and absolute JS path");
            assert!(std::path::Path::new(path).is_absolute());
            benchmark.bench(Bench::new(case).command(
                gungraun::Command::new(&binary).arg(path).build(),
            ));
        }
        group.binary_benchmark(benchmark);
    }
);
main!(binary_benchmark_groups = engine);
