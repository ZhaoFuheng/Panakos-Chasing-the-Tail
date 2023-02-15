# Panakos-p4
This is a p4 implementation of panakos

## Description
- `panakos.p4` file contains the p4 implementation of Panakos
- `send_traffic.py` python file to send traffic to network switch after reading test case file.
- `recieve_traffic.py` python file to recieve traffic from a network switch and write results to test case files.
- `create_test_zipf.py` python file to create a test case using zipf distribution.
- `evaluate.py` python file to generate CDF of feature using results from `recieve_trafic.py` and evaluates it.

## Usage
- Build and run p4 code on Tofino ASIC.
- Use other provided scripts to create test cases, send and recieve network traffic, and evaluate the results.

## Credits

The P4 implementation of panakos is build on top of [CocoSketch](https://github.com/yindazhang/CocoSketch/tree/main/P4) by yindazhang

