`default_nettype none
`timescale 1ns / 1ps
// dig_top RTL (instance dut, so test_dig.py runs unchanged) next to the hardened netlist (dig_top_gl, same inputs): every output is compared
// 2 ns after every falling clock edge (the testbench drives its inputs at the edge); mism counts the differences (!== so X against 0 counts too).
// Not compared while rst_n = 0: a cocotb test starts by restarting the clock and asserting reset in the same time step as a clock edge, and the
// RTL and the netlist resolve that race differently for one or two edges (seen on the heartbeat counter hb, which has a synchronous reset).
// The outputs after reset release, hb included, are compared on every edge.
module tb_dig ();
  initial begin
    $dumpfile("tb_dig.fst");
    $dumpvars(0, tb_dig);
    #1;
  end
  reg clk = 0, rst_n = 0, ena = 1;
  reg [7:0] ui_in = 0, uio_in = 0;
  wire [7:0] uo_out, uio_out, uio_oe, uo_gl, uio_out_gl, uio_oe_gl;
  wire [3:0] a_sel0, a_sel1, a_selb0, a_selb1, g_sel0, g_sel1, g_selb0, g_selb1;
  wire osc_en, adc_en, g_osc_en, g_adc_en;
  reg osc_in = 0, por_n_in = 0;
  integer mism = 0;
  dig_top #(.NN(4), .NI(2), .DEPTH(4)) dut (
    .clk(clk), .rst_n(rst_n), .ena(ena), .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
    .a_sel0(a_sel0), .a_sel1(a_sel1), .a_selb0(a_selb0), .a_selb1(a_selb1), .osc_en(osc_en), .adc_en(adc_en), .osc_in(osc_in), .por_n_in(por_n_in));
  dig_top_gl gl (
    .clk(clk), .rst_n(rst_n), .ena(ena), .ui_in(ui_in), .uo_out(uo_gl), .uio_in(uio_in), .uio_out(uio_out_gl), .uio_oe(uio_oe_gl),
    .a_sel0(g_sel0), .a_sel1(g_sel1), .a_selb0(g_selb0), .a_selb1(g_selb1), .osc_en(g_osc_en), .adc_en(g_adc_en), .osc_in(osc_in), .por_n_in(por_n_in));
  always @(negedge clk) #2 if (rst_n && {uo_out, uio_out, uio_oe, a_sel0, a_sel1, a_selb0, a_selb1, osc_en, adc_en} !==
                            {uo_gl, uio_out_gl, uio_oe_gl, g_sel0, g_sel1, g_selb0, g_selb1, g_osc_en, g_adc_en}) begin
    mism = mism + 1;
    if (mism <= 5) $display("MISMATCH t=%0t rst_n=%b uo rtl=%b gl=%b  uio_oe rtl=%b gl=%b  sel0 %b/%b selb0 %b/%b sel1 %b/%b selb1 %b/%b osc_en %b/%b adc_en %b/%b", $time, rst_n, uo_out, uo_gl, uio_oe, uio_oe_gl, a_sel0, g_sel0, a_selb0, g_selb0, a_sel1, g_sel1, a_selb1, g_selb1, osc_en, g_osc_en, adc_en, g_adc_en);
  end
endmodule
