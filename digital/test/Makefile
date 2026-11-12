# snn_tiny against the snn_gym model:   make            (RTL, Icarus, cocotb)
#   make GOLDEN=golden_8x4_d3.txt DEFS="-DDEPTH=3"      the FIFO-full case
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
FST ?= -fst
SRC_DIR = $(PWD)/../src
DEFS ?=
COMPILE_ARGS += $(DEFS)
VERILOG_SOURCES += $(SRC_DIR)/snn_tiny.v $(PWD)/tb_snn.v
TOPLEVEL = tb_snn
COCOTB_TEST_MODULES = test_snn
include $(shell cocotb-config --makefiles)/Makefile.sim
