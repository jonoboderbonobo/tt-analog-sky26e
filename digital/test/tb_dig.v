`default_nettype none
`timescale 1ns / 1ps
module tb_dig ();
  initial begin
    $dumpfile("tb_dig.fst");
    $dumpvars(0, tb_dig);
    #1;
  end
  reg clk = 0, rst_n = 0, ena = 1;
  reg [7:0] ui_in = 0, uio_in = 0;
  wire [7:0] uo_out, uio_out, uio_oe;
  wire [3:0] a_sel0, a_sel1, a_selb0, a_selb1;
  wire osc_en, adc_en;
  reg osc_in = 0, por_n_in = 0;
  dig_top #(.NN(4), .NI(2), .DEPTH(4)) dut (
    .clk(clk), .rst_n(rst_n), .ena(ena), .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe),
    .a_sel0(a_sel0), .a_sel1(a_sel1), .a_selb0(a_selb0), .a_selb1(a_selb1), .osc_en(osc_en), .adc_en(adc_en), .osc_in(osc_in), .por_n_in(por_n_in));
endmodule
