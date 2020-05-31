# Arline Benchmarks

**Arline Benchmarks** platform allows to benchmark various algorithms for quantum circuit mapping/compression against
each other on a list of predefined hardware types and target circuit classes.

## Installation

```console
$ pip3 install arline-benchmarks
```

Alternatively, Arline Benchmarks can be installed locally in the editable mode.
Clone Arline Benchmarks repository, `cd` to the source directory:

Clone repository, `cd` to the source directory:
```console
$ git clone https://github.com/ArlineQ/arline_benchmarks.git
$ cd arline_benchmarks
```

We recommend to install Arline Benchmarks in [virtual environment](https://virtualenv.pypa.io/en/latest/).

```console
$ virtualenv venv
$ source venv/bin/activate
```

If `virtualenv` is not installed on your machine, run

```console
$ pip3 install virtualenv
```

Next in order to install the Arline Benchmarks platform execute:

```console
$ pip3 install .
```

Alternatively, Arline Benchmarks can be installed in the editable mode:

```console
$ pip3 install -e .
```

### TeXLive installation

Automated generation of LaTeX report is an essential part of Arline Benchmarks.
In order to enable full functionality of Arline Benchmarks, you will need to install TeXLive distribution.

#### Ubuntu or Debian Linux:

To install TeXLive simply run in terminal:

```console
$ sudo apt install texlive-latex-extra
```

#### Windows:

On Windows, TeXLive can be installed by downloading source code from [official website](https://www.tug.org/texlive/)
and following installation instructions.


#### MacOS:

On MacOS simply install MacTex distribution from the [official website](https://www.tug.org/mactex/).

#### Alternative solution for Linux/Windows/MacOS:

TeXLive can be also installed as a part of the MikTex package by downloading and installing source code from 
https://miktex.org. TeXworks frontend is not required and can be ignored.



## Getting Started

### Benchmark Example Run

In order to run your first benchmarking experiment execute following commands
```console
$ cd arline_benchmarks/configs/compression/
$ bash run_and_plot.sh
```

Bash script `run_and_plot.sh` executes

1. `scripts/arline-benchmarks-runner` - runs benchmarking experiment and saves result to `results/output
/gate_chain_report.csv`
2. `arline_benhmarks/reports/plot_benchmarks.py` - generates plots with metrics based on `results/output
/gate_chain_report.csv` to `results/output/figure`
3. `scripts/arline-latex-report-generator` - generates `results/latex/benchmark_report.tex` and
`results/latex/benchmark_report.pdf` report files with benchmarking results.

Configuration file `configs/compression/config.jsonnet` contains full description of benchmarking experiments.


### Generate plots with benchmark metrics

To re-draw plots execute (from `arline_benchmarks/configs/compression/`)
```console
$ bash plot.sh
```

### Generate LaTeX report

To re-generate LaTeX report based on the last benchmarking run (from `arline_benchmarks/configs/compression/`)

``` console
$ arline-latex-report-generator -i results -o results
```

### How to create a custom compilation pipeline?


The key element of Arline Benchmarks is the concept of **compilation pipeline**.
A pipeline is a sequence of compilation `stages: [stage1, stage2, stage3, ..]`.

A typical pipeline consists of the following stages:

* Generation of a target circuit
* Mapping of logical qubits to physical qubits
* Qubit routing for a particular hardware coupling topology
* Circuit compression by applying circuit identities
* Rebase to the final hardware gate set

You can easily create a custom compilation pipeline by stacking individual stages (that might correspond to different
compiler providers). A pipeline can consist of an unlimited number of compilation stages combined in an arbitrary order.
The only exceptions are the first stage `target_analysis` and the last `gateset rebase stage` (optional).


### Configuration file .jsonnet

Pipelines should be specified in the main configuration file .jsonnet.
An example of a configuration file is located in `configs/compression/config.jsonnet`.

* Function `local pipelines_set(target, hardware, plot_group)` defines a list of compilation pipelines to be benchmarked, `[pipeline1, pipeline2, ...]`.

Each `pipeline_i = {...}` is represented as a dictionary that contains a description of the pipeline and a list of
 compilation stages.

* Target circuits generation is defined in .jsonnet functions `local random_chain_cliford_t_target(...)` and `local random_chain_cx_u3_target(...)`.

* Benchmarking experiment specifications are defined at the end of the config file in the dictionary with keys `{pipelines: ..., plotter: ...}`

## API documentation

To generate HTML API documentation, run below command:

```console
$ cd docs/
$ make html
```

## Running tests

To run unit-tests and check installed dependencies:

```console
$ tox
```

## Folder structure

```
arline_benchmarks
│
├── configs                      # configuration files
│   └── compression              # config .jsonnet file and .sh scripts  
│
├── circuits                     # qasm circuits dataset
│
├── scripts                      # run files
│
├── arline_benchmarks            # platform classes
│   ├── config_parser            # parser of pipeline configuration
│   ├── engine                   # pipeline engine
│   ├── metrics                  # metrics for pipeline comparison
│   ├── reports                  # LaTeX report generator
│   ├── strategies               # list of strategies for mapping/compression/rebase
│   └── targets                  # target generator
│
├── docs                         # documentation
│
└── test                         # tests
    ├── qasm_files               # .qasm files for test
    └── targets                  # test for targets module
```
