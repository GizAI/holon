#!/usr/bin/env bash
set -e
python3 qfi_sigma.py --Lx 4 --Ly 4 --J 1.0 --h0 3.0 --dh 0.01 --iters 60 --dtype fp32 --device cuda --reorth_every 8 --normalize per_bond
