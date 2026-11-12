`default_nettype none
`timescale 1ns / 1ps
`ifndef NN
`define NN 8
`endif
`ifndef NI
`define NI 4
`endif
`ifndef DEPTH
`define DEPTH 8
`endif
module tb_snn ();
  initial begin
    $dumpfile("tb_snn.fst");
    $dumpvars(0, tb_snn);
    #1;
  end
  localparam NN = `NN, NI = `NI, DEPTH = `DEPTH;
  localparam NR = NN + NI;
  localparam RW = $clog2(NR), JW = $clog2(NN), IW = (NI <= 2) ? 1 : $clog2(NI);

  reg clk = 0, rst_n = 0;
  reg w_we = 0; reg [RW-1:0] w_row = 0; reg [JW-1:0] w_col = 0; reg [3:0] w_data = 0;
  reg thr_we = 0; reg [11:0] thr_data = 0; reg leak_we = 0; reg [6:0] leak_data = 0;
  reg in_valid = 0; reg [IW-1:0] in_line = 0; reg tref = 0;
  wire busy, spk_pulse; wire [NN-1:0] spk_last; wire [JW-1:0] spk_idx; wire [12*NN-1:0] state_flat;

  snn_tiny #(.NN(NN), .NI(NI), .DEPTH(DEPTH)) dut (
    .clk(clk), .rst_n(rst_n),
    .w_we(w_we), .w_row(w_row), .w_col(w_col), .w_data(w_data),
    .thr_we(thr_we), .thr_data(thr_data), .leak_we(leak_we), .leak_data(leak_data),
    .in_valid(in_valid), .in_line(in_line), .tref(tref),
    .busy(busy), .spk_last(spk_last), .spk_pulse(spk_pulse), .spk_idx(spk_idx), .state_flat(state_flat));
endmodule
