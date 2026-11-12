// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 Jonas Boerschmann
//
// dig_top: the digital part of the mixed-signal tile. Hardened as one macro (see ../librelane/), placed in the
// upper part of the analog tile. It holds the spiking core, the serial configuration port, the control register of
// the analog blocks and the pin functions. Pin functions and the frame format are in ../../docs/PINS.md.
`default_nettype none

module dig_top #(
    parameter NN = 4, parameter NI = 2, parameter DEPTH = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       ena,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,

    // to the analog blocks (static while measuring)
    output wire [3:0] a_sel0,      // one-hot: ua[0] connected to channel 0..3 (all 0 = ua[0] open)
    output wire [3:0] a_sel1,      // one-hot: ua[1] connected to channel 0..3
    output wire [3:0] a_selb0,     // complements of a_sel0 / a_sel1 for the pfets of the transmission gates;
    output wire [3:0] a_selb1,     // after reset all select lines are 0 and all complements 1: every switch open
    output wire       osc_en,
    output wire       adc_en,      // reserved for the ADC
    // from the analog blocks
    input  wire       osc_in,      // oscillator output, digital level
    input  wire       por_n_in     // power-on reset of the analog side, observed only
);
    initial if (NN > 4) $error("dig_top: uo_out has room for 4 neurons");
    localparam NR = NN + NI;
    localparam RW = $clog2(NR), JW = (NN <= 2) ? 1 : $clog2(NN), IW = (NI <= 2) ? 1 : $clog2(NI);

    // ---- input synchronisers and edge detection ------------------------------------------------------------
    reg [2:0] cs_s, din_s, val_s, tref_s;
    always @(posedge clk) begin
        cs_s   <= {cs_s[1:0],   ui_in[0]};
        din_s  <= {din_s[1:0],  ui_in[1]};
        val_s  <= {val_s[1:0],  ui_in[2]};
        tref_s <= {tref_s[1:0], ui_in[4]};
    end
    wire cs       = cs_s[1];
    wire din      = din_s[1];
    wire in_pulse = val_s[1]  & ~val_s[2];
    wire tr_pulse = tref_s[1] & ~tref_s[2];

    // ---- serial configuration port: 24-bit frame {op[3:0], a[7:0], d[11:0]}, MSB first, shifted while cs = 1,
    // executed in the clock after cs fell. A frame with another number of bits is ignored.
    reg [23:0] sh;
    reg [4:0]  nbits;
    reg        cs_prev;
    always @(posedge clk) cs_prev <= cs;
    wire fall = cs_prev & ~cs;
    always @(posedge clk) begin
        if (!rst_n) begin sh <= 24'd0; nbits <= 5'd0; end
        else if (cs) begin
            sh <= {sh[22:0], din};
            if (nbits != 5'd31) nbits <= nbits + 1'b1;
        end else if (!fall) nbits <= 5'd0;           // nbits stays valid during the clock in which fall is high
    end
    wire exec = fall && rst_n && (nbits == 5'd24);
    wire [3:0]  op = sh[23:20];
    wire [7:0]  fa = sh[19:12];
    wire [11:0] fd = sh[11:0];

    wire w_we    = exec && (op == 4'd1);
    wire thr_we  = exec && (op == 4'd2);
    wire leak_we = exec && (op == 4'd3);
    wire ctl_we  = exec && (op == 4'd4);

    // analog control register: [2:0] ua0 channel (0 off, 1..4 = ch0..ch3), [5:3] ua1 channel, [6] osc_en, [7] adc_en, [11:9] osc divider
    reg [11:0] ctl;
    always @(posedge clk) begin
        if (!rst_n) ctl <= 12'd0;
        else if (ctl_we) ctl <= fd;
    end
    assign a_sel0 = {ctl[2:0] == 3'd4, ctl[2:0] == 3'd3, ctl[2:0] == 3'd2, ctl[2:0] == 3'd1};
    assign a_sel1 = {ctl[5:3] == 3'd4, ctl[5:3] == 3'd3, ctl[5:3] == 3'd2, ctl[5:3] == 3'd1};
    assign a_selb0 = ~a_sel0;
    assign a_selb1 = ~a_sel1;
    assign osc_en = ctl[6];
    assign adc_en = ctl[7];

    // ---- spiking core ---------------------------------------------------------------------------------------
    wire busy, spk_pulse;
    wire [NN-1:0] spk_last;
    wire [JW-1:0] spk_idx;
    wire [12*NN-1:0] state_flat;
    snn_tiny #(.NN(NN), .NI(NI), .DEPTH(DEPTH)) core (
        .clk(clk), .rst_n(rst_n),
        .w_we(w_we), .w_row(fa[RW+JW-1:JW]), .w_col(fa[JW-1:0]), .w_data(fd[3:0]),
        .thr_we(thr_we), .thr_data(fd), .leak_we(leak_we), .leak_data(fd[6:0]),
        .in_valid(in_pulse), .in_line(ui_in[3 +: IW]), .tref(tr_pulse),
        .busy(busy), .spk_last(spk_last), .spk_pulse(spk_pulse), .spk_idx(spk_idx), .state_flat(state_flat));

    // ---- oscillator divider, in the oscillator's own clock domain ---------------------------------------------
    reg [14:0] odiv;
    always @(posedge osc_in or negedge osc_en) begin
        if (!osc_en) odiv <= 15'd0;
        else odiv <= odiv + 1'b1;
    end
    wire [7:0] odiv_tap = {odiv[14], odiv[12], odiv[10], odiv[8], odiv[6], odiv[4], odiv[2], odiv[0]};
    wire osc_out_pin = odiv_tap[ctl[11:9]];

    // ---- pins -----------------------------------------------------------------------------------------------
    // uo_out: [NN-1:0] spikes at the last event, then busy, osc divided, por_n, clk/2^k heartbeat
    reg [6:0] hb;
    always @(posedge clk) hb <= rst_n ? hb + 1'b1 : 7'd0;
    wire [7:0] uo_i;
    assign uo_i[NN-1:0] = spk_last;
    generate if (NN < 4) begin : pad_lo assign uo_i[3:NN] = {(4-NN){1'b0}}; end endgenerate
    assign uo_i[4] = busy;
    assign uo_i[5] = osc_out_pin;
    assign uo_i[6] = por_n_in;
    assign uo_i[7] = hb[6];
    assign uo_out  = uo_i;
    assign uio_out = 8'd0;
    assign uio_oe  = 8'd0;

    wire _unused = &{ena, uio_in, ui_in[7:5], spk_pulse, spk_idx, state_flat, 1'b0};
endmodule
`default_nettype wire
